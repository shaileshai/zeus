#!/bin/bash
# Setup GCP project for Zeus
# Run this once to configure the project

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Set GOOGLE_CLOUD_PROJECT environment variable"
    exit 1
fi

echo "=== Zeus GCP Setup ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    run.googleapis.com \
    bigquery.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com

# Create Artifact Registry repository
echo "Creating Artifact Registry repo..."
gcloud artifacts repositories create zeus \
    --repository-format=docker \
    --location="$REGION" \
    --description="Zeus container images" \
    2>/dev/null || echo "  (already exists)"

# Create BigQuery dataset
echo "Creating BigQuery dataset..."
bq mk --dataset --location="$REGION" \
    "${PROJECT_ID}:zeus_data" \
    2>/dev/null || echo "  (already exists)"

# Create secrets (placeholders — user must fill in values)
echo "Creating Secret Manager secrets..."
echo -n "PLACEHOLDER" | gcloud secrets create fivetran-api-key \
    --data-file=- --replication-policy=automatic \
    2>/dev/null || echo "  fivetran-api-key (already exists)"

echo -n "PLACEHOLDER" | gcloud secrets create fivetran-api-secret \
    --data-file=- --replication-policy=automatic \
    2>/dev/null || echo "  fivetran-api-secret (already exists)"

# Grant the Cloud Run runtime service account (default compute SA) the roles the
# deployed agent needs: call Vertex AI, read/write BigQuery, read the secrets.
echo "Granting IAM roles to the Cloud Run runtime service account..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for ROLE in roles/aiplatform.user roles/bigquery.dataEditor roles/bigquery.jobUser; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${RUNTIME_SA}" --role="$ROLE" \
        --condition=None --quiet >/dev/null
done
for SECRET in fivetran-api-key fivetran-api-secret; do
    gcloud secrets add-iam-policy-binding "$SECRET" \
        --member="serviceAccount:${RUNTIME_SA}" \
        --role="roles/secretmanager.secretAccessor" --quiet >/dev/null
done
echo "  granted to ${RUNTIME_SA}"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Update secrets with real Fivetran credentials:"
echo "   echo -n 'YOUR_KEY' | gcloud secrets versions add fivetran-api-key --data-file=-"
echo "   echo -n 'YOUR_SECRET' | gcloud secrets versions add fivetran-api-secret --data-file=-"
echo "2. Deploy the MCP server: ./deploy/scripts/deploy_mcp.sh"
echo "3. Deploy the web UI: ./deploy/scripts/deploy_web.sh"
