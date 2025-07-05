import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain.tools.python.tool import PythonREPLTool
from langchain_community.llms import Ollama

class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Useful for searching the web for current information. "
        "Input should be a search query."
    )

    def _run(self, query: str) -> str:
        """Search the web for information."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            response = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
            if response.status_code != 200:
                return f"Error: Received status code {response.status_code}"
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for div in soup.find_all("div", class_=["BNeawe", "vvjwJb", "AP7Wnd"]):
                text = div.text.strip()
                if text:
                    results.append(text)
            return "\n".join(results[:5]) if results else "No results found."
        except Exception as e:
            return f"Error performing web search: {str(e)}"

class FileOperationTool(BaseTool):
    name = "file_operations"
    description = (
        "Useful for reading from or writing to files. "
        "Input should be a JSON string with 'operation' ('read' or 'write'), "
        "'path', and 'content' (for write operations). "
        "Example: {\"operation\": \"read\", \"path\": \"example.txt\"} or "
        "{\"operation\": \"write\", \"path\": \"example.txt\", \"content\": \"Hello world\"}"
    )

    def _run(self, query: str) -> str:
        """Read from or write to a file."""
        try:
            params = json.loads(query)
            operation = params.get("operation", "").lower()
            path = params.get("path", "")
            if not path:
                return "Error: A file path must be provided."
            path = os.path.normpath(path)

            if operation == "read":
                if not os.path.exists(path):
                    return f"Error: The file at '{path}' does not exist."
                with open(path, "r", encoding="utf-8") as f:
                    return f"File content:\n{f.read()}"
            elif operation == "write":
                content = params.get("content", "")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully wrote to '{path}'."
            else:
                return "Error: Invalid operation. Use 'read' or 'write'."
        except json.JSONDecodeError:
            return "Error: Input must be a valid JSON string with the required parameters."
        except Exception as e:
            return f"Error performing file operation: {str(e)}"

def create_local_agent(model_name: Optional[str] = None, temperature: float = 0.7) -> AgentExecutor:
    """
    Create a local agent using Ollama and specified tools.

    Args:
        model_name: The model to use with Ollama. If None,
                    reads from OLLAMA_MODEL env var (default 'llama3:8b').
        temperature: Temperature setting for the model (default: 0.7)

    Returns:
        An initialized AgentExecutor
    """
    # Determine which model to use
    selected_model = model_name or os.getenv("OLLAMA_MODEL", "llama3:8b")

    # Initialize the Ollama LLM
    llm = Ollama(
        model=selected_model,
        temperature=temperature,
        base_url="http://localhost:11434"
    )

    # Initialize tools
    tools = [
        WebSearchTool(),
        PythonREPLTool(),
        FileOperationTool()
    ]

    # Create the agent using ReAct framework
    prompt = PromptTemplate.from_template(
        """Answer the following questions as best you can. You have access to these tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: """
    )

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    return agent_executor

def main():
    """Main function to run the agent."""
    selected_model = os.getenv("OLLAMA_MODEL", "llama3:8b")
    print(f"Using Ollama model: {selected_model}")
    print("Supported models: llama3:8b, qwen3:8b, deepseek-coder:6.7b\n")

    print("Initializing local LangChain agent with Ollama...")
    agent = create_local_agent(selected_model)

    print("\nLocal Agent Ready! Type 'exit' to quit.")
    print("Example queries:")
    print("- What is the current weather in New York?")
    print("- Write a Python function to calculate the factorial of a number and save it to factorial.py")
    print("- Read the content of a file named 'example.txt'\n")

    while True:
        user_input = input("\nEnter your query: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting agent. Goodbye!")
            break
        try:
            response = agent.invoke({"input": user_input})
            print("\nAgent Response:")
            print(response["output"])
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()