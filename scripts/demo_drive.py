"""Headless driver: run root_agent end-to-end, auto-approving all writes.

Prints every tool call (+args), agent handoffs, function responses (compact),
and the final answer text. Used to validate the demo flow without the web UI.

Usage: python scripts/demo_drive.py "Analyze my sales pipeline..."
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

CONFIRM_FC = "adk_request_confirmation"


def _compact(obj, n=240):
    try:
        s = json.dumps(obj, default=str)
    except Exception:
        s = str(obj)
    return s if len(s) <= n else s[:n] + "…"


async def main(goal: str):
    from agent.agent import root_agent

    runner = Runner(
        agent=root_agent,
        app_name="zeus",
        session_service=InMemorySessionService(),
    )
    sid = "drive"
    await runner.session_service.create_session(app_name="zeus", user_id="op", session_id=sid)

    content = types.Content(role="user", parts=[types.Part(text=goal)])
    invocation_id = None
    author = None

    while True:
        interrupt = None
        async for ev in runner.run_async(
            user_id="op", session_id=sid, invocation_id=invocation_id, new_message=content
        ):
            if ev.author and ev.author != author:
                author = ev.author
                print(f"\n=== agent: {author} ===", flush=True)

            confirm = None
            for fc in ev.get_function_calls():
                if fc.name == CONFIRM_FC:
                    confirm = fc
                else:
                    print(f"  → CALL {fc.name}({_compact(fc.args)})", flush=True)

            if confirm is not None:
                orig = (confirm.args or {}).get("originalFunctionCall", {}) or {}
                print(f"  ⏸ APPROVAL requested for: {orig.get('name')} — auto-approving", flush=True)
                interrupt = (confirm.id, ev.invocation_id)
                break

            for fr in ev.get_function_responses():
                if fr.name == CONFIRM_FC:
                    continue
                print(f"  ← RESP {fr.name}: {_compact(fr.response)}", flush=True)

            if ev.content and ev.content.parts:
                for part in ev.content.parts:
                    if getattr(part, "text", None) and not ev.partial:
                        print(f"  [{author}] {part.text}", flush=True)

        if interrupt is None:
            break
        approval_id, inv = interrupt
        content = types.Content(
            role="user",
            parts=[types.Part(function_response=types.FunctionResponse(
                id=approval_id, name=CONFIRM_FC, response={"confirmed": True},
            ))],
        )
        invocation_id = inv

    print("\n=== DONE ===", flush=True)


if __name__ == "__main__":
    goal = sys.argv[1] if len(sys.argv) > 1 else "Analyze my sales pipeline against our support tickets."
    asyncio.run(main(goal))
