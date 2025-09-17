"""
Unit tests for E2B Aider Code Generator.
"""

import os
import unittest
from unittest.mock import Mock, call, patch

from generator import CodeGenerationResult, E2BAiderClient


class TestE2BAiderClient(unittest.TestCase):
    """Test cases for E2BAiderClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = E2BAiderClient(
            e2b_api_key='test_e2b_key',
            openai_api_key='test_openai_key',
            openai_model='gpt-3.5-turbo',
            openai_api_base='https://api.openai.com/v1',
        )

    def test_init_success(self):
        """Test successful initialization."""
        with patch('e2b_code_interpreter.Sandbox'):
            client = E2BAiderClient(
                e2b_api_key='test_key',
                openai_api_key='test_openai_key',
                openai_model='gpt-3.5-turbo',
                openai_api_base='https://custom.api.com/v1',
            )
            self.assertEqual(client.e2b_api_key, 'test_key')
            self.assertEqual(client.openai_api_key, 'test_openai_key')
            self.assertEqual(client.openai_model, 'gpt-3.5-turbo')
            self.assertEqual(client.openai_api_base, 'https://custom.api.com/v1')

    def test_init_missing_e2b_key(self):
        """Test initialization with missing E2B API key."""
        # Temporarily remove environment variable
        original_key = os.environ.get('E2B_API_KEY')
        if 'E2B_API_KEY' in os.environ:
            del os.environ['E2B_API_KEY']

        try:
            with patch('e2b_code_interpreter.Sandbox'):
                with self.assertRaises(ValueError) as context:
                    E2BAiderClient(e2b_api_key='', openai_api_key='test')
                self.assertIn('E2B_API_KEY', str(context.exception))
        finally:
            # Restore environment variable
            if original_key:
                os.environ['E2B_API_KEY'] = original_key

    def test_init_missing_openai_key(self):
        """Test initialization with missing OpenAI API key."""
        # Temporarily remove environment variable
        original_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

        try:
            with patch('e2b_code_interpreter.Sandbox'):
                with self.assertRaises(ValueError) as context:
                    E2BAiderClient(e2b_api_key='test', openai_api_key='')
                self.assertIn('OPENAI_API_KEY', str(context.exception))
        finally:
            # Restore environment variable
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key

    def test_init_default_model(self):
        """Test initialization with default model."""
        with patch('e2b_code_interpreter.Sandbox'):
            # Clear environment variable to test default
            import os

            original_model = os.environ.get('OPENAI_MODEL')
            if 'OPENAI_MODEL' in os.environ:
                del os.environ['OPENAI_MODEL']

            try:
                client = E2BAiderClient(
                    e2b_api_key='test_key', openai_api_key='test_openai_key'
                )
                self.assertEqual(client.openai_model, 'gpt-4')  # Default value
            finally:
                # Restore environment variable
                if original_model:
                    os.environ['OPENAI_MODEL'] = original_model

    def test_init_env_vars(self):
        """Test initialization with environment variables."""
        # Set environment variables
        os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'
        os.environ['OPENAI_API_BASE'] = 'https://api.example.com/v1'

        try:
            client = E2BAiderClient(
                e2b_api_key='test_key', openai_api_key='test_openai_key'
            )
            self.assertEqual(client.openai_model, 'gpt-3.5-turbo')
            self.assertEqual(client.openai_api_base, 'https://api.example.com/v1')
        finally:
            # Clean up environment variables
            if 'OPENAI_MODEL' in os.environ:
                del os.environ['OPENAI_MODEL']
            if 'OPENAI_API_BASE' in os.environ:
                del os.environ['OPENAI_API_BASE']

    def test_init_with_aider_template_id(self):
        """Test initialization with AIDER_TEMPLATE_ID."""
        with patch('e2b_code_interpreter.Sandbox'):
            # Test with direct parameter
            client1 = E2BAiderClient(
                e2b_api_key='test_key',
                openai_api_key='test_openai_key',
                aider_template_id='template123',
            )
            self.assertEqual(client1.aider_template_id, 'template123')

            # Test with environment variable
            os.environ['AIDER_TEMPLATE_ID'] = 'template456'
            client2 = E2BAiderClient(
                e2b_api_key='test_key', openai_api_key='test_openai_key'
            )
            self.assertEqual(client2.aider_template_id, 'template456')

            # Test precedence: direct parameter over environment variable
            client3 = E2BAiderClient(
                e2b_api_key='test_key',
                openai_api_key='test_openai_key',
                aider_template_id='direct_template',
            )
            self.assertEqual(client3.aider_template_id, 'direct_template')

        # Clean up
        if 'AIDER_TEMPLATE_ID' in os.environ:
            del os.environ['AIDER_TEMPLATE_ID']

    def test_generate_code_success(self):
        """Test successful code generation."""
        # Test that the result object is created correctly
        result = CodeGenerationResult(
            success=True,
            output='Generated successfully',
            generated_files={'test.py': "print('hello')"},
            execution_time=1.0,
        )

        # Verify result structure
        self.assertIsInstance(result, CodeGenerationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.output, 'Generated successfully')
        self.assertEqual(result.generated_files, {'test.py': "print('hello')"})
        self.assertEqual(result.execution_time, 1.0)

    def test_generate_code_with_error(self):
        """Test code generation with error."""
        # Test that the result object handles errors correctly
        result = CodeGenerationResult(
            success=False,
            output='',
            generated_files={},
            error_message='Connection error',
            execution_time=1.0,
        )

        # Verify error handling
        self.assertIsInstance(result, CodeGenerationResult)
        self.assertFalse(result.success)
        self.assertEqual(result.output, '')
        self.assertEqual(result.generated_files, {})
        self.assertEqual(result.error_message, 'Connection error')
        self.assertEqual(result.execution_time, 1.0)

    def test_install_aider(self):
        """Test Aider installation in sandbox."""
        mock_sandbox = Mock()
        mock_commands = Mock()
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_commands.run.return_value = mock_result
        mock_sandbox.commands = mock_commands

        self.client._install_aider(mock_sandbox)

        # Verify installation commands were called
        expected_calls = [
            call('pip install aider-chat'),
            call('pip install openai'),
        ]
        mock_commands.run.assert_has_calls(expected_calls, any_order=True)

    def test_run_aider_prompt(self):
        """Test running Aider with prompt."""
        mock_sandbox = Mock()
        mock_commands = Mock()
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_commands.run.return_value = mock_result
        mock_sandbox.commands = mock_commands

        result = self.client._run_aider_prompt(
            mock_sandbox, 'Create hello world', '/tmp/project', 'gpt-4', 300
        )

        # The result now includes streaming callbacks, so check for the expected format
        self.assertIn('STDOUT:', result)
        self.assertIn('STDERR:', result)
        self.assertIn('Return code: 0', result)
        self.assertTrue(mock_commands.run.called)

    def test_run_aider_prompt_with_custom_api_base(self):
        """Test running Aider with custom API base."""
        mock_sandbox = Mock()
        mock_commands = Mock()
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_commands.run.return_value = mock_result
        mock_sandbox.commands = mock_commands

        # Create client with custom API base
        client = E2BAiderClient(
            e2b_api_key='test_key',
            openai_api_key='test_openai_key',
            openai_api_base='https://custom.api.com/v1',
        )

        # Verify the client has the custom API base set
        self.assertEqual(client.openai_api_base, 'https://custom.api.com/v1')

        result = client._run_aider_prompt(
            mock_sandbox, 'Create hello world', '/tmp/project', 'gpt-4', 300
        )

        # The result now includes streaming callbacks, so check for the expected format
        self.assertIn('STDOUT:', result)
        self.assertIn('STDERR:', result)
        self.assertIn('Return code: 0', result)
        self.assertTrue(mock_commands.run.called)

    def test_run_aider_prompt_error(self):
        """Test running Aider with error."""
        mock_sandbox = Mock()
        mock_commands = Mock()
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_commands.run.return_value = mock_result
        mock_sandbox.commands = mock_commands

        # Should not raise RuntimeError, just return error message
        result = self.client._run_aider_prompt(
            mock_sandbox, 'Create hello world', '/tmp/project', 'gpt-4', 300
        )

        # Verify the result contains error information in the expected format
        self.assertIn('STDOUT:', result)
        self.assertIn('STDERR:', result)
        self.assertIn('Return code: 1', result)

    def test_get_generated_files(self):
        """Test getting generated files."""
        mock_sandbox = Mock()
        mock_commands = Mock()
        mock_files = Mock()

        # Mock find command result
        find_result = Mock()
        find_result.exit_code = 0
        find_result.stdout = '/tmp/project/main.py\n/tmp/project/README.md'

        # Mock file reading - now uses sandbox.files.read()
        mock_files.read.side_effect = [
            b'print("hello")',  # main.py content
            b'# Project'       # README.md content
        ]

        mock_commands.run.return_value = find_result
        mock_sandbox.commands = mock_commands
        mock_sandbox.files = mock_files

        files = self.client._get_generated_files(mock_sandbox, '/tmp/project')

        expected = {'main.py': 'print("hello")', 'README.md': '# Project'}
        self.assertEqual(files, expected)

    def test_get_generated_files_error(self):
        """Test getting generated files with error."""
        mock_sandbox = Mock()
        mock_commands = Mock()
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_result.stderr = 'Failed to list files'
        mock_commands.run.return_value = mock_result
        mock_sandbox.commands = mock_commands

        files = self.client._get_generated_files(mock_sandbox, '/tmp/project')

        self.assertIn('error', files)
        self.assertIn('Failed to list files', files['error'])


class TestCodeGenerationResult(unittest.TestCase):
    """Test cases for CodeGenerationResult."""

    def test_success_result(self):
        """Test successful result creation."""
        result = CodeGenerationResult(
            success=True,
            output='Generated successfully',
            generated_files={'main.py': "print('hello')"},
            execution_time=5.0,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.output, 'Generated successfully')
        self.assertEqual(result.generated_files, {'main.py': "print('hello')"})
        self.assertEqual(result.execution_time, 5.0)
        self.assertIsNone(result.error_message)

    def test_error_result(self):
        """Test error result creation."""
        result = CodeGenerationResult(
            success=False,
            output='',
            generated_files={},
            error_message='Generation failed',
            execution_time=2.0,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.output, '')
        self.assertEqual(result.generated_files, {})
        self.assertEqual(result.error_message, 'Generation failed')
        self.assertEqual(result.execution_time, 2.0)


if __name__ == '__main__':
    unittest.main()
