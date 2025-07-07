#!/usr/bin/env python3
"""
Local coding agent using Ollama and LangChain with performance optimizations.
"""
import os
from typing import Optional, Dict, Any, Union
from functools import lru_cache
import threading
import weakref
import time

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_experimental.tools import PythonREPLTool
from langchain_ollama.llms import OllamaLLM
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from typing import List, Dict, Any


from .tools import WebSearchTool, DiskOperationsTool

# Constants
DEFAULT_MODEL = "llama3:8b"

# Global cache for agents and tools
_agent_cache = {}
_cache_lock = threading.Lock()

# Message content cache for performance
_message_content_cache = weakref.WeakKeyDictionary()
_content_cache_lock = threading.Lock()

# Fast message key lookup cache
_known_message_keys = {"messages", "input", "content"}  # Pre-populate common keys


@lru_cache(maxsize=4)
def get_cached_tools():
    """Get or create a cached set of tools for reuse."""
    return [WebSearchTool(), PythonREPLTool(), DiskOperationsTool()]


@lru_cache(maxsize=4)
def get_cached_llm(model_name: str, temperature: float, base_url: str) -> OllamaLLM:
    """Get or create a cached LLM instance with optimized HTTP client."""
    # Note: OllamaLLM will internally use httpx for better performance
    # Connection pooling is handled by the underlying httpx client
    return OllamaLLM(
        model=model_name,
        temperature=temperature,
        base_url=base_url,
        # Additional optimizations
        num_ctx=4096,  # Context window optimization
        # These settings optimize for production use
    )


