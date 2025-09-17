# E2B Code Tools

A collection of Python utilities for AI-powered code generation and live preview using E2B sandboxes.

## Project Structure

- **`generator.py`**: AI code generation using Aider in E2B sandboxes
- **`previewer.py`**: Live preview server for web applications in E2B sandboxes  
- **`e2b_dev_server_manager.py`**: Development server management utilities
- **`dev_server_examples.py`**: Usage examples for development server manager

## Features

### Generator (`generator.py`)
- 🚀 **Secure Execution**: Runs code generation in isolated E2B sandboxes
- 🤖 **AI-Powered**: Uses Aider with GPT models for intelligent code generation
- 📁 **File Management**: Handles multiple files and project structures
- ⏱️ **Timeout Control**: Configurable timeout for long-running operations
- 📊 **Result Tracking**: Detailed execution results and performance metrics
- 🔄 **Real-time Output**: Streaming output shows Aider's progress in real-time

### Preview (`previewer.py`)
- 🌐 **Live Preview**: Start development servers for web applications
- 🔍 **Auto-Detection**: Automatically detects project type and server configuration
- 📦 **Dependency Management**: Installs Node.js and Python dependencies automatically
- 🛠️ **Multiple Frameworks**: Supports static sites, Node.js, FastAPI, and more
- 🔗 **External Access**: Provides public URLs for accessing running applications

### Dev Server Manager (`e2b_dev_server_manager.py`)
- 🎛️ **Server Management**: Manage multiple development servers in parallel
- 🔧 **Framework Support**: Built-in support for Next.js, FastAPI, Node.js, Vite, React, Vue
- 📊 **Health Monitoring**: Check server health and get logs
- 🔄 **Background Processes**: Run servers in background with proper cleanup
- 🌐 **URL Management**: Automatic public URL generation for each server

## Installation

1. Install required packages:

```bash
pip install e2b-code-interpreter python-dotenv
```

2. (Optional) For development with Poetry:

```bash
poetry install
```

3. Set up environment variables:

```bash
# Create .env file
echo "E2B_API_KEY=your_e2b_api_key_here" > .env
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

## Usage

### Generator - Command Line Interface

```bash
# Generate a simple hello world program
python generator.py "Create a hello world program"

# Generate a Flask web application
python generator.py "Create a Flask app with routes"

# Save generated files to a specific directory
python generator.py "Create a data analysis script" --output ./generated

# Use a specific model
python generator.py "Create a complex algorithm" --model gpt-4

# Use custom API base and model
python generator.py "Create code with custom API" --model gpt-3.5-turbo --api-base https://api.example.com/v1

# Set timeout
python generator.py "Create a large project" --timeout 600
```

### Preview - Command Line Interface

```bash
# Preview a project directory with auto-detection
python previewer.py --path ./my-project --type auto

# Preview a Node.js project
python previewer.py --path ./my-react-app --type nodejs --port 3000

# Preview a FastAPI project with custom timeout
python previewer.py --path ./my-api --type fastapi --port 8080 --timeout 7200

# Preview a static website
python previewer.py --path ./my-website --type static --port 8000
```

### Generator - Python API

```python
from generator import E2BAiderClient

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

### Preview - Python API

```python
from previewer import preview_directory, start_live_preview

# Method 1: Preview a directory directly
preview_url = preview_directory(
    directory_path="./my-project",
    preview_type="auto",  # auto, static, nodejs, fastapi
    preview_port=8000,
    sandbox_timeout=3600
)

if preview_url:
    print(f"Preview running at: {preview_url}")

# Method 2: Manual control with existing sandbox
from e2b_code_interpreter import Sandbox

with Sandbox.create(timeout=3600) as sandbox:
    # Load your files into the sandbox
    files = {
        "index.html": "<html><body>Hello World</body></html>",
        "style.css": "body { font-family: Arial; }"
    }
    
    # Start preview server
    preview_url = start_live_preview(
        sandbox=sandbox,
        files=files,
        preview_type="static",
        preview_port=8000
    )
    
    if preview_url:
        print(f"Preview running at: {preview_url}")
```

