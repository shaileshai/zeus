# Zeus — AI-Era Data Engineer

> An AI agent that builds and maintains your data foundation. Drop in a goal, get a fully provisioned, self-healing data pipeline with answers backed by lineage.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is Zeus?

Zeus is an AI agent built on **Google Cloud (Gemini 3 + ADK + Vertex AI Agent Engine)** that operates a **Fivetran** data foundation autonomously:

1. **Provision by intent** — Describe what you want to analyze; Zeus creates the pipelines
2. **Self-healing** — Detects and fixes broken connections automatically
3. **Answers with lineage** — Every data point traced back to source, table, and sync time
4. **Open protocol** — Drives Fivetran via MCP (Model Context Protocol), not a closed API

Built for the [Google Cloud Rapid Agent Hackathon](https://rapid-agent.devpost.com/) · Fivetran Track.

## Architecture

```
User → Web UI (Cloud Run)
         → ADK Agent (Vertex AI Agent Engine, Gemini 3)
              → Fivetran MCP Server (Cloud Run) → Fivetran SaaS → Sources
              → BigQuery (query + lineage)
```

## Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud project with billing enabled
- Fivetran account (free trial)
- Docker (for local MCP server)

### Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/zeus.git
cd zeus

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run the MCP server locally
cd mcp_server && docker compose up -d && cd ..

# Start the agent (local dev)
adk web
```

### Environment Variables

See `.env.example` for all required configuration.

## Project Structure

```
zeus/
├── agent/          # ADK Agent (core logic, sub-agents, tools)
├── mcp_server/     # Fivetran MCP server (Docker)
├── web/            # Web UI (FastAPI + static frontend)
├── deploy/         # GCP deployment scripts
└── tests/          # Test suite
```

## Tech Stack

- **Agent Framework:** [Google ADK](https://google.github.io/adk-docs/) (Python)
- **Model:** Gemini 3 (Flash for dev, Pro for production)
- **Runtime:** Vertex AI Agent Engine
- **Data Integration:** [Fivetran MCP Server](https://github.com/fivetran/fivetran-mcp) (MIT)
- **Data Warehouse:** BigQuery
- **Web:** FastAPI + Vanilla JS
- **Infrastructure:** Google Cloud Run, Secret Manager

## License

MIT — see [LICENSE](./LICENSE)