def create_local_agent(
    model_name: Optional[str] = None, temperature: float = 0.7
) -> AgentExecutor:
    """
    Create a local agent using Ollama and specified tools with caching for performance.

    Args:
        model_name: The model to use with Ollama. If None,
                    reads from OLLAMA_MODEL env var (default 'llama3:8b').
        temperature: Temperature setting for the model (default: 0.7)

    Returns:
        An initialized AgentExecutor
    """
    # Determine which model to use
    selected_model = model_name or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

    # Create cache key for this configuration
    cache_key = f"{selected_model}_{temperature}_{base_url}"

    with _cache_lock:
        if cache_key in _agent_cache:
            return _agent_cache[cache_key]

        # Get cached LLM and tools
        llm = get_cached_llm(selected_model, temperature, base_url)
        tools = get_cached_tools()

        # Create optimized prompt template
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
Thought: {agent_scratchpad}"""
        )

        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,  # Reduced verbosity for performance
            handle_parsing_errors=True,
            return_intermediate_steps=False,
            max_iterations=6,  # Further reduced from 8 for faster responses
            early_stopping_method="generate",
            max_execution_time=45,  # Reduced from 60 for faster timeout
        )

        # Cache the agent executor
        _agent_cache[cache_key] = agent_executor
        return agent_executor


def get_raw_agent_executor():
    """Get the raw agent executor (not wrapped for chat playground)."""
    selected_model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
    return create_local_agent(selected_model)


# Pydantic models for input/output schema
class AgentInput(BaseModel):
    """Input schema for the standard agent."""

    input: str = Field(description="The question or instruction for the agent")


class AgentOutput(BaseModel):
    """Output schema for the standard agent."""

    output: str = Field(description="The agent's response")


# Global singletons for performance
_chat_agent_executor = None
_standard_agent_executor = None
_singleton_lock = threading.Lock()


def get_chat_agent_executor():
    """Get a singleton chat agent executor for better performance."""
    global _chat_agent_executor

    with _singleton_lock:
        if _chat_agent_executor is None:
            selected_model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
            base_executor = create_local_agent(selected_model)

            # Optimized wrapper with faster message processing
            class OptimizedChatAgentWrapper(
                Runnable[Dict[str, List[BaseMessage]], str]
            ):
                """Optimized chat wrapper with minimal overhead."""

                def __init__(self, executor: AgentExecutor):
                    self.executor = executor
                    # Pre-compile common message keys for faster lookup
                    self._message_keys = ["messages", "input", "data"]
                    # Cache for recently processed messages
                    self._content_cache = {}
                    self._cache_max_size = 50

                def invoke(
                    self, input: Dict[str, List[BaseMessage]], config=None, **kwargs
                ) -> str:
                    """Execute the agent with optimized message extraction."""
                    user_input = self._extract_content_fast(input)

                    # Direct execution with minimal overhead
                    result = self.executor.invoke(
                        {"input": user_input}, config, **kwargs
                    )
                    return result.get("output", str(result))

                async def ainvoke(
                    self, input: Dict[str, List[BaseMessage]], config=None, **kwargs
                ) -> str:
                    """Async execution with optimized processing."""
                    user_input = self._extract_content_fast(input)

                    result = await self.executor.ainvoke(
                        {"input": user_input}, config, **kwargs
                    )
                    return result.get("output", str(result))

                def _extract_content_fast(
                    self, input: Dict[str, List[BaseMessage]]
                ) -> str:
                    """Highly optimized message content extraction with fast paths."""
                    if not input:
                        return "Hello"

                    # Ultra-fast path: check for 'messages' key first (most common)
                    messages = input.get("messages")
                    if messages is None:
                        # Try other common keys
                        messages = input.get("input") or input.get("data")
                        if messages is None:
                            # Fallback: get first available value
                            messages = next(iter(input.values())) if input else []

                    if not messages:
                        return "Hello"

                    # Get last message efficiently
                    last_message = messages[-1]

                    # Check cache first (using object id as key for speed)
                    msg_id = id(last_message)
                    cached_content = self._content_cache.get(msg_id)
                    if cached_content is not None:
                        return cached_content

                    # Extract content with optimized attribute access
                    content = getattr(last_message, "content", None)
                    if content is None:
                        content = getattr(last_message, "text", str(last_message))
                    elif not isinstance(content, str):
                        content = str(content)

                    # Cache management with size limit
                    if len(self._content_cache) >= self._cache_max_size:
                        # Remove oldest entry (simple FIFO)
                        oldest_key = next(iter(self._content_cache))
                        del self._content_cache[oldest_key]

                    self._content_cache[msg_id] = content
                    return content

            _chat_agent_executor = OptimizedChatAgentWrapper(base_executor)

        return _chat_agent_executor


def get_standard_agent_executor():
    """Get a singleton standard agent executor for better performance."""
    global _standard_agent_executor

    with _singleton_lock:
        if _standard_agent_executor is None:
            selected_model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
            base_executor = create_local_agent(selected_model)

            # Optimized wrapper with minimal overhead
            class OptimizedStandardAgentWrapper(Runnable[AgentInput, AgentOutput]):
                """Optimized standard wrapper with minimal overhead."""

                def __init__(self, executor: AgentExecutor):
                    self.executor = executor

                @property
                def InputType(self) -> type[AgentInput]:
                    return AgentInput

                @property
                def OutputType(self) -> type[AgentOutput]:
                    return AgentOutput

                def invoke(
                    self, input: AgentInput, config=None, **kwargs
                ) -> AgentOutput:
                    """Execute the agent with minimal overhead."""
                    # Direct execution - input is already a simple string field
                    result = self.executor.invoke(
                        {"input": input.input}, config, **kwargs
                    )
                    return AgentOutput(output=result.get("output", str(result)))

                async def ainvoke(
                    self, input: AgentInput, config=None, **kwargs
                ) -> AgentOutput:
                    """Async execution with minimal overhead."""
                    result = await self.executor.ainvoke(
                        {"input": input.input}, config, **kwargs
                    )
                    return AgentOutput(output=result.get("output", str(result)))

            _standard_agent_executor = OptimizedStandardAgentWrapper(base_executor)

        return _standard_agent_executor


# Model warm-up functionality
_is_warmed_up = False
_warmup_lock = threading.Lock()


def warm_up_model():
    """Warm up the model by running a simple query."""
    global _is_warmed_up

    if _is_warmed_up:
        return

    with _warmup_lock:
        if _is_warmed_up:
            return

        try:
            # Get the standard agent and run a simple query
            agent = get_standard_agent_executor()
            warmup_input = AgentInput(input="Hello")

            # Run a simple query to warm up the model
            agent.invoke(warmup_input)
            _is_warmed_up = True
            print("✅ Model warmed up successfully")

        except Exception as e:
            print(f"⚠️ Model warm-up failed: {e}")
            # Continue anyway - warm-up is optional
