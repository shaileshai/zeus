"""Tests for the Zeus agent."""

import pytest
from agent.config import WRITE_TOOL_PREFIXES


def test_write_tool_prefixes():
    """Verify write tool prefix list covers expected operations."""
    assert "create_" in WRITE_TOOL_PREFIXES
    assert "modify_" in WRITE_TOOL_PREFIXES
    assert "delete_" in WRITE_TOOL_PREFIXES
    assert "sync_" in WRITE_TOOL_PREFIXES


def test_write_detection():
    """Verify we correctly identify write vs read tools."""
    write_tools = ["create_connection", "modify_connection_table_config", "sync_connection"]
    read_tools = ["list_connections", "get_connection_details"]

    for tool in write_tools:
        assert any(tool.startswith(p) for p in WRITE_TOOL_PREFIXES), f"{tool} should be write"

    for tool in read_tools:
        assert not any(tool.startswith(p) for p in WRITE_TOOL_PREFIXES), f"{tool} should be read"
