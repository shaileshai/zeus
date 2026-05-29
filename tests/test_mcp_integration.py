"""Integration tests for MCP connection (requires running MCP server)."""

import os
import pytest

# Skip these tests unless MCP server is available
pytestmark = pytest.mark.skipif(
    not os.getenv("FIVETRAN_MCP_URL"),
    reason="FIVETRAN_MCP_URL not set — MCP server not available",
)


@pytest.mark.asyncio
async def test_mcp_connection():
    """Verify we can connect to the Fivetran MCP server."""
    from google.adk.tools.mcp_tool import MCPToolset, SseServerParams

    mcp_url = os.getenv("FIVETRAN_MCP_URL")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=SseServerParams(url=mcp_url)
    )

    assert len(tools) > 0, "Should discover MCP tools"

    # Check for expected Fivetran tools
    tool_names = [t.name for t in tools]
    assert "list_connections" in tool_names, "Should have list_connections tool"

    await exit_stack.aclose()
