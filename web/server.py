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

# --- ADK Runner (lazy) ---
# The real agent (agent/agent.py:root_agent) drives the Fivetran MCP toolset.
# We build the Runner lazily on first chat so a missing credential surfaces as a
# clean SSE error instead of crashing server startup.
APP_NAME = "zeus"
USER_ID = "operator"
_runner = None
_adk_sessions: set[str] = set()  # web session ids that have an ADK session

# Approval round-trip: approval_id -> asyncio.Future[bool] resolved by /api/approve
_approval_futures: dict[str, asyncio.Future] = {}


def _get_runner():
    """Build (once) and return the ADK Runner wrapping the real root_agent."""
    global _runner
    if _runner is None:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from agent.agent import root_agent

        _runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=InMemorySessionService(),
        )
        logger.info("ADK Runner initialized for agent '%s'", root_agent.name)
    return _runner

# --- Session Management (in-memory; swap for Firestore in production) ---
import uuid
from datetime import datetime

MAX_CONTEXT_TOKENS = 128000  # Gemini 2.5 Flash context window

class Session:
    def __init__(self, session_id: str = None, title: str = "New Session"):
        self.id = session_id or str(uuid.uuid4())[:8]
        self.title = title
        self.messages: list[dict] = []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.token_usage = 0  # approximate

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "token_usage": self.token_usage,
            "context_remaining_pct": max(0, round(100 * (1 - self.token_usage / MAX_CONTEXT_TOKENS))),
        }

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        # Rough token estimate: ~4 chars per token
        self.token_usage += len(content) // 4
        self.updated_at = datetime.utcnow().isoformat()
        # Auto-title from first user message
        if role == "user" and self.title == "New Session":
            self.title = content[:50] + ("..." if len(content) > 50 else "")

sessions: dict[str, Session] = {}
active_session_id: str = ""

def get_or_create_session(session_id: str = None) -> Session:
    global active_session_id
    if session_id and session_id in sessions:
        active_session_id = session_id
        return sessions[session_id]
    s = Session(session_id)
    sessions[s.id] = s
    active_session_id = s.id
    return s

# Legacy compat
conversation_history: list[dict] = []


# ---  API Routes ---

@app.get("/api/status")
async def get_status():
    """Return current readiness meter state."""
    return JSONResponse(meter.get_state().to_dict())


@app.get("/api/sessions")
async def list_sessions():
    """List all sessions ordered by last updated."""
    sorted_sessions = sorted(sessions.values(), key=lambda s: s.updated_at, reverse=True)
    return JSONResponse({"sessions": [s.to_dict() for s in sorted_sessions], "active": active_session_id})


@app.post("/api/sessions")
async def create_session(request: Request):
    """Create a new session."""
    body = await request.json() if await request.body() else {}
    title = body.get("title", "New Session")
    s = Session(title=title)
    sessions[s.id] = s
    global active_session_id
    active_session_id = s.id
    return JSONResponse(s.to_dict())


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a session's messages."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    s = sessions[session_id]
    return JSONResponse({**s.to_dict(), "messages": s.messages})


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    global active_session_id
    if session_id in sessions:
        del sessions[session_id]
        if active_session_id == session_id:
            active_session_id = next(iter(sessions), "")
    return JSONResponse({"status": "deleted"})


@app.get("/api/history")
async def get_history():
    """Return active session conversation history."""
    if active_session_id and active_session_id in sessions:
        return JSONResponse({"messages": sessions[active_session_id].messages})
    return JSONResponse({"messages": []})


@app.post("/api/chat")
async def chat(request: Request):
    """Send a message to the Zeus agent and stream the response via SSE."""
    body = await request.json()
    user_message = body.get("message", "").strip()
    session_id = body.get("session_id", active_session_id)
    if not user_message:
        raise HTTPException(status_code=400, detail="message required")

    session = get_or_create_session(session_id)
    session.add_message("user", user_message)

    async def event_stream() -> AsyncGenerator[str, None]:
        """Stream real ADK agent events as SSE data events."""
        final_text: list[str] = []
        try:
            async for ev in _run_agent(user_message, session):
                # Accumulate the authoritative answer text for the final bubble.
                if ev.get("type") == "token" and ev.get("_final"):
                    final_text.append(ev["content"])
                    ev = {"type": "token", "content": ev["content"]}
                yield json.dumps(ev)

            response_text = "".join(final_text)
            if response_text:
                session.add_message("assistant", response_text)

            # Final meter + context snapshot.
            yield json.dumps({"type": "meter_update", **_meter_flat()})
            yield json.dumps({"type": "status", "status": meter.get_state().to_dict()})
            yield json.dumps({
                "type": "context_update",
                "context_remaining_pct": session.to_dict()["context_remaining_pct"],
                "token_usage": session.token_usage,
            })
            yield json.dumps({"type": "done", "content": response_text})

        except Exception as e:
            logger.exception("Agent error")
            yield json.dumps({"type": "error", "content": f"Agent error: {str(e)}"})

    return EventSourceResponse(event_stream())


