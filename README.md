# E2B Aider Code Generator

A Python program that uses E2B sandbox to run Aider for code generation via a one-time prompt.

## Features

- 🚀 **Secure Execution**: Runs code generation in isolated E2B sandboxes
- 🤖 **AI-Powered**: Uses Aider with GPT models for intelligent code generation
- 📁 **File Management**: Handles multiple files and project structures
- ⏱️ **Timeout Control**: Configurable timeout for long-running operations
- 📊 **Result Tracking**: Detailed execution results and performance metrics
- 🔧 **Direct Shell Commands**: Efficient shell command execution via E2B commands API

## Installation

1. Install required packages:

```bash
pip install e2b-code-interpreter python-dotenv
```

2. Set up environment variables:

```bash
# Create .env file
echo "E2B_API_KEY=your_e2b_api_key_here" > .env
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

## Usage

### Command Line Interface

```bash
# Generate a simple hello world program
python e2b_aider_generator.py "Create a hello world program"

# Generate a Flask web application
python e2b_aider_generator.py "Create a Flask app with routes"

# Save generated files to a specific directory
python e2b_aider_generator.py "Create a data analysis script" --output ./generated

# Use a specific model
python e2b_aider_generator.py "Create a complex algorithm" --model gpt-4

# Use custom API base and model
python e2b_aider_generator.py "Create code with custom API" --model gpt-3.5-turbo --api-base https://api.example.com/v1

# Set timeout
python e2b_aider_generator.py "Create a large project" --timeout 600
```

### Python API

```python
from e2b_aider_generator import E2BAiderClient

# Initialize client with custom settings
client = E2BAiderClient(
    openai_model="gpt-3.5-turbo",
    openai_api_base="https://api.example.com/v1"
)

# Generate code
result = client.generate_code(
    prompt="Create a Python program that calculates factorial"
)

if result.success:
    print("Generated files:")
    for filename, content in result.generated_files.items():
        print(f"{filename}:")
        print(content)
else:
    print(f"Error: {result.error_message}")
```

### Environment Variable Configuration

```bash
# Set up environment variables
export E2B_API_KEY="your_e2b_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_API_BASE="https://api.example.com/v1"  # Optional
export OPENAI_MODEL="gpt-3.5-turbo"  # Optional

# Run with environment variables
python e2b_aider_generator.py "Create a program"
```

## Examples

See `example_usage.py` for comprehensive examples including:

- Simple hello world program
- Flask web application
- Data analysis script

## Environment Variables

- `E2B_API_KEY`: Your E2B API key (required)
- `OPENAI_API_KEY`: Your OpenAI API key for Aider (required)
- `OPENAI_API_BASE`: Custom OpenAI API base URL (optional)
- `OPENAI_MODEL`: Default model to use (optional, defaults to "gpt-4")
- `AIDER_TEMPLATE_ID`: E2B sandbox template ID with pre-installed aider (optional)

## API Reference

### E2BAiderClient

#### `__init__(e2b_api_key=None, openai_api_key=None, openai_api_base=None, openai_model=None, sandbox_template="base")`

Initialize the client with API keys.

**Parameters:**
- `e2b_api_key`: E2B API key (defaults to E2B_API_KEY env var)
- `openai_api_key`: OpenAI API key for Aider (defaults to OPENAI_API_KEY env var)
- `openai_api_base`: Custom OpenAI API base URL (defaults to OPENAI_API_BASE env var)
- `openai_model`: Custom model name (defaults to OPENAI_MODEL env var, then "gpt-4")
- `sandbox_template`: E2B sandbox template to use
- `aider_template_id`: E2B sandbox template ID with pre-installed aider (defaults to AIDER_TEMPLATE_ID env var)

#### `generate_code(prompt, project_dir="/tmp/project", aider_model=None, timeout=300)`

Generate code using Aider in E2B sandbox.

**Parameters:**
- `prompt`: The prompt to give to Aider
- `project_dir`: Directory to work in inside sandbox
- `aider_model`: Aider model to use (defaults to client's openai_model)
- `timeout`: Timeout in seconds

**Returns:**
`CodeGenerationResult` object containing:
- `success`: Whether generation succeeded
- `output`: Aider output text
- `generated_files`: Dictionary of filename -> content
- `error_message`: Error message if failed
- `execution_time`: Time taken in seconds

### CodeGenerationResult

Dataclass containing the results of code generation.

## Running Tests

```bash
# Run unit tests
python -m pytest test_e2b_aider_generator.py -v

# Run with coverage
python -m pytest test_e2b_aider_generator.py --cov=e2b_aider_generator --cov-report=html
```

## Error Handling

The client handles various error scenarios:

- Missing API keys
- Sandbox creation failures
- Aider installation issues
- Timeout errors
- File system errors

## License

MIT License