# Local LangChain Agent with Ollama

A containerized Python implementation of a local LangChain agent that connects to Ollama's local LLM server. This agent can perform web searches, execute Python code, and handle file operations.

Run the unified test framework for performance validation:

```bash
# Run all tests
python -m test.run_tests

# Generate a comprehensive performance report
python -m test.generate_report --output reports/performance_report.md
```

**⚠️ NVIDIA GPU REQUIRED: This application strictly requires NVIDIA GPU acceleration.**

## Features

- 🤖 Connects to local Olloma LLM server (<http://localhost:11434>)
- 🔍 Includes three built-in tools:
  - Web Search: Search the internet for information
  - Python REPL: Execute Python code safely
  - File Operations: Read from and write to files
- 🧠 Uses ReAct framework to let the LLM decide when to use tools
- 💻 Windows with WSL2 or Linux with NVIDIA GPU
- 🐳 Docker support with GPU acceleration
- 🎯 GPU-accelerated inference with NVIDIA Container Toolkit
- ⚡ Streaming response endpoints for improved UX
- 🚀 Optimized performance with extensive caching and connection pooling

## Documentation

For comprehensive documentation on performance optimizations and streaming implementation:

- [Performance Optimizations](test/docs/PERFORMANCE_OPTIMIZATIONS_COMPREHENSIVE.md)
- [Streaming Implementation](test/docs/STREAMING_IMPLEMENTATION.md)
- [Test Framework](test/README.md)

## Prerequisites

- Docker and Docker Compose
- NVIDIA Container Toolkit
- NVIDIA GPU with compatible drivers (CUDA capability 3.0+)

## Installation

1. Clone this repository:

   ```bash
   git clone <your-repository-url>
   cd <repository-directory>
   ```

2. Install NVIDIA Container Toolkit (following NVIDIA's official guidance):

   **Ubuntu/Debian:**

   ```bash
   # Configure the package repository
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
     && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
       sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
       sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

   # Install the packages
   sudo apt-get update
   sudo apt-get install -y libnvidia-container1 libnvidia-container-tools nvidia-container-toolkit

   # Configure Docker runtime
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

   **Windows with WSL2:**
   - Install Windows NVIDIA drivers (version 450.80.02 or later)
   - Enable WSL2 with a supported Linux distribution
   - Install Docker Desktop with WSL2 backend enabled
   - Follow the Ubuntu/Debian instructions above within your WSL2 environment

3. Build and run with Docker Compose:

   ```bash
   docker-compose up --build
   ```

## Docker Services

The Docker setup includes three services:

- **gpu-check**: Verifies GPU availability and compatibility
- **ollama**: Runs the Ollama server with GPU acceleration
- **agent**: Runs the LangChain agent application

Access the agent at: <http://localhost:8000>

## Environment Variables

The application uses the following environment variables with sensible defaults:

- `OLLAMA_MODEL`: The Ollama model to use (default: `llama3:8b`)
- `OLLAMA_BASE_URL`: The Ollama server URL (default: `http://localhost:11434`)
- `OLLAMA_TEMPERATURE`: Temperature setting for the model (default: `0.7`)
- `USER_AGENT`: User agent string for web searches
- `SEARCH_RESULTS_LIMIT`: Maximum number of search results to return (default: `5`)

## Usage

Run with Docker Compose:

```bash
docker-compose up
```

The agent will start and be accessible at <http://localhost:8000>. The system includes:

- Ollama server running on port 11434
- Agent application running on port 8000
- Automatic model downloading (llama3:8b, deepseek-coder:6.7b)

## GPU Support

The application uses NVIDIA Container Toolkit for GPU acceleration:

- **GPU Access**: Uses `NVIDIA_VISIBLE_DEVICES=all` to access all available GPUs
- **Driver Capabilities**: Configured with `compute,utility` capabilities for ML workloads
- **Memory Management**: 8GB memory limit configured for Ollama service
- **Compatibility**: NVIDIA GPU with CUDA capability 3.0 or higher

### GPU Environment Variables

The following NVIDIA-specific environment variables are configured automatically:

- `NVIDIA_VISIBLE_DEVICES=all`: Makes all GPUs visible to containers
- `NVIDIA_DRIVER_CAPABILITIES=compute,utility`: Enables compute and utility capabilities

## Log Export

The repository includes scripts to export all container logs for debugging and analysis purposes.

### Scripts Location

Log export scripts are located in the `scripts/` directory:

- `scripts/export-logs.ps1` - PowerShell script for exporting logs
- `scripts/export-logs.bat` - Batch file wrapper for easy execution

### Basic Usage

Simply double-click `scripts/export-logs.bat` or run from the root directory:

```cmd
scripts\export-logs.bat
```

### Advanced Usage with PowerShell

```powershell
# Export all logs with timestamps
.\scripts\export-logs.ps1

# Export last 100 lines only
.\scripts\export-logs.ps1 -TailLines 100

# Export without timestamps
.\scripts\export-logs.ps1 -IncludeTimestamps:$false

# Export to custom directory
.\scripts\export-logs.ps1 -OutputDir "my-logs"

# Combine multiple options
.\scripts\export-logs.ps1 -TailLines 500 -OutputDir "recent-logs" -IncludeTimestamps:$false
```

### Parameters

- `-OutputDir` - Directory name for logs (default: "logs")
- `-TailLines` - Number of recent lines to export (default: 0 = all logs)
- `-IncludeTimestamps` - Include Docker timestamps (default: true)
- `-TimestampFormat` - Format for export session timestamp (default: "yyyy-MM-dd_HH-mm-ss")

### Output Structure

The script creates a timestamped directory structure:

```text
logs/
└── export_2025-07-08_14-30-15/
    ├── ollama.log
    ├── searxng.log
    ├── agent.log
    ├── docker-compose-combined.log
    └── export-summary.txt
```

### What Gets Exported

1. **Individual container logs** - Separate log file for each container (ollama, searxng, agent)
2. **Combined logs** - Single file with all container logs interleaved by timestamp
3. **Export summary** - Details about the export session and file sizes

## API Endpoints

The agent provides several endpoints:

### Standard Request-Response API

- **GET** `/health`: Health check endpoint
- **POST** `/agent/invoke`: Standard agent endpoint
  - Input: `{"input": {"input": "your query"}}`
- **POST** `/chat/invoke`: Chat-style agent endpoint
  - Input: `{"input": {"messages": [{"content": "your query"}]}}`

### Streaming API (July 2025 Update)

- **POST** `/agent/stream`: Streaming standard agent endpoint
  - Input: `{"input": {"input": "your query"}}`
  - Returns: Server-sent events (SSE) with token-by-token updates
- **POST** `/chat/stream`: Streaming chat-style agent endpoint
  - Input: `{"input": {"messages": [{"content": "your query"}]}}`
  - Returns: Server-sent events (SSE) with token-by-token updates

### Demo Client

The repository includes a web-based demo client for testing streaming endpoints:

- Open `test/demo_streaming_client.html` in your browser to test and compare streaming vs non-streaming responses

### Streaming vs Non-Streaming

For better user experience and perceived performance:

- Use streaming endpoints for interactive applications
- Use standard endpoints for programmatic API calls

Run the streaming test script for a detailed comparison:

```bash
python test/test_streaming.py
```

## Performance Optimization

For details on performance optimizations:

- See `test/docs/PERFORMANCE_OPTIMIZATIONS.md` for comprehensive optimization details
- See `test/docs/PROVEN_OPTIMIZATIONS.md` for benchmarked improvements
- See `test/docs/STREAMING_IMPLEMENTATION.md` for streaming endpoint details
- See `test/docs/CHAT_PERFORMANCE_REPORT.md` for chat agent optimization report
- See `test/docs/OPTIMIZATION_SUMMARY.md` for overall optimization summary

## Troubleshooting

### GPU Issues

- Verify NVIDIA drivers: `nvidia-smi` (requires driver version 450.80.02+)
- Test container runtime: `docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi`
- Check NVIDIA Container Toolkit: `nvidia-ctk --version`
- Verify Docker GPU support: `docker info | grep -i nvidia`

### Docker Issues

- Ensure Docker daemon is running with NVIDIA runtime support
- For Windows: Verify WSL2 integration and GPU passthrough is enabled
- Check container logs: `docker-compose logs ollama` for GPU initialization errors
- Verify port availability (8000, 11434)

### Common GPU Setup Issues

- **Driver mismatch**: NVIDIA drivers must be compatible with CUDA version
- **Insufficient permissions**: Add user to docker group: `sudo usermod -aG docker $USER`
- **WSL2 GPU support**: Windows version 21H2 or later with WSL2 GPU support enabled
