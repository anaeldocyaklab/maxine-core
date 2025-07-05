# Local LangChain Agent with Ollama

A simple yet powerful Python implementation of a local LangChain agent that connects to Ollama's local LLM server. This agent can perform web searches, execute Python code, and handle file operations.

## Features

- 🤖 Connects to local Ollama LLM server (http://localhost:11434)
- 🔍 Includes three built-in tools:
  - Web Search: Search the internet for information
  - Python REPL: Execute Python code safely
  - File Operations: Read from and write to files
- 🧠 Uses ReAct framework to let the LLM decide when to use tools
- 💻 Works on Windows and other platforms
- 🚀 Minimal dependencies and setup

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running locally with models like:
  - `llama3:8b`
  - `qwen3:8b`
  - `deepseek-coder:6.7b`

## Installation

1. Clone this repository:
   ```bash
   git clone <your-repository-url>
   cd <repository-directory>