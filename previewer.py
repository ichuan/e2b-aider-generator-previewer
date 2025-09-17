"""
E2B Sandbox Live Preview

A utility for starting live preview servers for web projects in E2B sandboxes.
Supports various frameworks like static HTML, Node.js, and FastAPI applications.
"""

import io
import time
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()


def detect_server_type(files: Dict[str, str]) -> Optional[str]:
    """
    Auto-detect server type based on generated files.

    Args:
        files: Dictionary of generated filename -> content

    Returns:
        Detected server type ('static', 'nodejs', 'fastapi') or None if no clear match
    """
    if not files:
        return None

    filenames = list(files.keys())

    # Check for Python files with FastAPI
    python_files = [f for f in filenames if f.endswith('.py')]
    if python_files:
        for filename, content in files.items():
            if filename.endswith('.py') and content:
                if 'fastapi' in content.lower() or 'uvicorn' in content.lower():
                    return 'fastapi'

    # Check for package.json (Node.js projects)
    if 'package.json' in filenames:
        return 'nodejs'

    # Check for HTML files
    html_files = [f for f in filenames if f.endswith(('.html', '.htm'))]
    if html_files:
        return 'static'

    # Check for web-related files
    web_extensions = ['.css', '.js', '.jsx', '.ts', '.tsx']
    if any(any(f.endswith(ext) for ext in web_extensions) for f in filenames):
        return 'static'

    return None


def _install_with_pip(
    sandbox, working_dir: str, files: Dict[str, str]
) -> Optional[str]:
    """
    Install Python dependencies using pip.

    Args:
        sandbox: E2B sandbox instance
        working_dir: Working directory in sandbox
        files: Generated files dictionary

    Returns:
        Public URL for preview or None if failed
    """
    # Check for requirements.txt
    if 'requirements.txt' in files:
        print('🔍 Found requirements.txt, installing with pip...')
        install_result = sandbox.commands.run(
            f'cd {working_dir} && pip install -r requirements.txt', timeout=120
        )
        if install_result.exit_code != 0:
            print(f'❌ pip install failed: {install_result.stderr}')
            return None
        print('✅ Dependencies installed with pip successfully')
    else:
        # Install basic FastAPI dependencies if no requirements file
        print('🔍 No requirements.txt found, installing basic FastAPI dependencies...')
        basic_deps = ['fastapi', 'uvicorn[standard]']
        for dep in basic_deps:
            install_result = sandbox.commands.run(
                f'cd {working_dir} && pip install {dep}', timeout=60
            )
            if install_result.exit_code != 0:
                print(f'❌ Failed to install {dep}: {install_result.stderr}')
                return None
        print('✅ Basic dependencies installed successfully')

    return None  # Will continue with server startup


def start_live_preview(
    sandbox,
    files: Dict[str, str],
    preview_type: str,
    preview_port: int,
    working_dir: str = '/tmp/project',
) -> Optional[str]:
    """
    Start live preview server for generated code using E2B sandbox.

    Args:
        sandbox: E2B sandbox instance
        files: Generated files dictionary
        preview_type: Type of preview server ('auto', 'static', 'nodejs', 'fastapi')
        preview_port: Port number for preview server
        working_dir: Working directory in sandbox

    Returns:
        Public URL for preview or None if failed
    """
    try:
        # Auto-detect server type if requested
        if preview_type == 'auto':
            detected_type = detect_server_type(files)
            if detected_type:
                print(f'🔍 Auto-detected server type: {detected_type}')
                preview_type = detected_type
            else:
                print('🔍 Could not auto-detect server type, using static server')
                preview_type = 'static'

        # Validate preview type
        supported_types = ['static', 'nodejs', 'fastapi']
        if preview_type not in supported_types:
            print(f'❌ Unsupported preview type: {preview_type}')
            print(f'Supported types: {", ".join(supported_types)}')
            return None

        # Install dependencies if needed
        if preview_type == 'nodejs':
            print('📦 Installing Node.js dependencies...')
            install_result = sandbox.commands.run(
                f'cd {working_dir} && npm install', timeout=60
            )
            if install_result.exit_code != 0:
                print(f'⚠️  npm install failed: {install_result.stderr}')
                print('🔄 Trying with --no-optional flag...')
                install_result = sandbox.commands.run(
                    f'cd {working_dir} && npm install --no-optional', timeout=60
                )
                if install_result.exit_code != 0:
                    print(f'❌ Failed to install dependencies: {install_result.stderr}')
                    return None
            print('✅ Node.js dependencies installed successfully')

        elif preview_type == 'fastapi':
            print('📦 Installing Python dependencies...')
            # Check for poetry.lock first
            if 'poetry.lock' in files:
                print('🔍 Found poetry.lock, using poetry install...')
                install_result = sandbox.commands.run(
                    f'cd {working_dir} && poetry install', timeout=120
                )
                if install_result.exit_code != 0:
                    print(f'⚠️  poetry install failed: {install_result.stderr}')
                    print('🔄 Trying with pip install...')
                    # Fall back to pip install if poetry fails
                    pip_result = _install_with_pip(sandbox, working_dir, files)
                    if pip_result is not None:
                        return pip_result  # Failed, return error
                    # Success, continue with server startup
                print('✅ Dependencies installed with poetry successfully')
            else:
                # Use pip install
                pip_result = _install_with_pip(sandbox, working_dir, files)
                if pip_result is not None:
                    return pip_result  # Failed, return error

        # Determine the command to run based on server type
        if preview_type == 'static':
            command = f'python -m http.server {preview_port}'
        elif preview_type == 'nodejs':
            # Check if package.json has dev script
            package_json_content = files.get('package.json', '')
            if '"dev"' in package_json_content:
                command = 'npm run dev'
            else:
                command = 'npm start'
        elif preview_type == 'fastapi':
            # Find main.py or app.py
            main_file = next(
                (f for f in files.keys() if f in ['main.py', 'app.py', 'server.py']),
                'main.py',
            )
            # Check if using poetry
            if 'poetry.lock' in files:
                command = (
                    f'poetry run fastapi dev {main_file} '
                    f'--host 0.0.0.0 --port {preview_port}'
                )
            else:
                command = (
                    f'fastapi dev {main_file} --host 0.0.0.0 --port {preview_port}'
                )

        print(
            f'🚀 Starting {preview_type} live preview server on port {preview_port}...'
        )
        print(f'🔧 Command: {command}')

        # Start the server process in background using E2B's background=True
        sandbox.commands.run(f'cd {working_dir} && {command}', background=True)

        print('✅ Server started in background')

        # Get the public URL using E2B's get_host method
        try:
            host = sandbox.get_host(preview_port)
            preview_url = f'https://{host}'
            print('✅ Live preview started successfully!')
            print(f'🌐 Preview URL: {preview_url}')
            print('💡 Sandbox will remain active as long as this script runs')
            return preview_url
        except Exception as e:
            print(f'❌ Failed to get preview URL: {str(e)}')
            return None

    except Exception as e:
        print(f'❌ Error starting live preview: {str(e)}')
        return None


