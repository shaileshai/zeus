"""FastAPI web server for Zeus — chat proxy to ADK agent, readiness meter, approval gate."""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

# Add project root so we can import agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import readiness as meter
from agent.config import WEB_HOST, WEB_PORT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Zeus — AI Data Engineer", version="0.1.0")

# Per-session conversation history (in-memory; replace with Firestore for production)
conversation_history: list[dict] = []

# Approval gate: pending approvals keyed by action_id
pending_approvals: dict[str, asyncio.Future] = {}


# ---  API Routes ---

@app.get("/api/status")
async def get_status():
    """Return current readiness meter state."""
    return JSONResponse(meter.get_state().to_dict())


@app.get("/api/history")
async def get_history():
    """Return conversation history."""
    return JSONResponse({"messages": conversation_history})


@app.post("/api/chat")
async def chat(request: Request):
    """Send a message to the Zeus agent and stream the response via SSE."""
    body = await request.json()
    user_message = body.get("message", "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="message required")

    conversation_history.append({"role": "user", "content": user_message})
    meter.on_mcp_call("chat")  # Count as an interaction

    async def event_stream() -> AsyncGenerator[str, None]:
        """Stream agent response chunks as SSE data events."""
        try:
            # TODO: integrate with ADK InMemoryRunner / Agent Engine API
            # For now, yield a structured placeholder response that demonstrates
            # the SSE streaming format the frontend expects.
            response_text = await _run_agent(user_message)
            conversation_history.append({"role": "assistant", "content": response_text})

            yield json.dumps({
                "type": "message",
                "role": "assistant",
                "content": response_text,
            })

            # Send updated meter state
            yield json.dumps({
                "type": "status",
                "status": meter.get_state().to_dict(),
            })

        except Exception as e:
            logger.error("Agent error: %s", e)
            yield json.dumps({
                "type": "error",
                "content": f"Agent error: {str(e)}",
            })

    return EventSourceResponse(event_stream())


@app.post("/api/approve")
async def approve_action(request: Request):
    """User approves or rejects a pending write action."""
    body = await request.json()
    action_id = body.get("action_id", "")
    approved = body.get("approved", False)

    if action_id in pending_approvals:
        future = pending_approvals.pop(action_id)
        if not future.done():
            future.set_result("approved" if approved else "rejected")

    return JSONResponse({
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
    })


@app.post("/api/webhook")
async def fivetran_webhook(request: Request):
    """Receive Fivetran webhook events for freshness monitoring."""
    body = await request.json()
    event_type = body.get("event", "unknown")
    data = body.get("data", {})
    logger.info("Fivetran webhook: %s %s", event_type, data)

    # Update readiness based on event
    if event_type == "sync_end":
        connection_id = data.get("connectionId", "unknown")
        meter.on_sync_completed(connection_id)
    elif event_type == "sync_start":
        connection_id = data.get("connectionId", "unknown")
        meter.on_sync_started(connection_id)

    return JSONResponse({"status": "received"})


@app.get("/api/reset")
async def reset():
    """Reset the readiness meter state (useful for demo resets)."""
    meter.reset_state()
    conversation_history.clear()
    return JSONResponse({"status": "reset"})


# --- Agent Integration ---

async def _run_agent(message: str) -> str:
    """Run the Zeus agent for a user message.

    Currently a placeholder that returns a demo response.
    Full integration uses ADK InMemoryRunner or Vertex AI Agent Engine API.
    """
    # Detect common intent patterns for demo purposes
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["analyze", "sales", "pipeline", "support"]):
        meter.on_mcp_call("planner")
        return (
            "I'll analyze your sales pipeline against support tickets. "
            "Let me plan the data provisioning:\n\n"
            "**Plan:**\n"
            "1. Create BigQuery destination (dataset: zeus_data)\n"
            "2. Create connection: Sales Google Sheet → BigQuery\n"
            "3. Create connection: Support Tickets Google Sheet → BigQuery\n"
            "4. Scope tables: opportunities, deals, tickets, responses\n"
            "5. Run setup tests → Sync → Query\n\n"
            "Shall I proceed? I'll request your approval before each write operation."
        )
    elif any(w in msg_lower for w in ["list", "connections", "show"]):
        meter.on_mcp_call("list_connections")
        return (
            "Calling Fivetran MCP: `list_connections`...\n\n"
            "*(Connect your Fivetran account to see live data)*"
        )
    else:
        return (
            f"I received your message: \"{message}\"\n\n"
            "I'm Zeus, your AI Data Engineer. I can:\n"
            "- **Provision** data pipelines from any source into BigQuery\n"
            "- **Monitor** data freshness and self-heal broken connections\n"
            "- **Answer** questions with full data lineage\n\n"
            "Try: *\"Analyze my sales pipeline against support tickets\"*"
        )


# Serve static frontend
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