@app.post("/api/approve")
async def approve_action(request: Request):
    """User approves or rejects a pending write action — unblocks the agent."""
    body = await request.json()
    # Frontend sends `approval_id`; accept `action_id` too for backward compat.
    approval_id = body.get("approval_id") or body.get("action_id", "")
    approved = bool(body.get("approved", False))

    future = _approval_futures.get(approval_id)
    if future and not future.done():
        future.set_result(approved)

    return JSONResponse({
        "approval_id": approval_id,
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


@app.get("/api/settings")
async def get_settings():
    """Return current configuration (secrets are masked)."""
    from agent import config
    return JSONResponse({
        "google_cloud_project": config.GOOGLE_CLOUD_PROJECT,
        "google_cloud_location": config.GOOGLE_CLOUD_LOCATION,
        "gemini_model": config.GEMINI_MODEL,
        "google_ai_api_key": _mask(config.GOOGLE_AI_API_KEY),
        "mcp_transport": config.MCP_TRANSPORT,
        "fivetran_mcp_url": config.FIVETRAN_MCP_URL,
        "fivetran_api_key": _mask(config.FIVETRAN_API_KEY),
        "fivetran_api_secret": _mask(config.FIVETRAN_API_SECRET),
        "bigquery_dataset": config.BIGQUERY_DATASET,
        "web_host": config.WEB_HOST,
        "web_port": config.WEB_PORT,
    })


@app.post("/api/settings")
async def update_settings(request: Request):
    """Update configuration at runtime (persists to .env file)."""
    from agent import config
    body = await request.json()

    field_map = {
        "google_cloud_project": "GOOGLE_CLOUD_PROJECT",
        "google_cloud_location": "GOOGLE_CLOUD_LOCATION",
        "gemini_model": "GEMINI_MODEL",
        "google_ai_api_key": "GOOGLE_AI_API_KEY",
        "mcp_transport": "MCP_TRANSPORT",
        "fivetran_mcp_url": "FIVETRAN_MCP_URL",
        "fivetran_api_key": "FIVETRAN_API_KEY",
        "fivetran_api_secret": "FIVETRAN_API_SECRET",
        "bigquery_dataset": "BIGQUERY_DATASET",
    }

    updated = []
    for key, env_var in field_map.items():
        if key in body and body[key] is not None:
            val = body[key]
            # Skip masked values (user didn't change secrets)
            if val.startswith("••••"):
                continue
            setattr(config, env_var, val)
            os.environ[env_var] = val
            updated.append(key)

    # Persist to .env file
    if updated:
        _persist_env(field_map, body)

    return JSONResponse({"status": "updated", "fields": updated})


def _mask(value: str) -> str:
    """Mask a secret value for display."""
    if not value:
        return ""
    if len(value) <= 4:
        return "••••"
    return "••••" + value[-4:]


def _persist_env(field_map: dict, body: dict):
    """Write updated values back to .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        env_path.touch()

    lines = env_path.read_text().splitlines()
    existing_keys = {}
    for i, line in enumerate(lines):
        if "=" in line and not line.strip().startswith("#"):
            k = line.split("=", 1)[0].strip()
            existing_keys[k] = i

    for key, env_var in field_map.items():
        if key not in body or body[key] is None:
            continue
        val = body[key]
        if val.startswith("••••"):
            continue
        new_line = f"{env_var}={val}"
        if env_var in existing_keys:
            lines[existing_keys[env_var]] = new_line
        else:
            lines.append(new_line)

    env_path.write_text("\n".join(lines) + "\n")


# --- Agent Integration (real ADK Runner driving the Fivetran MCP toolset) ---

CONFIRM_FC_NAME = "adk_request_confirmation"
SUB_AGENTS = {"planner", "provisioner", "healer", "analyst"}


def _meter_flat() -> dict:
    """Flat pillar ints matching the frontend updateMeter() signature."""
    p = meter.get_state().to_dict()["pillars"]
    return {
        "freshness": p["freshness"]["value"],
        "lineage": p["lineage"]["value"],
        "governance": p["governance"]["value"],
        "interoperability": p["interoperability"]["value"],
    }


def _extract_id(resp) -> str:
    """Best-effort pull of a Fivetran resource id from an MCP tool response."""
    if isinstance(resp, dict):
        for key in ("id", "connection_id", "connector_id", "destination_id"):
            if key in resp:
                return str(resp[key])
        if isinstance(resp.get("data"), dict):
            return _extract_id(resp["data"])
    return "unknown"


def _bump_meter_for_call(name: str):
    """Interoperability + sync-start signals fire on the tool *call*."""
    meter.on_mcp_call(name)
    if name in ("sync_connection", "resync_connection", "resync_tables"):
        meter.on_sync_started(_pending_conn or "unknown")


def _bump_meter_for_response(name: str, resp) -> bool:
    """Map a completed tool response to readiness pillars. Returns True if changed."""
    global _pending_conn
    if isinstance(resp, dict) and resp.get("error"):
        return False
    if name == "create_connection":
        cid = _extract_id(resp)
        _pending_conn = cid
        meter.on_connection_created(cid, "fivetran")
    elif name in ("sync_connection", "resync_connection", "resync_tables"):
        meter.on_sync_completed(_extract_id(resp) or _pending_conn or "unknown")
    elif name.startswith("create_account_webhook") or name.startswith("create_group_webhook"):
        meter.on_webhook_created()
    elif name in ("create_group", "modify_group", "create_destination"):
        meter.on_governance_configured(teams_count=1)
    elif name == "get_connection_details":
        meter.on_lineage_answer()
    else:
        return False
    return True


_pending_conn: str = ""


async def _ensure_adk_session(runner, session_id: str):
    """Create the ADK-side session on first use for this web session id."""
    if session_id not in _adk_sessions:
        await runner.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        _adk_sessions.add(session_id)


async def _run_agent(message: str, session: "Session"):
    """Drive the real root_agent via the ADK Runner, yielding SSE event dicts.

    Yields dicts with a `type` of: token (with optional `_final`), agent_state,
    tool_activity, meter_update, approval_request.
    """
    from contextlib import aclosing
    from google.genai import types

    try:
        runner = _get_runner()
        await _ensure_adk_session(runner, session.id)
    except Exception as e:
        logger.exception("Runner init failed")
        yield {"type": "token", "content": f"⚠️ Agent unavailable: {e}", "_final": True}
        return

    content = types.Content(role="user", parts=[types.Part(text=message)])
    invocation_id = None
    current_author = None

    while True:
        interrupt = None  # (approval_id, invocation_id) if a confirmation pauses us

        async with aclosing(
            runner.run_async(
                user_id=USER_ID,
                session_id=session.id,
                invocation_id=invocation_id,
                new_message=content,
            )
        ) as agen:
            async for event in agen:
                # Surface which (sub-)agent is active, from the event author.
                if event.author and event.author != current_author:
                    current_author = event.author
                    if event.author in SUB_AGENTS:
                        yield {"type": "agent_state", "agent": event.author, "state": "working"}

                # Look for a pending tool confirmation (the approval gate).
                confirm_fc = None
                for fc in event.get_function_calls():
                    if fc.name == CONFIRM_FC_NAME:
                        confirm_fc = fc
                    else:
                        _bump_meter_for_call(fc.name)
                        yield {"type": "tool_activity", "tool": fc.name, "params": fc.args or {}}
                        yield {"type": "meter_update", **_meter_flat()}

                if confirm_fc is not None:
                    orig = (confirm_fc.args or {}).get("originalFunctionCall", {}) or {}
                    conf = (confirm_fc.args or {}).get("toolConfirmation", {}) or {}
                    approval_id = confirm_fc.id
                    yield {
                        "type": "approval_request",
                        "approval_id": approval_id,
                        "action": orig.get("name", "write operation"),
                        "impact": conf.get("hint") or "This will modify your Fivetran data foundation.",
                        "params": orig.get("args", {}) or {},
                    }
                    interrupt = (approval_id, event.invocation_id)
                    break  # suspend this run; wait for the operator's decision

                # Tool results → readiness pillars.
                for fr in event.get_function_responses():
                    if _bump_meter_for_response(fr.name, fr.response):
                        yield {"type": "meter_update", **_meter_flat()}

                # Streaming + final answer text.
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            if event.partial:
                                yield {"type": "token", "content": part.text}
                            else:
                                yield {"type": "token", "content": part.text, "_final": True}

        if interrupt is None:
            break  # turn complete

        # --- Approval round-trip: wait for /api/approve to resolve the future ---
        approval_id, interrupt_invocation_id = interrupt
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        _approval_futures[approval_id] = future
        try:
            approved = await asyncio.wait_for(future, timeout=300.0)
        except asyncio.TimeoutError:
            approved = False
            yield {"type": "token", "content": "\n\n⏱️ Approval timed out — action rejected.", "_final": True}
        finally:
            _approval_futures.pop(approval_id, None)

        # Resume the same invocation with the operator's decision.
        content = types.Content(
            role="user",
            parts=[types.Part(function_response=types.FunctionResponse(
                id=approval_id, name=CONFIRM_FC_NAME, response={"confirmed": approved},
            ))],
        )
        invocation_id = interrupt_invocation_id


# Serve static frontend
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
