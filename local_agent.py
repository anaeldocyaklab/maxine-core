import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

# LangChain imports
from langchain.agents import AgentType, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.tools.python.tool import PythonREPLTool
from langchain_community.llms import Ollama

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Useful for searching the web for current information. Input should be a search query."
    
    def _run(self, query: str) -> str:
        """Search the web for information."""
        try:
            # Simple web search using requests and BeautifulSoup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
            
            if response.status_code != 200:
                return f"Error: Received status code {response.status_code}"
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results (simplified)
            results = []
            for div in soup.find_all('div', class_=['BNeawe', 'vvjwJb', 'AP7Wnd']):
                if div.text.strip():
                    results.append(div.text.strip())
            
            # Limit the results to avoid overwhelming the model
            results = results[:5]
            return "\n".join(results) if results else "No results found."
        
        except Exception as e:
            return f"Error performing web search: {str(e)}"

class FileOperationTool(BaseTool):
    name = "file_operations"
    description = """Useful for reading from or writing to files. 
    Input should be a JSON string with 'operation' ('read' or 'write'), 'path', and 'content' (for write operations).
    Example: {"operation": "read", "path": "example.txt"} or {"operation": "write", "path": "example.txt", "content": "Hello world"}"""
    
    def _run(self, query: str) -> str:
        """Read from or write to a file."""
        try:
            # Parse the input JSON
            params = json.loads(query)
            operation = params.get('operation', '').lower()
            path = params.get('path', '')
            
            # Validate the path
            if not path:
                return "Error: A file path must be provided."
            
            # Normalize path for Windows
            path = os.path.normpath(path)
            
            # Handle read operation
            if operation == 'read':
                if not os.path.exists(path):
                    return f"Error: The file at '{path}' does not exist."
                
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                return f"File content:\n{content}"
            
            # Handle write operation
            elif operation == 'write':
                content = params.get('content', '')
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                return f"Successfully wrote to '{path}'."
            
            else:
                return "Error: Invalid operation. Use 'read' or 'write'."
        
        except json.JSONDecodeError:
            return "Error: Input must be a valid JSON string with the required parameters."
        except Exception as e:
            return f"Error performing file operation: {str(e)}"

def create_local_agent(model_name: str = "deepseek-coder:7b-instruct-v2", temperature: float = 0.7):
    """
    Create a local agent using Ollama and specified tools.
    
    Args:
        model_name: The model to use with Ollama (default: deepseek-coder:7b-instruct-v2)
        temperature: Temperature setting for the model (default: 0.7)
    
    Returns:
        An initialized AgentExecutor
    """
    # Initialize the Ollama LLM
    llm = Ollama(
        model=model_name,
        temperature=temperature,
        base_url="http://localhost:11434"  # Ollama's default endpoint
    )
    
    # Initialize tools
    tools = [
        WebSearchTool(),
        PythonREPLTool(),
        FileOperationTool()
    ]
    
    # Create the agent using ReAct framework
    # This allows the model to decide when to use tools based on reasoning
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
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # Set to True to see the agent's thought process
        handle_parsing_errors=True
    )
    
    return agent_executor

def main():
    """Main function to run the agent."""
    # Create the agent
    print("Initializing local LangChain agent with Ollama...")
    agent = create_local_agent()
    
    # Interactive loop
    print("\nLocal Agent Ready! Type 'exit' to quit.")
    print("Example queries:")
    print("- What is the current weather in New York?")
    print("- Write a Python function to calculate the factorial of a number and save it to factorial.py")
    print("- Read the content of a file named 'example.txt'\n")
    
    while True:
        user_input = input("\nEnter your query: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting agent. Goodbye!")
            break
        
        try:
            response = agent.invoke({"input": user_input})
            print("\nAgent Response:")
            print(response['output'])
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()