"""HTTP/SSE wrapper for the Fivetran MCP server.

This module wraps the stdio-based Fivetran MCP server with an HTTP+SSE transport,
enabling it to run as a Cloud Run service that ADK's McpToolset can connect to
via SseConnectionParams.

Usage:
    python http_server.py            # starts on port 8080
    PORT=9000 python http_server.py  # custom port

The stdio server (server.py) must be importable in the same directory.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn

load_dotenv()

# Import the Fivetran MCP server instance from server.py
sys.path.insert(0, str(Path(__file__).parent))
from server import server as fivetran_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8080"))


async def health(_request):
    """Health check endpoint for Cloud Run."""
    return JSONResponse({"status": "ok", "service": "fivetran-mcp"})


def create_app():
    sse_transport = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await fivetran_server.run(
                streams[0],
                streams[1],
                fivetran_server.create_initialization_options(),
            )

    return Starlette(
        routes=[
            Route("/health", health),
            Route("/sse", handle_sse),
            Mount("/messages", app=sse_transport.handle_post_message),
        ]
    )


if __name__ == "__main__":
    # Validate credentials
    if not os.getenv("FIVETRAN_API_KEY") or not os.getenv("FIVETRAN_API_SECRET"):
        logger.error(
            "FIVETRAN_API_KEY and FIVETRAN_API_SECRET must be set. "
            "Configure them in .env or Secret Manager."
        )
        sys.exit(1)

    allow_writes = os.getenv("FIVETRAN_ALLOW_WRITES", "false").lower() == "true"
    logger.info(f"Starting Fivetran MCP HTTP server on port {PORT}")
    logger.info(f"Write operations: {'ENABLED' if allow_writes else 'DISABLED'}")
    logger.info(f"SSE endpoint: http://0.0.0.0:{PORT}/sse")

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
