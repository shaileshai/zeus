"""Provisioner sub-agent — executes the pipeline plan via Fivetran MCP tools."""

from google.adk import Agent

from ..config import GEMINI_MODEL
from ..prompts import PROVISIONER_PROMPT

PROVISIONER_DESCRIPTION = (
    "Executes a data pipeline provisioning plan step by step using Fivetran MCP tools. "
    "Always requests human approval before any write operation."
)


def create_provisioner(fivetran_mcp) -> Agent:
    """Create the provisioner sub-agent with access to Fivetran MCP tools."""
    return Agent(
        model=GEMINI_MODEL,
        name="provisioner",
        description=PROVISIONER_DESCRIPTION,
        instruction=PROVISIONER_PROMPT,
        tools=[fivetran_mcp],
    )
