"""Healer sub-agent — monitors and self-heals broken Fivetran connections."""

from google.adk import Agent

from ..config import GEMINI_MODEL
from ..prompts import HEALER_PROMPT, HEALER_EXTENDED_PROMPT


def create_healer(fivetran_mcp) -> Agent:
    """Create the healer sub-agent with access to Fivetran MCP tools."""
    return Agent(
        model=GEMINI_MODEL,
        name="healer",
        description=(
            "Monitors Fivetran connection health and automatically diagnoses and "
            "heals broken pipelines. Re-tests, resyncs, and reports."
        ),
        instruction=HEALER_EXTENDED_PROMPT,
        tools=[fivetran_mcp],
    )
