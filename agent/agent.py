"""Zeus root agent definition using Google ADK 2.1.0."""

import logging
import os
from pathlib import Path

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

from . import config
from .prompts import SYSTEM_PROMPT, PLANNER_PROMPT, HEALER_PROMPT, ANALYST_PROMPT
from .callbacks import before_tool_callback, is_write_tool
from .tools.bigquery_tool import query_bigquery

logger = logging.getLogger(__name__)

# --- Fivetran MCP Toolset ---
# Supports two transport modes:
#   stdio: spawns mcp_server/server.py as a subprocess (local dev)
#   sse:   connects to HTTP/SSE Cloud Run service (production)

_MCP_SERVER_PATH = str(Path(__file__).parent.parent / "mcp_server" / "server.py")

if config.MCP_TRANSPORT == "stdio":
    _connection_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[_MCP_SERVER_PATH],
            env={
                **os.environ,
                "FIVETRAN_API_KEY": config.FIVETRAN_API_KEY,
                "FIVETRAN_API_SECRET": config.FIVETRAN_API_SECRET,
                "FIVETRAN_ALLOW_WRITES": "true",
            },
        )
    )
    logger.info("MCP transport: stdio (subprocess: %s)", _MCP_SERVER_PATH)
else:
    _connection_params = SseServerParams(url=config.FIVETRAN_MCP_URL)
    logger.info("MCP transport: SSE (%s)", config.FIVETRAN_MCP_URL)

fivetran_mcp = McpToolset(
    connection_params=_connection_params,
    require_confirmation=is_write_tool,
)

# --- Sub-Agents ---

planner_agent = Agent(
    model=config.GEMINI_MODEL,
    name="planner",
    description="Decomposes user goals into data pipeline provisioning plans",
    instruction=PLANNER_PROMPT,
    tools=[fivetran_mcp],
)

healer_agent = Agent(
    model=config.GEMINI_MODEL,
    name="healer",
    description="Monitors connection health and self-heals broken pipelines",
    instruction=HEALER_PROMPT,
    tools=[fivetran_mcp],
)

analyst_agent = Agent(
    model=config.GEMINI_MODEL,
    name="analyst",
    description="Queries BigQuery and answers questions with full data lineage",
    instruction=ANALYST_PROMPT,
    tools=[query_bigquery, fivetran_mcp],
)

# --- Root Agent ---
# ADK expects a module-level `root_agent` for `adk web` and `adk deploy`.
root_agent = Agent(
    model=config.GEMINI_MODEL,
    name="zeus",
    description="AI Data Engineer that operates a Fivetran data foundation",
    instruction=SYSTEM_PROMPT,
    tools=[query_bigquery, fivetran_mcp],
    sub_agents=[planner_agent, healer_agent, analyst_agent],
    before_tool_callback=before_tool_callback,
)
