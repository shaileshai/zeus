#!/bin/bash
# Deploy the Fivetran MCP server to Cloud Run

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Set GOOGLE_CLOUD_PROJECT environment variable"
    exit 1
fi

echo "=== Deploying Fivetran MCP Server ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

cd "$(dirname "$0")/../../mcp_server"

gcloud run deploy fivetran-mcp \
    --source=. \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --set-secrets="FIVETRAN_API_KEY=fivetran-api-key:latest,FIVETRAN_API_SECRET=fivetran-api-secret:latest" \
    --set-env-vars="FIVETRAN_ALLOW_WRITES=true,MCP_TRANSPORT=sse" \
    --timeout=3600 \
    --min-instances=0 \
    --max-instances=2 \
    --memory=512Mi

echo ""
echo "=== MCP Server Deployed ==="
MCP_URL=$(gcloud run services describe fivetran-mcp --region="$REGION" --format="value(status.url)")
echo "MCP URL: ${MCP_URL}/sse"
echo ""
echo "Update your .env: FIVETRAN_MCP_URL=${MCP_URL}/sse"
