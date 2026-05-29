# Fivetran MCP Server

This directory will contain the forked [Fivetran MCP server](https://github.com/fivetran/fivetran-mcp).

## Setup

```bash
# Clone the Fivetran MCP server into this directory
git clone https://github.com/fivetran/fivetran-mcp.git .

# Install dependencies
npm install

# Build
npm run build

# Run locally
FIVETRAN_API_KEY=your-key FIVETRAN_API_SECRET=your-secret \
FIVETRAN_ALLOW_WRITES=true MCP_TRANSPORT=sse \
node dist/index.js
```

## Docker

```bash
docker build -t fivetran-mcp .
docker run -p 8080:8080 \
  -e FIVETRAN_API_KEY=your-key \
  -e FIVETRAN_API_SECRET=your-secret \
  -e FIVETRAN_ALLOW_WRITES=true \
  fivetran-mcp
```

## Deploy to Cloud Run

```bash
gcloud run deploy fivetran-mcp \
  --source=. \
  --region=us-central1 \
  --set-secrets=FIVETRAN_API_KEY=fivetran-api-key:latest,FIVETRAN_API_SECRET=fivetran-api-secret:latest \
  --set-env-vars=FIVETRAN_ALLOW_WRITES=true,MCP_TRANSPORT=sse \
  --allow-unauthenticated
```
