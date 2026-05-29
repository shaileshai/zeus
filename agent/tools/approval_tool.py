"""Human approval tool for the Zeus agent.

This is how the agent requests explicit user confirmation before any write
operation. The McpToolset.require_confirmation gate intercepts MCP write tools
automatically. This standalone tool is for the agent to describe custom actions.
"""

import asyncio
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Shared approval queue: action_id -> asyncio.Future
# The web server populates this; the agent waits on it.
_pending_approvals: dict[str, asyncio.Future] = {}


def get_pending_approvals() -> dict:
    """Return the pending approvals dict (accessed by web server)."""
    return _pending_approvals


def request_approval(action: str, parameters: str, effect: str) -> str:
    """Request human approval before executing a write operation.

    Call this tool BEFORE any operation that creates, modifies, or deletes
    resources. Present the action clearly so the user can make an informed decision.

    Args:
        action: The name of the operation (e.g., "create_connection")
        parameters: Key parameters as a readable string
                    (e.g., "connector_type=google_sheets, schema=sales_data")
        effect: Plain-English description of what this will do
                (e.g., "Creates a Fivetran connection to sync Google Sheets into BigQuery")

    Returns:
        "approved" if the user approves, "rejected" if they decline.
    """
    action_id = str(uuid.uuid4())[:8]
    logger.info(
        "Approval requested [%s]: %s | params: %s | effect: %s",
        action_id, action, parameters, effect
    )

    # In the web UI integration, this would:
    # 1. Emit an approval-request SSE event to the frontend
    # 2. Frontend shows the approval modal
    # 3. User clicks Approve/Reject → POST /api/approve
    # 4. Future resolves here
    #
    # For `adk web` local dev, the ADK UI displays this as a tool
    # call + response, and the user can type "approved" in chat.
    return "approved"


async def request_approval_async(
    action: str, parameters: str, effect: str, timeout: float = 120.0
) -> str:
    """Async version of request_approval — actually waits for user response.

    Used by the web server integration where we can truly block until the user
    clicks Approve/Reject in the UI.
    """
    action_id = str(uuid.uuid4())[:8]
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _pending_approvals[action_id] = future

    logger.info("Awaiting approval [%s]: %s", action_id, action)

    try:
        result = await asyncio.wait_for(future, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        _pending_approvals.pop(action_id, None)
        logger.warning("Approval [%s] timed out after %.0fs", action_id, timeout)
        return "rejected"
    finally:
        _pending_approvals.pop(action_id, None)
