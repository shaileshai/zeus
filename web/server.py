"""FastAPI web server for Zeus — proxies chat to ADK agent, serves UI."""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from agent import config

logger = logging.getLogger(__name__)

app = FastAPI(title="Zeus — AI Data Engineer", version="0.1.0")

# In-memory state (will be replaced with proper session management)
conversation_history: list[dict] = []
pending_approvals: dict[str, asyncio.Event] = {}
readiness_state = {
    "freshness": 0,
    "lineage": 0,
    "governance": 10,  # Base: MCP protocol is open
    "interoperability": 25,
}


@app.get("/api/status")
async def get_status():
    """Return current readiness meter values."""
    overall = sum(readiness_state.values()) / 4
    return {
        "pillars": readiness_state,
        "overall": round(overall, 1),
    }


@app.get("/api/history")
async def get_history():
    """Return conversation history."""
    return {"messages": conversation_history}


@app.post("/api/chat")
async def chat(request: Request):
    """Send a message to the Zeus agent and stream the response."""
    body = await request.json()
    user_message = body.get("message", "")

    conversation_history.append({"role": "user", "content": user_message})

    async def event_stream() -> AsyncGenerator[str, None]:
        # TODO: Connect to actual ADK agent via Agent Engine API
        # For now, echo back a placeholder
        response = {
            "role": "assistant",
            "content": f"[Zeus agent processing: '{user_message}']\n\n"
            "Agent integration pending — connect ADK agent here.",
        }
        conversation_history.append(response)
        yield json.dumps(response)

    return EventSourceResponse(event_stream())


@app.post("/api/approve")
async def approve_action(request: Request):
    """User approves or rejects a pending write action."""
    body = await request.json()
    action_id = body.get("action_id", "")
    approved = body.get("approved", False)

    if action_id in pending_approvals:
        # Signal the waiting approval gate
        pending_approvals[action_id].set()

    return {
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
    }


@app.post("/api/webhook")
async def fivetran_webhook(request: Request):
    """Receive Fivetran webhook events for freshness monitoring."""
    body = await request.json()
    event_type = body.get("event", "unknown")
    logger.info(f"Fivetran webhook received: {event_type}")

    # Update freshness based on webhook events
    if event_type in ("sync_end", "sync_start"):
        readiness_state["freshness"] = min(100, readiness_state["freshness"] + 20)

    return {"status": "received"}


# Serve static frontend files
app.mount("/", StaticFiles(directory="static", html=True), name="static")