def load_files_from_directory(directory_path: str) -> Dict[str, str]:
    """
    Load all files from a directory into a dictionary.

    Args:
        directory_path: Path to the directory to load files from

    Returns:
        Dictionary mapping file paths to their content
    """
    files = {}
    directory = Path(directory_path)

    if not directory.exists():
        print(f'❌ Directory does not exist: {directory_path}')
        return files

    print(f'📁 Loading files from: {directory_path}')

    for file_path in directory.rglob('*'):
        if file_path.is_file():
            # Get relative path from the specified directory
            rel_path = file_path.relative_to(directory)
            try:
                content = file_path.read_text(encoding='utf-8')
                files[str(rel_path)] = content
                print(f'  ✅ Loaded: {rel_path}')
            except Exception as e:
                print(f'  ⚠️  Failed to load {rel_path}: {e}')

    print(f'📊 Loaded {len(files)} files')
    return files


def preview_directory(
    directory_path: str,
    preview_type: str = 'auto',
    preview_port: int = 8000,
    sandbox_timeout: int = 3600,
) -> Optional[str]:
    """
    Start a live preview for a directory of files.

    Args:
        directory_path: Path to the directory containing the project files
        preview_type: Type of preview server ('auto', 'static', 'nodejs', 'fastapi')
        preview_port: Port number for preview server
        sandbox_timeout: Sandbox timeout in seconds

    Returns:
        Public URL for preview or None if failed
    """
    sandbox = None
    try:
        from e2b_code_interpreter import Sandbox

        # Load files from directory
        files = load_files_from_directory(directory_path)
        if not files:
            print('❌ No files found to preview')
            return None

        # Create sandbox
        print('🏗️  Creating sandbox...')
        sandbox = Sandbox.create(timeout=sandbox_timeout)

        # Copy files to sandbox
        working_dir = '/tmp/project'
        sandbox.commands.run(f"mkdir -p '{working_dir}'")

        for filename, content in files.items():
            file_path = f'{working_dir}/{filename}'
            dir_path = '/'.join(file_path.split('/')[:-1])
            if dir_path:
                sandbox.commands.run(f"mkdir -p '{dir_path}'")
            sandbox.files.write(file_path, io.BytesIO(content.encode()))

        print('📁 Files copied to sandbox')

        # Start preview
        preview_url = start_live_preview(
            sandbox, files, preview_type, preview_port, working_dir
        )

        if preview_url:
            print(f'✅ Sandbox is running and accessible at: {preview_url}')
            print('💡 Keep this terminal open to maintain the sandbox')

            # Keep the script running to maintain the sandbox
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print('\n🛑 Stopping sandbox...')
                try:
                    sandbox.kill()
                    print('✅ Sandbox destroyed successfully')
                except Exception as e:
                    print(f'⚠️  Error destroying sandbox: {e}')
                print('✅ Preview stopped')

        return preview_url

    except Exception as e:
        print(f'❌ Error setting up preview: {str(e)}')
        if sandbox:
            try:
                sandbox.kill()
                print('✅ Sandbox cleaned up after error')
            except Exception as cleanup_error:
                print(f'⚠️  Error during cleanup: {cleanup_error}')
        return None


def main():
    """Command-line interface for preview functionality."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Start live preview server for a project directory'
    )
    parser.add_argument(
        '--path', required=True, help='Path to the project directory to preview'
    )
    parser.add_argument(
        '--type',
        choices=['auto', 'static', 'nodejs', 'fastapi'],
        default='auto',
        help='Type of preview server (default: auto)',
    )
    parser.add_argument(
        '--port', type=int, default=8000, help='Port for preview server (default: 8000)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=3600,
        help='Sandbox timeout in seconds (default: 3600)',
    )

    args = parser.parse_args()

    print('🚀 E2B Live Preview')
    print('=' * 50)

    # Start preview
    preview_url = preview_directory(args.path, args.type, args.port, args.timeout)

    if not preview_url:
        print('❌ Failed to start preview')
        exit(1)


if __name__ == '__main__':
    main()
