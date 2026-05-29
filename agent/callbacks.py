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


def before_tool_callback(
    tool: BaseTool, args: dict, tool_context: Context
) -> Optional[dict]:
    """Log every tool call. Write tools are already gated by McpToolset.require_confirmation.

    Returns None to allow the tool call to proceed.
    Returns a dict to short-circuit execution with that response.
    """
    tool_name = tool.name
    is_write = is_write_tool(tool_name)
    log_level = logging.WARNING if is_write else logging.DEBUG
    logger.log(log_level, "Tool call: %s | write=%s | args=%s", tool_name, is_write, args)
    return None  # Always proceed; confirmation handled by McpToolset
