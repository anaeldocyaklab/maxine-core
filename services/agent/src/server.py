#!/usr/bin/env python3
"""
LangServe FastAPI server for the local coding agent.
"""
import os
import uvicorn
import orjson

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from langserve import add_routes

from .agent import (
    get_chat_agent_executor,
    get_standard_agent_executor,
    DEFAULT_MODEL,
    warm_up_model,
)
from .streaming import create_streaming_endpoint
from .routes import root, health_check


def create_base_routes() -> APIRouter:
    """Create the base API routes."""
    router = APIRouter(tags=["general"])

    # Register route handlers from routes module
    router.get("/")(root)
    router.get("/health")(health_check)

    return router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application with performance optimizations."""
    app = FastAPI(
        title="Local Coding Agent API",
        version="0.1.0",
        description="A local coding agent with web search and disk operations capabilities",
        # Performance optimizations
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,  # Use faster JSON serialization
    )

    # Add CORS middleware with optimized settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

    # Add LangServe routes for chat playground with optimizations
    add_routes(
        app,
        get_chat_agent_executor(),
        path="/chat",
        playground_type="chat",
        enable_feedback_endpoint=False,  # Disable for performance
        enable_public_trace_link_endpoint=False,  # Disable for performance
        include_callback_events=False,  # Disable for performance
    )

    # Add LangServe routes for standard API with optimizations
    add_routes(
        app,
        get_standard_agent_executor(),
        path="/agent",
        playground_type="default",
        enable_feedback_endpoint=False,  # Disable for performance
        enable_public_trace_link_endpoint=False,  # Disable for performance
        include_callback_events=False,  # Disable for performance
    )

    # Add streaming endpoints for improved perceived performance
    create_streaming_endpoint(app, get_chat_agent_executor)
    create_streaming_endpoint(app, get_standard_agent_executor)

    # Include base routes
    app.include_router(create_base_routes())

    return app


def main():
    """Main entry point for the server."""
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting Local Coding Agent API server on {host}:{port}")
    print(f"Using Ollama model: {os.getenv('OLLAMA_MODEL', DEFAULT_MODEL)}")
    print(f"API docs will be available at: http://{host}:{port}/docs")
    print(f"Chat playground will be available at: http://{host}:{port}/chat/playground")
    print(
        f"Standard agent playground will be available at: http://{host}:{port}/agent/playground"
    )
    print("Streaming endpoints:")
    print(f"  - Chat streaming: http://{host}:{port}/chat/stream")
    print(f"  - Standard streaming: http://{host}:{port}/agent/stream")

    # Warm up the model on startup
    print("🔥 Warming up model...")
    warm_up_model()

    app = create_app()

    # Performance optimizations for uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduced from "info" for performance
        access_log=False,  # Disable access logging for performance
        workers=1,  # Single worker for simplicity (can be increased for production)
        loop="asyncio",  # Use asyncio event loop
        http="httptools",  # Use httptools for better performance
        ws="websockets",  # Use websockets for WebSocket support
    )


if __name__ == "__main__":
    main()
