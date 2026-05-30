"""Callback hooks for the Zeus agent — approval gate and tool logging."""

import logging
from typing import Optional

from google.adk.tools import BaseTool
from google.adk.agents.context import Context

from . import config

logger = logging.getLogger(__name__)


def is_write_tool(tool_name: str) -> bool:
    """Return True if the tool name represents a write/mutating operation.

    Used by McpToolset(require_confirmation=...) to gate write operations.
    """
    return any(tool_name.startswith(prefix) for prefix in config.WRITE_TOOL_PREFIXES)


def _summarize_args(args: dict) -> str:
    """Short, human-readable rendering of key tool args for the approval prompt."""
    if not args:
        return ""
    parts = []
    for k, v in list(args.items())[:4]:
        sv = str(v)
        parts.append(f"{k}={sv[:40]}")
    return ", ".join(parts)


def before_tool_callback(
    tool: BaseTool, args: dict, tool_context: Context
) -> Optional[dict]:
    """Log every tool call and gate write/mutating tools behind human approval.

    For write tools we trigger ADK's native tool-confirmation flow (the same one
    McpTool uses): the first invocation requests confirmation and short-circuits,
    which surfaces as an `adk_request_confirmation` event the web layer turns into
    an approval modal. On resume the tool re-runs with `tool_confirmation` set.

    Returns None to allow the tool call to proceed; a dict to short-circuit.
    """
    tool_name = tool.name
    is_write = is_write_tool(tool_name)
    log_level = logging.WARNING if is_write else logging.DEBUG
    logger.log(log_level, "Tool call: %s | write=%s | args=%s", tool_name, is_write, args)

    if not is_write:
        return None  # reads proceed freely

    # Defensive: if this context can't request confirmation, don't block the demo.
    if not hasattr(tool_context, "request_confirmation"):
        return None

    confirmation = getattr(tool_context, "tool_confirmation", None)
    if confirmation is None:
        tool_context.request_confirmation(
            hint=f"Approve write operation: {tool_name}({_summarize_args(args)})"
        )
        return {"error": f"'{tool_name}' requires human approval before executing."}
    if not getattr(confirmation, "confirmed", False):
        return {"status": "rejected", "message": f"Operator rejected '{tool_name}'."}
    return None  # approved → proceed with the real call
