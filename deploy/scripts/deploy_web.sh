#!/bin/bash
# Deploy the Zeus web UI + agent to Cloud Run (single container).
#
# Default: MCP runs in-process over stdio inside this container (one service,
# fewest moving parts). To use a separate MCP Cloud Run service instead, set
# FIVETRAN_MCP_URL before running and this script switches to SSE transport.

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"          # Cloud Run / resources region
MODEL_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"     # Vertex model endpoint (Gemini 3 = global)
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3-flash-preview}"
BIGQUERY_DATASET="${BIGQUERY_DATASET:-zeus_data}"
FIVETRAN_MCP_URL="${FIVETRAN_MCP_URL:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Set GOOGLE_CLOUD_PROJECT environment variable"
    exit 1
fi

# Choose MCP transport: stdio (in-process, default) or sse (remote MCP service).
if [ -n "$FIVETRAN_MCP_URL" ]; then
    MCP_TRANSPORT="sse"
    EXTRA_ENV=",MCP_TRANSPORT=sse,FIVETRAN_MCP_URL=${FIVETRAN_MCP_URL}"
else
    MCP_TRANSPORT="stdio"
    EXTRA_ENV=",MCP_TRANSPORT=stdio"
fi

# Public URL of this service, so the agent can register a Fivetran webhook that
# points back at our own /api/webhook. After the first deploy, set WEBHOOK_URL to
# the printed Service URL and redeploy so live webhook creation targets the app.
if [ -n "${WEBHOOK_URL:-}" ]; then
    EXTRA_ENV="${EXTRA_ENV},WEBHOOK_URL=${WEBHOOK_URL}"
fi

echo "=== Deploying Zeus Web UI + Agent ==="
echo "Project: $PROJECT_ID | Region: $REGION | MCP transport: $MCP_TRANSPORT"
echo ""

# Deploy from project root (Dockerfile at root)
cd "$(dirname "$0")/../../"

gcloud run deploy zeus-web \
    --source=. \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION},GOOGLE_CLOUD_REGION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true,GEMINI_MODEL=${GEMINI_MODEL},BIGQUERY_DATASET=${BIGQUERY_DATASET}${EXTRA_ENV}" \
    --set-secrets="FIVETRAN_API_KEY=fivetran-api-key:latest,FIVETRAN_API_SECRET=fivetran-api-secret:latest" \
    --cpu=2 \
    --memory=2Gi \
    --timeout=3600 \
    --no-cpu-throttling \
    --min-instances=0 \
    --max-instances=3

echo ""
echo "=== Web UI Deployed ==="
WEB_URL=$(gcloud run services describe zeus-web --region="$REGION" --format="value(status.url)")
echo "Zeus is live at: $WEB_URL"
echo ""
echo "Public hosted URL for Devpost submission: $WEB_URL"
echo ""
echo "TIP: before recording, set --min-instances=1 to avoid cold starts."
