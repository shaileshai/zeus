"""Configuration for the Zeus agent."""

import os

from dotenv import load_dotenv

load_dotenv()

# Google Cloud
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
# Vertex AI *model* endpoint location. Gemini 3 models are served from the
# "global" endpoint (not a region like us-central1), so default to global.
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
# Region for Google Cloud *resources* (Cloud Run, BigQuery, Artifact Registry).
GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")

# Run the agent on Vertex AI (required by the hackathon rules — "Gemini + Agent
# Builder"), NOT the AI Studio API-key path. google-genai / ADK read these
# values from the environment, so we export them below before any client is built.
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true")

# Model — the hackathon is "built with Gemini 3". gemini-3-flash-preview for dev,
# gemini-3.1-pro-preview for the final/demo. Both require GOOGLE_CLOUD_LOCATION=global.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

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

# Google AI API Key — legacy AI Studio path. Kept only for the Settings form;
# the agent itself authenticates to Vertex AI via ADC, not this key.
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")

# Web — Cloud Run injects $PORT and the container MUST listen on it; prefer it.
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("PORT") or os.getenv("WEB_PORT") or "8000")

# Export the Vertex settings into the environment so the google-genai client
# (used by ADK under the hood) picks them up regardless of import order.
if GOOGLE_GENAI_USE_VERTEXAI.lower() == "true":
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    if GOOGLE_CLOUD_PROJECT:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT)
    # Force the model endpoint location (global for Gemini 3); BigQuery and other
    # resources are unaffected (they route by the resource's own region).
    os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_CLOUD_LOCATION

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
