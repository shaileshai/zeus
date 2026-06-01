"""Drive the DEPLOYED Zeus service through a full turn, auto-approving writes.

Streams POST /api/chat (SSE) and, whenever an approval_request arrives, fires
POST /api/approve concurrently so the agent proceeds. Prints tools/approvals/answer.

Usage: python scripts/deployed_e2e.py <base_url> "<message>"
"""

import asyncio
import json
import sys

import httpx


async def run(base: str, message: str, session: str):
    approved = []
    answer_parts = []
    async with httpx.AsyncClient(timeout=300.0) as client:
        async def approve(aid):
            try:
                r = await client.post(f"{base}/api/approve",
                                      json={"approval_id": aid, "approved": True})
                print(f"    ✓ approved {aid[:8]} -> {r.json().get('status')}", flush=True)
            except Exception as e:
                print(f"    ! approve failed: {e}", flush=True)

        async with client.stream("POST", f"{base}/api/chat",
                                 json={"message": message, "session_id": session}) as resp:
            async for line in resp.aiter_lines():
                line = line.strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                t = ev.get("type")
                if t == "tool_activity":
                    print(f"  TOOL {ev.get('tool')}", flush=True)
                elif t == "agent_state":
                    print(f"=== {ev.get('agent')} ===", flush=True)
                elif t == "approval_request":
                    aid = ev.get("approval_id")
                    print(f"  APPROVAL: {ev.get('action')} (id {aid[:8]})", flush=True)
                    approved.append(aid)
                    asyncio.create_task(approve(aid))
                elif t == "token" and ev.get("content", "").strip():
                    answer_parts.append(ev["content"])
                elif t == "error":
                    print(f"  ERROR: {ev.get('content')}", flush=True)
                elif t == "done":
                    break
    print("\n--- FINAL ANSWER ---")
    print("".join(answer_parts)[-1200:])
    print(f"\n[{len(approved)} approvals auto-granted]")


if __name__ == "__main__":
    base = sys.argv[1].rstrip("/")
    msg = sys.argv[2]
    sess = sys.argv[3] if len(sys.argv) > 3 else "e2e1"
    asyncio.run(run(base, msg, sess))
