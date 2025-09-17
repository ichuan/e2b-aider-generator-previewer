"""
E2B Aider Code Generator

A Python program that uses E2B sandbox to run Aider for code generation
via a one-time prompt.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

# Removed E2BDevServerManager dependency - using direct commands now

load_dotenv()


@dataclass
class CodeGenerationResult:
    """Result of code generation operation."""

    success: bool
    output: str
    generated_files: Dict[str, str]
    error_message: Optional[str] = None
    execution_time: float = 0.0


class E2BAiderClient:
    """Client for running Aider in E2B sandbox."""

    def __init__(
        self,
        e2b_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_api_base: Optional[str] = None,
        openai_model: Optional[str] = None,
        sandbox_template: str = 'base',
        aider_template_id: Optional[str] = None,
    ):
        """
        Initialize the E2B Aider client.

        Args:
            e2b_api_key: E2B API key (defaults to E2B_API_KEY env var)
            openai_api_key: OpenAI API key for Aider (defaults to OPENAI_API_KEY env
                         var)
            openai_api_base: Custom OpenAI API base URL (defaults to
                          OPENAI_API_BASE env var)
            openai_model: Custom model name (defaults to OPENAI_MODEL env var,
                        then "gpt-4")
            sandbox_template: E2B sandbox template to use
            aider_template_id: E2B sandbox template ID with pre-installed aider
                            (defaults to AIDER_TEMPLATE_ID env var)
        """
        self.e2b_api_key = e2b_api_key or os.getenv('E2B_API_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.openai_api_base = openai_api_base or os.getenv('OPENAI_API_BASE')
        self.openai_model = openai_model or os.getenv('OPENAI_MODEL', 'gpt-4')
        self.sandbox_template = sandbox_template
        self.aider_template_id = aider_template_id or os.getenv('AIDER_TEMPLATE_ID')

        if not self.e2b_api_key:
            raise ValueError('E2B_API_KEY environment variable is required')
        if not self.openai_api_key:
            raise ValueError('OPENAI_API_KEY environment variable is required')

        # Import E2B SDK
        try:
            from e2b_code_interpreter import Sandbox

            # Use the new create method with template_id if available
            if self.aider_template_id:
                self.Sandbox = lambda: Sandbox.create(
                    api_key=self.e2b_api_key, template=self.aider_template_id
                )
            else:
                self.Sandbox = lambda: Sandbox.create(api_key=self.e2b_api_key)
        except ImportError:
            raise ImportError(
                'e2b-code-interpreter package not found. '
                'Install it with: pip install e2b-code-interpreter'
            )

    def generate_code(
        self,
        prompt: str,
        project_dir: str = '/tmp/project',
        aider_model: Optional[str] = None,
        timeout: int = 300,
    ) -> CodeGenerationResult:
        """
        Generate code using Aider in E2B sandbox.

        Args:
            prompt: The prompt to give to Aider
            project_dir: Directory to work in inside sandbox
            aider_model: Aider model to use (defaults to client's openai_model)
            timeout: Timeout in seconds

        Returns:
            CodeGenerationResult containing the results
        """
        # Use provided model or fall back to client's default
        model = aider_model or self.openai_model
        start_time = time.time()

        try:
            with self.Sandbox() as sandbox:
                # Create project directory
                mkdir_result = sandbox.commands.run(f"mkdir -p '{project_dir}'")
                if mkdir_result.exit_code != 0:
                    raise RuntimeError(
                        f'Failed to create project directory: {mkdir_result.stderr}'
                    )

                # Install Aider (skip if using pre-installed template)
                if not self.aider_template_id:
                    self._install_aider(sandbox)

                # Run Aider with the prompt
                result = self._run_aider_prompt(
                    sandbox, prompt, project_dir, model, timeout
                )

                # Get generated files
                generated_files = self._get_generated_files(sandbox, project_dir)

                execution_time = time.time() - start_time

                return CodeGenerationResult(
                    success=True,
                    output=result,
                    generated_files=generated_files,
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time

            # The sandbox is automatically cleaned up by the context manager
            # but we log the error for debugging
            print(f'⚠️  Error occurred during code generation: {e}')
            print('🧹 Sandbox will be automatically cleaned up by context manager')

            return CodeGenerationResult(
                success=False,
                output='',
                generated_files={},
                error_message=str(e),
                execution_time=execution_time,
            )

    def _install_aider(self, sandbox) -> None:
        """Install Aider in the sandbox."""
        install_commands = [
            'pip install aider-chat',  # Install aider-chat instead of aider
            'pip install openai',  # Ensure OpenAI package is available
        ]

        for cmd in install_commands:
            result = sandbox.commands.run(cmd)
            if result.exit_code != 0:
                raise RuntimeError(
                    f'Failed to install aider with command "{cmd}": {result.stderr}'
                )

        # Verify aider is installed
        verify_result = sandbox.commands.run('which aider')
        if verify_result.exit_code != 0:
            raise RuntimeError(
                f'Aider not found after installation: {verify_result.stderr}'
            )

    def _run_aider_prompt(
        self, sandbox, prompt: str, project_dir: str, model: str, timeout: int
    ) -> str:
        """Run Aider with the given prompt."""
        # Write prompt to a temporary file to avoid shell escaping issues
        prompt_file = f'{project_dir}/.aider_prompt.txt'
        try:
            sandbox.files.write(prompt_file, prompt.encode('utf-8'))
        except Exception as e:
            raise RuntimeError(f'Failed to write prompt file: {e}')

        # Build the aider command with proper parameters
        aider_cmd = f"aider --model '{model}' "

        # Add API key parameter
        aider_cmd += f"--openai-api-key '{self.openai_api_key}' "

        # Add API base if provided
        if self.openai_api_base:
            aider_cmd += f"--openai-api-base '{self.openai_api_base}' "

        # Use --message-file instead of --message to avoid shell escaping
        aider_cmd += (
            f"--message-file '{prompt_file}' "
            f'--no-git '  # Disable git for simplicity
            f'--yes'  # Auto-confirm changes
        )

        print('🤖 Starting Aider with streaming output...')
        print(f'🔧 Command: {aider_cmd}')
        print('-' * 50)

        # Collect output for return while streaming
        stdout_buffer = []
        stderr_buffer = []

        def on_stdout(data):
            """Handle stdout streaming data."""
            print(data, end='', flush=True)
            stdout_buffer.append(data)

        def on_stderr(data):
            """Handle stderr streaming data."""
            print(data, end='', flush=True)
            stderr_buffer.append(data)

        # Run aider with streaming output
        result = sandbox.commands.run(
            aider_cmd,
            cwd=project_dir,
            timeout=timeout,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )

        print('-' * 50)
        print(f'🔍 Aider completed with exit code: {result.exit_code}')

        if result.exit_code != 0:
            # Don't raise exception for authentication errors, let it continue
            print('⚠️  Aider execution had issues but continuing')

        # Combine stdout and stderr for the output
        stdout_content = ''.join(stdout_buffer)
        stderr_content = ''.join(stderr_buffer)
        output = (
            f'STDOUT:\n{stdout_content}\nSTDERR:\n{stderr_content}\n'
            f'Return code: {result.exit_code}'
        )
        return output

    def _get_generated_files(self, sandbox, project_dir: str) -> Dict[str, str]:
        """Get all generated files from the project directory."""
        # List all files in the project directory recursively
        find_result = sandbox.commands.run(f"find '{project_dir}' -type f")
        if find_result.exit_code != 0:
            return {'error': f'Failed to list files: {find_result.stderr}'}

        files_dict = {}

        # Parse file paths and read each file
        file_paths = find_result.stdout.strip().split('\n')
        for file_path in file_paths:
            if not file_path.strip():
                continue

            # Get relative path
            rel_path = file_path.replace(f'{project_dir}/', '')
            
            # Skip temporary files
            skip_files = ['.aider.input.history', '.aider.chat.history.md']
            if rel_path.startswith('.aider_prompt.txt') or rel_path in skip_files:
                continue

            # Read file content
            try:
                file_content = sandbox.files.read(file_path)
                files_dict[rel_path] = file_content.decode('utf-8')
            except Exception as e:
                files_dict[rel_path] = f'Error reading file: {str(e)}'

        return files_dict


def main():
    """Main function for command-line usage."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Generate code using Aider in E2B sandbox',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple prompt
  python generator.py "Create a hello world script"
  
  # Prompt from file
  python generator.py --prompt-file prompt.txt
  
  # Prompt from stdin
  echo "Create a web app" | python generator.py --stdin
  
  # Large prompt with heredoc
  python generator.py --stdin << 'EOF'
  Create a complex web application with:
  - User authentication
  - Database integration
  - REST API endpoints
  EOF
        """
    )
    
    # Add prompt source options (mutually exclusive)
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument('prompt', nargs='?', help='The prompt to give to Aider')
    prompt_group.add_argument('--prompt-file', '-f', help='Read prompt from file')
    prompt_group.add_argument(
        '--stdin', action='store_true', help='Read prompt from stdin'
    )
    
    parser.add_argument('--output', '-o', help='Output directory for generated files')
    parser.add_argument('--model', help='Aider model to use (overrides OPENAI_MODEL)')
    parser.add_argument(
        '--api-base', help='OpenAI API base URL (overrides OPENAI_API_BASE)'
    )
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')

    args = parser.parse_args()

    # Get prompt from appropriate source
    if args.stdin:
        if sys.stdin.isatty():
            parser.error("stdin requested but no input provided")
        prompt = sys.stdin.read()
    elif args.prompt_file:
        try:
            with open(args.prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except FileNotFoundError:
            print(f'❌ Error: Prompt file not found: {args.prompt_file}')
            sys.exit(1)
        except Exception as e:
            print(f'❌ Error reading prompt file: {e}')
            sys.exit(1)
    else:
        prompt = args.prompt

    # Create client with custom settings
    client = E2BAiderClient(openai_model=args.model, openai_api_base=args.api_base)

    # Show prompt preview for large prompts
    if len(prompt) > 100:
        print(f'📝 Generating code with prompt ({len(prompt)} chars):')
        print(f'   "{prompt[:100]}..."')
    else:
        print(f'📝 Generating code with prompt: {prompt}')

    # Generate code
    result = client.generate_code(prompt=prompt, timeout=args.timeout)

    # Print results
    print('\n' + '=' * 50)
    print('RESULTS')
    print('=' * 50)

    if result.success:
        print('✅ Code generation successful!')
        print(f'⏱️  Execution time: {result.execution_time:.2f} seconds')
        print(f'📁 Generated {len(result.generated_files)} files:')

        for filename, content in result.generated_files.items():
            print(f'  - {filename}')

            # Save files if output directory is specified
            if args.output:
                output_path = Path(args.output) / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
                print(f'    💾 Saved to {output_path}')

        print('\n📝 Aider output:')
        print(result.output)
    else:
        print('❌ Code generation failed!')
        print(f'⏱️  Execution time: {result.execution_time:.2f} seconds')
        print(f'🔥 Error: {result.error_message}')


if __name__ == '__main__':
    main()
