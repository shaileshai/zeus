"""Zeus root agent definition using Google ADK 2.1.0."""

import logging

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

from . import config
from .prompts import SYSTEM_PROMPT, PLANNER_PROMPT, HEALER_PROMPT, ANALYST_PROMPT
from .callbacks import before_tool_callback, is_write_tool
from .tools.bigquery_tool import query_bigquery

logger = logging.getLogger(__name__)

# --- Fivetran MCP Toolset ---
# McpToolset connects lazily when the agent first runs.
# require_confirmation=is_write_tool gates all write operations through the
# approval flow defined in callbacks.py.
fivetran_mcp = McpToolset(
    connection_params=SseServerParams(url=config.FIVETRAN_MCP_URL),
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
