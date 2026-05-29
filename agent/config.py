"""Configuration for the Zeus agent."""

import os

from dotenv import load_dotenv

load_dotenv()

# Google Cloud
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Model — ADK 2.1 default is gemini-2.5-flash; switch to gemini-2.5-pro for demo
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Fivetran MCP transport mode:
#   "stdio" — run server.py as a local subprocess (local dev, no Fivetran MCP server needed)
#   "sse"   — connect to remote MCP server via HTTP/SSE (Cloud Run production)
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
FIVETRAN_MCP_URL = os.getenv("FIVETRAN_MCP_URL", "http://localhost:8080/sse")

# Fivetran API credentials (used in stdio mode to pass to subprocess)
FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY", "")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET", "")

# BigQuery
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "zeus_data")

# Web
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

# Write operations that require human approval (intercepted by McpToolset.require_confirmation)
WRITE_TOOL_PREFIXES = (
    "create_",
    "modify_",
    "delete_",
    "sync_",
    "resync_",
    "run_",
    "update_",
)
