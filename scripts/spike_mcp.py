#!/usr/bin/env python3
"""Day-1 Spike — Validate the Fivetran MCP connection from an ADK agent.

Run this script once the MCP server is running locally or on Cloud Run.

Usage:
    # With local MCP server:
    FIVETRAN_MCP_URL=http://localhost:8080/sse python scripts/spike_mcp.py

    # With Cloud Run MCP server:
    FIVETRAN_MCP_URL=https://fivetran-mcp-xxx.run.app/sse python scripts/spike_mcp.py

Success looks like:
    ✅ Connected to Fivetran MCP server
    ✅ Discovered N tools
    ✅ list_connections returned: [...]
    ✅ DAY-1 SPIKE COMPLETE — project is de-risked
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


async def run_spike():
    mcp_url = os.getenv("FIVETRAN_MCP_URL", "http://localhost:8080/sse")
    print(f"Connecting to MCP server at: {mcp_url}")
    print()

    try:
        from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

        mcp = McpToolset(connection_params=SseServerParams(url=mcp_url))

        print("Fetching tools...")
        tools = await mcp.get_tools()
        tool_names = [t.name for t in tools]
        print(f"✅ Connected to Fivetran MCP server")
        print(f"✅ Discovered {len(tools)} tools")
        print(f"   First 10: {tool_names[:10]}")
        print()

        # Verify key tools exist
        required_tools = [
            "list_connections",
            "get_connection_details",
            "create_connection",
            "sync_connection",
        ]
        missing = [t for t in required_tools if t not in tool_names]
        if missing:
            print(f"⚠️  Missing expected tools: {missing}")
        else:
            print(f"✅ All required Fivetran tools present")
        print()

        print("Calling list_connections...")
        # Call through the ADK agent to verify end-to-end
        from google.adk import Agent
        from google.adk.runners import InMemoryRunner
        import google.genai.types as genai_types

        agent = Agent(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            name="spike_agent",
            instruction="You are a test agent. Call the list_connections tool and report the results.",
            tools=[mcp],
        )

        runner = InMemoryRunner(agent=agent, app_name="spike")
        session = await runner.session_service.create_session(
            app_name="spike", user_id="spike_user"
        )

        events = runner.run_async(
            user_id="spike_user",
            session_id=session.id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text="List all Fivetran connections")]
            ),
        )

        print("Agent response:")
        async for event in events:
            if event.is_final_response():
                print(f"   {event.content.parts[0].text}")

        await mcp.close()

        print()
        print("✅ DAY-1 SPIKE COMPLETE — project is de-risked!")

    except Exception as e:
        print(f"❌ Spike failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_spike())
