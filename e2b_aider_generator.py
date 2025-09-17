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
        # Build the aider command with proper parameters
        escaped_prompt = prompt.replace("'", "'\\''")  # Escape single quotes

        # Start with base command
        aider_cmd = f"aider --model '{model}' "

        # Add API key parameter
        aider_cmd += f"--openai-api-key '{self.openai_api_key}' "

        # Add API base if provided
        if self.openai_api_base:
            aider_cmd += f"--openai-api-base '{self.openai_api_base}' "

        # Add the rest of the parameters
        aider_cmd += (
            f"--message '{escaped_prompt}' "
            f'--no-git '  # Disable git for simplicity
            f'--yes'  # Auto-confirm changes
        )

        print(f'🔍 DEBUG: Running aider command: {aider_cmd}')

        # Run aider without environment variables
        result = sandbox.commands.run(aider_cmd, cwd=project_dir, timeout=timeout)

        print(f'🔍 DEBUG: Aider exit code: {result.exit_code}')
        print(f'🔍 DEBUG: Aider stderr: {result.stderr}')

        if result.exit_code != 0:
            # Don't raise exception for authentication errors, let it continue
            print(f'⚠️  Aider execution had issues but continuing: {result.stderr}')

        # Combine stdout and stderr for the output
        output = (
            f'STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n'
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

            # Read file content
            cat_result = sandbox.commands.run(f"cat '{file_path}'")
            if cat_result.exit_code == 0:
                files_dict[rel_path] = cat_result.stdout
            else:
                files_dict[rel_path] = f'Error reading file: {cat_result.stderr}'

        return files_dict


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate code using Aider in E2B sandbox'
    )
    parser.add_argument('prompt', help='The prompt to give to Aider')
    parser.add_argument('--output', '-o', help='Output directory for generated files')
    parser.add_argument('--model', help='Aider model to use (overrides OPENAI_MODEL)')
    parser.add_argument(
        '--api-base', help='OpenAI API base URL (overrides OPENAI_API_BASE)'
    )
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')

    args = parser.parse_args()

    # Create client with custom settings
    client = E2BAiderClient(openai_model=args.model, openai_api_base=args.api_base)

    print(f'Generating code with prompt: {args.prompt}')

    # Generate code
    result = client.generate_code(prompt=args.prompt, timeout=args.timeout)

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
