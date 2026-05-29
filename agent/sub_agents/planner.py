"""Planner sub-agent — decomposes user goals into pipeline provisioning plans."""

from google.adk import Agent

from ..config import GEMINI_MODEL
from ..prompts import PLANNER_PROMPT

planner_agent = Agent(
    model=GEMINI_MODEL,
    name="planner",
    description=(
        "Decomposes a user's natural-language data goal into a structured "
        "pipeline provisioning plan: which sources, which tables, which destination."
    ),
    instruction=PLANNER_PROMPT,
)
