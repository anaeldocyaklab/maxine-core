#!/usr/bin/env python3
"""
Streaming response wrapper for improved perceived performance.
"""
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import BaseCallbackHandler


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler to stream LLM responses."""

    def __init__(self):
        self.tokens = []
        self.current_response = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token."""
        self.current_response += token
        self.tokens.append(token)

    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes."""
        pass


async def stream_agent_response(
    agent, input_data: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Stream agent responses token by token."""

    # Create streaming callback
    streaming_handler = StreamingCallbackHandler()

    # Configure agent with streaming
    config = {"callbacks": [streaming_handler]}

    try:
        # Start the agent execution in background
        task = asyncio.create_task(agent.ainvoke(input_data, config=config))

        # Stream tokens as they become available
        last_length = 0
        while not task.done():
            current_length = len(streaming_handler.current_response)
            if current_length > last_length:
                # New tokens available
                new_content = streaming_handler.current_response[last_length:]
                yield f"data: {json.dumps({'token': new_content})}\n\n"
                last_length = current_length

            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting

        # Get final result
        final_result = await task
        yield f"data: {json.dumps({'final': True, 'result': str(final_result)})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def create_streaming_endpoint(app: FastAPI, agent_getter):
    """Add streaming endpoint to FastAPI app."""

    @app.post("/chat/stream")
    async def stream_chat(input_data: Dict[str, Any]):
        """Stream chat responses for better perceived performance."""
        agent = agent_getter()

        return StreamingResponse(
            stream_agent_response(agent, input_data),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    @app.post("/agent/stream")
    async def stream_standard(input_data: Dict[str, Any]):
        """Stream standard agent responses."""
        agent = agent_getter()

        return StreamingResponse(
            stream_agent_response(agent, input_data), media_type="text/event-stream"
        )