### Dev Server Manager - Python API

```python
from e2b_code_interpreter import Sandbox
from e2b_dev_server_manager import E2BDevServerManager, ServerType

# Create sandbox and manager
with Sandbox.create(timeout=3600) as sandbox:
    manager = E2BDevServerManager(sandbox)
    
    # Start a FastAPI server
    result = manager.start_dev_server(
        server_type=ServerType.FASTAPI,
        working_dir="/tmp/project"
    )
    
    if result.success:
        print(f"FastAPI server running at: {result.public_url}")
        
        # Check server health
        is_healthy = manager.check_server_health(ServerType.FASTAPI, 8000)
        print(f"Server health: {is_healthy}")
        
        # Stop the server when done
        manager.stop_dev_server(ServerType.FASTAPI, 8000)
```

### Environment Variable Configuration

```bash
# Set up environment variables
export E2B_API_KEY="your_e2b_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_API_BASE="https://api.example.com/v1"  # Optional
export OPENAI_MODEL="gpt-3.5-turbo"  # Optional

# Run with environment variables
python generator.py "Create a program"
```

## Examples

See `dev_server_examples.py` for comprehensive examples including:

- Simple hello world program
- Flask web application
- Data analysis script

### Live Preview Examples

The live preview functionality supports various server types:

- **Auto Detection**: Automatically detects the server type based on generated files
- **Static HTML**: Serves static HTML, CSS, and JavaScript files
- **Next.js**: Starts Next.js development server
- **FastAPI**: Starts FastAPI development server with auto-reload
- **Node.js**: Starts Node.js applications
- **Vite**: Starts Vite development server
- **React**: Starts React development server
- **Vue**: Starts Vue development server
- **Python**: Starts Python HTTP server

```bash
# Generate code and then preview it
python generator.py "Create a React app with routing" --output ./my-app
python previewer.py --path ./my-app --type react

# Generate a FastAPI app and preview it
python generator.py "Create a REST API with FastAPI" --output ./my-api
python previewer.py --path ./my-api --type fastapi --port 9000

# Generate a static website and preview it
python generator.py "Create a portfolio website" --output ./my-website
python previewer.py --path ./my-website --type static
```

## Live Preview Server

The preview functionality provides a complete development environment:

1. **Load Files**: Copy project files into the E2B sandbox
2. **Auto-Detect**: Automatically detect the project type and server requirements
3. **Install Dependencies**: Install Node.js, Python, or other dependencies as needed
4. **Start Server**: Launch the appropriate development server in the E2B sandbox
5. **Expose Externally**: Provide a public URL for accessing the running application
6. **Keep Running**: Maintain the server until you press Ctrl+C

### Server Type Detection

The auto-detection feature analyzes generated files to determine the server type:

- **package.json** with "next" → Next.js server
- **package.json** with "react" → React server  
- **package.json** with "vue" → Vue server
- **main.py** with "fastapi" → FastAPI server
- **main.py** with "flask" → FastAPI server
- **.html** files → Static HTML server
- **.js/.ts** files → Static HTML server

### Supported Preview Types

| Type | Description | Default Port |
|------|-------------|-------------|
| `auto` | Automatically detect server type | 8000 |
| `static` | Static file server | 8000 |
| `nextjs` | Next.js development server | 3000 |
| `fastapi` | FastAPI development server | 8000 |
| `nodejs` | Node.js application server | 3000 |
| `vite` | Vite development server | 5173 |
| `react` | React development server | 3000 |
| `vue` | Vue development server | 5173 |
| `python` | Python HTTP server | 8000 |

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
# Run generator tests
python -m pytest test_e2b_aider_generator.py -v

# Run dev server manager tests
python -m pytest test_e2b_dev_server_manager.py -v

# Run with coverage
python -m pytest test_e2b_aider_generator.py --cov=generator --cov-report=html
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