"""Zeus root agent definition using Google ADK 2.1.0."""

import logging
import os
import sys
from pathlib import Path

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

from . import config
from .prompts import SYSTEM_PROMPT
from .callbacks import before_tool_callback
from .tools.bigquery_tool import query_bigquery
from .sub_agents.planner import planner_agent
from .sub_agents.provisioner import create_provisioner
from .sub_agents.healer import create_healer
from .sub_agents.analyst import create_analyst

logger = logging.getLogger(__name__)

# --- Fivetran MCP Toolset ---
# Supports two transport modes:
#   stdio: spawns mcp_server/server.py as a subprocess (local dev, no separate server)
#   sse:   connects to HTTP/SSE Cloud Run service (production)

_MCP_SERVER_PATH = str(Path(__file__).parent.parent / "mcp_server" / "server.py")

if config.MCP_TRANSPORT == "stdio":
    _connection_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,  # current interpreter (venv) — "python" may not exist
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

# Write-tool approval is enforced in before_tool_callback (which receives the
# tool name); McpToolset.require_confirmation can't do per-tool-name gating.
fivetran_mcp = McpToolset(
    connection_params=_connection_params,
)

# --- Sub-Agents (created with shared MCP toolset) ---
provisioner_agent = create_provisioner(fivetran_mcp)
healer_agent = create_healer(fivetran_mcp)
analyst_agent = create_analyst(fivetran_mcp)

# --- Root Agent ---
# ADK expects a module-level `root_agent` for `adk web` and `adk deploy`.
# Inject the deployed app's public webhook endpoint so the agent can register a
# Fivetran webhook pointing back at us. Falls back to a sensible hint locally.
_webhook_endpoint = (
    f"{config.WEBHOOK_URL.rstrip('/')}/api/webhook"
    if config.WEBHOOK_URL
    else "the /api/webhook endpoint of this application"
)
_system_prompt = SYSTEM_PROMPT.replace("WEBHOOK_ENDPOINT_URL", _webhook_endpoint)

root_agent = Agent(
    model=config.GEMINI_MODEL,
    name="zeus",
    description="AI Data Engineer that operates a Fivetran data foundation",
    instruction=_system_prompt,
    tools=[query_bigquery, fivetran_mcp],
    sub_agents=[planner_agent, provisioner_agent, healer_agent, analyst_agent],
    before_tool_callback=before_tool_callback,
)
