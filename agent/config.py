"""Configuration for the Zeus agent."""

import os

from dotenv import load_dotenv

load_dotenv()

# Google Cloud
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Model — ADK 2.1 default is gemini-2.5-flash
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Fivetran MCP
FIVETRAN_MCP_URL = os.getenv("FIVETRAN_MCP_URL", "http://localhost:8080/sse")

# BigQuery
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "zeus_data")

# Web
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

# Write operations that require human approval
WRITE_TOOL_PREFIXES = (
    "create_",
    "modify_",
    "delete_",
    "sync_",
    "resync_",
    "run_",
    "update_",
)
