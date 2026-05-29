"""Analyst sub-agent — queries BigQuery and answers with full data lineage."""

from google.adk import Agent

from ..config import GEMINI_MODEL
from ..prompts import ANALYST_PROMPT
from ..tools.bigquery_tool import query_bigquery, list_bigquery_tables


def create_analyst(fivetran_mcp) -> Agent:
    """Create the analyst sub-agent with BigQuery + Fivetran lineage tools."""
    return Agent(
        model=GEMINI_MODEL,
        name="analyst",
        description=(
            "Queries BigQuery and answers data questions with full lineage: "
            "source connection, table name, and last sync time on every answer."
        ),
        instruction=ANALYST_PROMPT,
        tools=[query_bigquery, list_bigquery_tables, fivetran_mcp],
    )
