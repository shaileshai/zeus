"""Tests for Zeus tools."""

import pytest
from agent.tools.approval_tool import request_approval


def test_approval_tool_returns_approved():
    """Default approval tool returns 'approved' (placeholder)."""
    result = request_approval(
        action="create_connection",
        parameters="connector_type=google_sheets",
        effect="Creates a new Fivetran connection",
    )
    assert result == "approved"
