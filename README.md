# Zeus — AI-Era Data Engineer

> An AI agent that builds and maintains your data foundation. Give it a plain-English goal; it provisions Fivetran pipelines into BigQuery under human approval, keeps them fresh, heals them when they break, and answers questions with full lineage.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live demo:** https://zeus-web-pe7cp6h2la-uc.a.run.app
**Demo video:** https://youtu.be/IWtYfUCtd08

## What is Zeus?

Zeus is an AI agent built on **Google Cloud (Gemini 3 on Vertex AI + Google ADK)** that operates a **Fivetran** data foundation autonomously:

1. **Provision by intent** — describe what you want to analyze; Zeus plans and creates the pipelines.
2. **Human-in-the-loop** — every write (create/modify/sync) pauses for explicit operator approval.
3. **Self-healing** — detects broken connections, diagnoses, re-tests and re-syncs.
4. **Answers with lineage** — every figure is traced to its source connection, table, and sync time.
5. **Open protocol** — drives Fivetran's control plane via **MCP** (Model Context Protocol), not a closed API.

A live **readiness meter** tracks the four data-foundation pillars — Freshness, Lineage, Governance, Interoperability — moving red→green as the agent works.

Built for the [Google Cloud Rapid Agent Hackathon](https://rapid-agent.devpost.com/) · Fivetran Track.

## Architecture

```
        plain-English goal
                │
                ▼
   Web UI + FastAPI (Cloud Run)
                │  in-process ADK Runner
                ▼
   Zeus root agent (Gemini on Vertex AI)
     ├─ planner / provisioner / healer / analyst sub-agents
     ├─ Fivetran MCP server  ── Fivetran REST API ── sources (Google Sheets / Postgres)
     └─ BigQuery (query + lineage)            │
                                               ▼ syncs
                                          BigQuery (zeus_data)

   Secrets (Fivetran key/secret) → Secret Manager
   Approval gate: ADK tool-confirmation surfaced to the UI before every write
```

The agent runs **in-process** inside the Cloud Run web service via an ADK `Runner`; the Fivetran MCP
server runs as a stdio subprocess in the same container by default (set `FIVETRAN_MCP_URL` to use a
separate Cloud Run MCP service over SSE instead). The model is served by **Vertex AI** (not the AI
Studio API key) to satisfy the hackathon's Gemini + Agent Builder requirement.

## Quick Start (local)

### Prerequisites
- Python 3.11+
- A Google Cloud project with billing enabled, Vertex AI + BigQuery APIs on
- A Fivetran account (free trial) with an API key/secret
- `gcloud` CLI

### Run
```bash
git clone https://github.com/shaileshai/zeus.git
cd zeus

python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env: set GOOGLE_CLOUD_PROJECT, FIVETRAN_API_KEY, FIVETRAN_API_SECRET

# Authenticate to Vertex AI / BigQuery (the agent uses ADC, no API key):
gcloud auth application-default login

# Start the web app + agent (MCP runs in-process over stdio):
python web/server.py            # serves on http://localhost:$WEB_PORT (default 8000)
```

Alternatively, `adk web` launches ADK's built-in dev chat UI against the same `root_agent`,
and `docker compose up --build` runs the production container locally (mounts your ADC).

### Environment Variables
See `.env.example`. Key ones: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` (the Vertex model
endpoint — **`global`** for Gemini 3), `GOOGLE_CLOUD_REGION` (resources, e.g. `us-central1`),
`GOOGLE_GENAI_USE_VERTEXAI=true`, `GEMINI_MODEL`, `FIVETRAN_API_KEY`, `FIVETRAN_API_SECRET`,
`MCP_TRANSPORT` (`stdio` local / `sse` remote), `BIGQUERY_DATASET`.

## Deploy to Google Cloud

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_REGION=us-central1   # Cloud Run / BigQuery region (model uses the global endpoint)

# One-time: enable APIs, Artifact Registry, BigQuery dataset, secrets, IAM grants
./deploy/scripts/setup_gcp.sh

# Add your real Fivetran credentials to Secret Manager:
echo -n 'YOUR_KEY'    | gcloud secrets versions add fivetran-api-key    --data-file=-
echo -n 'YOUR_SECRET' | gcloud secrets versions add fivetran-api-secret --data-file=-

# Build + deploy the web app (prints the public URL):
./deploy/scripts/deploy_web.sh
```

## Project Structure
```
zeus/
├── agent/          # ADK agent: root + planner/provisioner/healer/analyst, tools, approval gate, readiness meter
├── mcp_server/     # Fivetran MCP server (fork) + SSE wrapper + Dockerfile
├── web/            # FastAPI server (ADK Runner + SSE) and static UI
├── deploy/         # GCP setup + Cloud Run deploy scripts
├── docs/           # Demo script, Devpost write-up
└── tests/          # Unit tests (approval gate, readiness, tools)
```

## Tech Stack
- **Agent framework:** [Google ADK](https://google.github.io/adk-docs/) 2.1 (Python)
- **Model:** Gemini 3 on **Vertex AI** (`gemini-3-flash-preview` for dev, `gemini-3.1-pro-preview` for the demo; served from the `global` endpoint)
- **Data integration:** [Fivetran MCP server](https://github.com/fivetran/fivetran-mcp) (MIT), write operations enabled
- **Data warehouse:** BigQuery
- **Web:** FastAPI + server-sent events + vanilla JS
- **Infrastructure:** Google Cloud Run, Secret Manager, Artifact Registry

## License
MIT — see [LICENSE](./LICENSE)
