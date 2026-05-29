"""Zeus root agent definition using Google ADK."""

import logging

from google.adk import Agent
from google.adk.tools.mcp_tool import MCPToolset, SseServerParams

from . import config
from .prompts import SYSTEM_PROMPT, PLANNER_PROMPT, HEALER_PROMPT, ANALYST_PROMPT
from .callbacks import before_tool_callback
from .tools.bigquery_tool import query_bigquery
from .tools.approval_tool import request_approval

logger = logging.getLogger(__name__)

# --- Sub-Agents ---

planner_agent = Agent(
    model=config.GEMINI_MODEL,
    name="planner",
    description="Decomposes user goals into data pipeline provisioning plans",
    instruction=PLANNER_PROMPT,
)

healer_agent = Agent(
    model=config.GEMINI_MODEL,
    name="healer",
    description="Monitors connection health and self-heals broken pipelines",
    instruction=HEALER_PROMPT,
)

analyst_agent = Agent(
    model=config.GEMINI_MODEL,
    name="analyst",
    description="Queries BigQuery and answers questions with full data lineage",
    instruction=ANALYST_PROMPT,
    tools=[query_bigquery],
)

# --- Root Agent ---


def create_agent() -> Agent:
    """Create the Zeus root agent with Fivetran MCP tools.

    Call this async factory to initialize the MCPToolset connection
    before starting the agent loop.
    """
    root_agent = Agent(
        model=config.GEMINI_MODEL,
        name="zeus",
        description="AI Data Engineer that operates a Fivetran data foundation",
        instruction=SYSTEM_PROMPT,
        tools=[query_bigquery, request_approval],
        sub_agents=[planner_agent, healer_agent, analyst_agent],
        before_tool_callback=before_tool_callback,
    )
    return root_agent


# ADK expects a module-level `root_agent` for `adk web` and `adk deploy`
root_agent = create_agent()
