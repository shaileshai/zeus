# Zeus — AI-Era Data Engineer (Devpost submission text)

> Draft for the Devpost project description. Fill the bracketed links before submitting.

**Tagline:** The data engineer that builds and maintains your data foundation by itself — on an open, agent-operable control plane.

**Links:** Live app: `[CLOUD_RUN_URL]` · Demo video: `[YOUTUBE_URL]` · Repo: `[GITHUB_URL]`

---

## Inspiration
60% of enterprise AI projects stall on bad data, and data teams burn weeks babysitting pipelines —
provisioning connectors, scoping tables, chasing broken syncs, re-explaining where a number came from.
Tools like Matillion's "Maia" already generate pipelines from natural language, but they're closed,
proprietary assistants welded inside one platform. The interesting shift in 2026 is that **Fivetran
exposed its control plane as an open MCP server** — which means the data foundation can now be operated
by *any* AI agent, not a person. We wanted to prove that thesis end to end: not a chatbot that talks
about data, but an agent that genuinely runs the foundation.

## What it does
You give Zeus a plain-English goal (e.g., *"Analyze my sales pipeline against support tickets"*) and it:
- **Plans and provisions** the pipeline — creates a BigQuery destination and a Fivetran connection,
  scopes the sync to only the tables the goal needs, runs setup tests, and triggers the sync.
- **Asks for approval before every write.** A human-in-the-loop gate pauses the agent and shows the
  exact action and parameters before anything mutates your data platform.
- **Answers the question with lineage** — queries BigQuery and attaches provenance to every figure
  (source connection, table, freshness).
- **Self-heals** — when a source breaks, it detects, diagnoses, re-tests, re-syncs, and re-verifies.
- **Stays fresh** — sets a webhook so it monitors sync health after you walk away.

A live **readiness meter** across four pillars — Freshness, Lineage, Governance, Interoperability —
moves red→green as the agent works, mirroring Fivetran's own "data foundation for AI" framing.

## How we built it
- **Reasoning layer:** a Google **ADK** agent (`root_agent`) with four sub-agents — planner,
  provisioner, healer, analyst — orchestrated by **Gemini 3** on **Vertex AI**
  (`gemini-3-flash-preview` for dev, `gemini-3.1-pro-preview` for the demo).
- **Tooling layer:** the **Fivetran MCP server** (the official MIT fork) with write operations
  enabled, exposing ~77 Fivetran control-plane tools to the agent over MCP.
- **Data layer:** **BigQuery** as both the Fivetran destination and the agent's query target, with
  lineage assembled from connection metadata.
- **Approval gate:** implemented on ADK's native tool-confirmation flow — write tools pause the run
  and surface an approval request to the web UI, which resumes the agent on the operator's decision.
- **Web app:** FastAPI driving the agent in-process via an ADK `Runner`, streaming real agent events
  (tokens, sub-agent transfers, tool calls, meter updates, approval requests) to a custom UI over SSE.
- **Infrastructure:** Cloud Run (web + agent + MCP), Secret Manager for Fivetran credentials, all on
  Google Cloud.

## Data sources
- **Google Sheets** (primary demo source: a small sales-pipeline sheet) synced via Fivetran.
- A free **Postgres** instance (Neon/Supabase) as a backup source for the self-heal demonstration.
- **BigQuery** dataset `zeus_data` as the destination and analytics target.

## Challenges we ran into
- **Per-tool approval gating in ADK.** `McpToolset.require_confirmation` receives the tool's *args*,
  not its name, and `ToolContext` doesn't expose the tool name — so it can't gate "writes only." We
  moved gating into `before_tool_callback` (which gets `tool.name`) and replicated ADK's native
  confirmation flow, then applied it to the root agent *and* every sub-agent (the provisioner does the
  real writes and would otherwise bypass the gate).
- **Streaming the human-in-the-loop round-trip** cleanly over SSE: detect the `adk_request_confirmation`
  event, surface it as an approval modal, and resume the same invocation with a `FunctionResponse`.
- **SQL correctness:** the analyst initially fan-out-joined one-row-per-entity to one-row-per-event
  tables, inflating sums — fixed by instructing pre-aggregation before joins.

## Accomplishments we're proud of
- A genuinely **agentic** loop — multi-step plan → real write-capable MCP calls → human gate →
  verification — not a chatbot.
- The whole thing runs on the **required stack**: Gemini + ADK on Vertex AI, driving Fivetran via the
  open MCP protocol, into BigQuery.
- A single, legible demo arc with a red→green readiness meter and visible approval gates.

## What we learned
- Exposing a SaaS control plane as MCP genuinely makes it agent-operable — the "open protocol" story
  isn't just narrative; the same agent code would drive any MCP-compliant control plane.
- Human-in-the-loop is a feature, not a tax: surfacing each write for approval is exactly the
  oversight enterprises need to trust an autonomous data engineer.

## What's next
- Column-level lineage and dbt transformation orchestration (`run_transformation`).
- Governance scoping via Fivetran teams/groups as a first-class pillar.
- Scheduled, fully-autonomous freshness monitoring driven by the webhook.
