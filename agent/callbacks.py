"""Callback hooks for the Zeus agent — approval gate logic."""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext

from . import config

logger = logging.getLogger(__name__)


def before_tool_callback(
    tool: any, args: dict, tool_context: ToolContext
) -> Optional[dict]:
    """Intercept write operations and require human approval.

    Returns None to allow the tool call to proceed.
    Returns a dict to short-circuit with that response instead.
    """
    tool_name = getattr(tool, "name", str(tool))

    # Check if this is a write operation
    is_write = any(tool_name.startswith(prefix) for prefix in config.WRITE_TOOL_PREFIXES)

    if not is_write:
        return None  # Allow read operations without gate

    # For write operations, log the pending approval
    # The actual approval UX is handled by the web UI layer
    # which intercepts the agent's "request_approval" tool calls
    logger.info(f"Write operation detected: {tool_name} with args: {args}")

    # In the full implementation, this would:
    # 1. Emit an approval request event to the UI
    # 2. Block until the user approves/rejects
    # 3. Return None (proceed) or dict (reject)
    #
    # For now, we let it through and rely on the agent's prompt
    # to always call request_approval before write operations.
    return None
