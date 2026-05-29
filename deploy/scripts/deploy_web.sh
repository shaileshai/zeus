#!/bin/bash
# Deploy the Zeus web UI to Cloud Run

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Set GOOGLE_CLOUD_PROJECT environment variable"
    exit 1
fi

echo "=== Deploying Zeus Web UI ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Deploy from project root (Dockerfile at root)
cd "$(dirname "$0")/../../"

gcloud run deploy zeus-web \
    --source=. \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,MCP_TRANSPORT=sse" \
    --set-secrets="FIVETRAN_API_KEY=fivetran-api-key:latest,FIVETRAN_API_SECRET=fivetran-api-secret:latest" \
    --min-instances=0 \
    --max-instances=3 \
    --memory=1Gi

echo ""
echo "=== Web UI Deployed ==="
WEB_URL=$(gcloud run services describe zeus-web --region="$REGION" --format="value(status.url)")
echo "Zeus is live at: $WEB_URL"
echo ""
echo "Public hosted URL for Devpost submission: $WEB_URL"
