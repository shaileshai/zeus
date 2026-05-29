# Build Brief — "AI-Era Data Engineer" Agent

**Google Cloud Rapid Agent Hackathon · Fivetran Track · Target: 1st place**

> Drop this file at the root of your repo (e.g. as `BUILD_BRIEF.md` or `.cursor/rules`). It is the single source of truth for what we are building, why, and the guardrails. Every build decision must trace back to a judging criterion or the differentiator. If it doesn't, cut it.

---

## 1. Objective (one sentence)

Build a web-based AI agent — on **Gemini 3 + Google Cloud Agent Builder** — that **operates a Fivetran data foundation by itself**: given a plain-English goal, it provisions and scopes data pipelines into BigQuery, keeps them fresh and governed, heals them when they break, and answers questions on the result **with lineage** — all under human approval.

**Thesis (the line the whole project must prove):**

> *Because Fivetran exposed its control plane as an open MCP server, the data foundation can now be run by an AI instead of a person. This is ETL for the AI era.*

---

## 2. Why This Wins (keep the build aligned to these)

- **Partner-judge fit.** The Fivetran MCP server was co-authored by a Fivetran hackathon judge. Exercising that MCP's *write* operations well is the most direct way to score with the people grading this track.
- **Mirrors Fivetran's own 2026 go-to-market.** Their flagship message is "data foundation for AI," built on four pillars: **freshness, lineage, governance, interoperability**. The agent operationalizes all four — show their own metric back to them.
- **Beats the competition's framing.** Matillion's "Maia" already builds pipelines from natural language, so *"an AI builds pipelines"* is no longer novel. Our edge is that Fivetran's control plane is an **open MCP protocol any agent can drive**, vs. Maia being a **closed, proprietary assistant welded inside one platform**. Differentiator = open + agent-operable, NOT "an AI does it."
- **Genuinely agentic, not a chatbot.** Multi-step plan → real write actions → human gate → verification loop. This is the "move beyond chat" story.

---

## 3. Judging Criteria (Stage 2, equal weight) — optimize for all four

| Criterion | How we win it |
|---|---|
| **Technological** | Clean separation: reasoning layer (agent) ↔ tooling layer (MCP on Cloud Run) ↔ data layer (BigQuery). Real write-capable MCP calls, not read-only. |
| **Design** | One continuous, legible demo arc. A live **red→green readiness meter** across the 4 pillars. Approval gates visible. No slideware. |
| **Potential Impact** | "Data teams lose weeks babysitting pipelines and 60% of AI projects die on bad data. This agent removes the human from the loop." |
| **Quality of the Idea** | The "ETL for the AI era / open agent-operable control plane" framing — defensible against Matillion/Databricks/Informatica. |

Stage 1 is pass/fail viability: the submission **must unmistakably use both a Fivetran product AND Google Cloud products.** Make both obvious.

---

## 4. HARD RULES — do not violate (auto-disqualifiers)

1. **Must use Gemini + Google Cloud Agent Builder.** ALL non-Google AI tools are prohibited. → Do NOT run the agent on Claude/GPT/etc. → The "bring-your-own-model" idea is DEAD as a feature; "open protocol" stays only as *narrative*, never demonstrated with a non-Google model.
2. **No services competing with Google Cloud or Fivetran.** → Destination is **BigQuery, not Snowflake.** No Airbyte / Matillion / Databricks ingestion anywhere. No AWS/Azure for platform.
3. **New, original project**, built within the contest window (May 5 – June 11, 2026). No reusing prior work.
4. **Platform:** must run on **web** (Android/iOS also allowed). Submit a **public hosted URL**.
5. **Repo:** public, with an **OSI-approved LICENSE file visible at the top** (About section). MIT is fine; the Fivetran MCP is already MIT.
6. **Video:** ≤ 3 minutes, on **YouTube or Vimeo**, English. Only the first 3 min are judged.
7. **Deadline: June 11, 2026 @ 2:00 PM PDT.** Late = disqualified.

**Action with its own deadline:** request the **$100 Google Cloud credit** via the hackathon form by **June 4, 2026** (approval takes 1–5 business days). Do this first.

---

## 5. Architecture (everything runs on Google Cloud)

```
        plain-English goal
                │
                ▼
  ┌──────────────────────┐       Gemini 3 (Vertex AI)
  │  Agent (ADK, Python) │◄────── reasoning / planning
  │  on Vertex AI        │
  │  Agent Engine        │
  └──────────┬───────────┘
             │ MCPToolset (HTTP/SSE)         │ SQL
             ▼                              ▼
  ┌──────────────────────┐     ┌────────────────────┐
  │  Fivetran MCP server │     │     BigQuery        │
  │  (container on       │     │  (data destination) │
  │   Cloud Run)         │     └─────────▲──────────┘
  └──────────┬───────────┘               │ syncs
             │  Fivetran REST API        │
             ▼                           │
  ┌──────────────────────────────────────┴───┐
  │  Fivetran (SaaS trial) — connectors      │
  │  source: Google Sheets / free Postgres   │
  └───────────────────────────────────────────┘

  Secrets (Fivetran API key/secret) → Secret Manager
  Web UI (the hosted URL)           → Cloud Run (or Firebase Hosting)
```

### Component → service map

- **Agent reasoning:** Google Agent Development Kit (ADK), Python 3.11+. Deploy to **Vertex AI Agent Engine** (`adk deploy agent_engine`) — this satisfies the "Agent Builder" requirement. Local dev loop via `adk web`.
- **Model: Gemini 3** via Vertex AI. (Dev on **Gemini 3 Flash**, switch to **Gemini 3 Pro** for final/demo runs — see §8.)
- **Fivetran MCP server:** fork `github.com/fivetran/fivetran-mcp` (MIT), containerize, deploy to Cloud Run, connect from the agent via `MCPToolset` to the remote URL. Set `FIVETRAN_ALLOW_WRITES=true`.
- **Data: BigQuery** dataset (the Fivetran destination + the agent's query target).
- **Web UI:** Cloud Run container (or Firebase Hosting). ADK's `api_server` can serve as the backend.
- **Secrets:** Secret Manager.
- **Fivetran:** SaaS 14-day free trial. Start it ~June 1 so it's still active when you record the demo (don't start today — it would expire on/near the deadline).

### Start from these official skeletons (do NOT build plumbing from scratch)

- Codelab: *"Build and deploy an ADK agent that uses an MCP server on Cloud Run"* — the agent↔remote-MCP pattern.
- Codelab/article: *ADK + BigQuery (MCP) + Agent Engine + Cloud Run* end-to-end — natural-language → SQL on BigQuery. (Google's own example is a World Cup stats agent.)
- ADK deploy docs: `google.github.io/adk-docs/deploy/agent-engine/deploy/`

> **Naming heads-up:** ADK = framework, Agent Engine = runtime, "Agent Builder" = umbrella (also seen as "Agent Platform" / "Gemini Enterprise"). Trust the codelabs over any single product page.

**Fallback if the MCP-on-Cloud-Run spike fights you:** call the **Fivetran REST API** directly from an ADK tool. REST is an official Fivetran integration path and still satisfies "use Partner products." Decide by end of Day 2.

---

## 6. What the Agent Actually Does — MCP tools → behaviors

Set `FIVETRAN_ALLOW_WRITES=true`. Put a **human-approval gate in front of every write** (this is also your answer to the "operates under human oversight" expectation).

| Capability (scores on…) | Fivetran MCP tools |
|---|---|
| **Provision foundation by intent** (Tech, Idea) | `create_destination`, `create_connection`, `modify_connection_table_config` (sync ONLY the tables the goal needs — cost + signal), `run_connection_setup_tests`, `sync_connection` |
| **Self-maintaining freshness** (Impact, Design) | `get_connection_details` (detect staleness), `sync_connection` / `resync_connection`, `create_account_webhook` + `test_webhook` (freshness SLA so it stays live after the demo) |
| **Self-heal** (Impact, Design) | `list_connections`, `get_connection_details`, re-test + re-sync, report |
| **Transform** (differentiation — most entrants ignore this) | `list_transformations`, `run_transformation` (dbt) |
| **Govern** (pillar) | teams / groups / users tools for access scoping |
| **Answer with lineage** (Design, Idea) | query BigQuery; attach provenance to every figure: source connection, table, last sync time (pulled from `get_connection_details`) |

---

## 7. The Demo (this IS the product — build the happy path to be bulletproof)

**Format:** one continuous screen recording, ≤3 min, single goal, no cuts that hide failure. A **readiness meter** (red→green across Freshness / Lineage / Governance / Interoperability) is on screen the whole time.

### Arc:

1. User types a goal: *"Analyze my sales pipeline against support tickets."* (meter: red, ~30%)
2. Agent plans, then **asks approval** to provision → `create_destination` (BigQuery) → `create_connection` (source = a Google Sheet or Postgres) → `modify_connection_table_config` (scopes to only needed tables) → `run_connection_setup_tests` → `sync_connection`. (meter climbing)
3. Agent **answers the question**, querying BigQuery, **with lineage** attached to each number. (Lineage pillar → green)
4. **Break a source** (revoke a credential / corrupt the sheet). Agent detects the failure, diagnoses, **heals** it (re-test + re-sync), and re-verifies. (Freshness pillar → green)
5. Agent sets a **webhook** so the foundation stays fresh going forward. (meter: green, ~92%)
6. Close on the one-liner: *"You didn't hire a data engineer. The agent is the data engineer — and it runs on an open protocol any agent could drive."*

**Demo source choice:** Google Sheets connector = easiest "watch it create a connection live." Free Postgres (Neon/Supabase) as backup. Keep the dataset tiny (MB scale).

---

## 8. Cost Controls (target: <$40 of the $100 credit)

- Dev on **Gemini 3 Flash** (~$0.50/$3 per 1M tok), not Pro (~$2/$12). Switch to **Pro only for final + demo runs.**
- **Context-cache the MCP tool schema.** The 50+ tool definitions are identical every turn; cached reads cost ~10% of base input — this is the single biggest saver in an agentic loop.
- **Never leave an agent loop retrying unattended** while debugging — that's how people burn the whole credit.
- BigQuery (MB data) and Cloud Run (scale-to-zero) are effectively free at this scale; Agent Engine bills at Gemini token rates.

---

## 9. Scope — explicit IN / OUT (protect the 2 weeks)

### IN (MVP = the demo arc in §7, working reliably on web):

- One goal, 1–2 sources, the full provision → answer-with-lineage → self-heal → webhook loop, with approval gates and the readiness meter.

### OUT (do not build):

- Model-swapping / non-Google models (rules-forbidden).
- Snowflake or any competing destination.
- Production hardening, multi-tenant, auth, many connectors, broad error handling beyond the demo path.
- Anything that doesn't show up in the 3-minute video.

---

## 10. Timeline (today → June 11, 2:00 PM PDT)

- **Now / this week:** Submit the **$100 credit form (before June 4)**. Register on Devpost, **join the Fivetran track**. **Day-1 spike:** get the Fivetran MCP running on Cloud Run and called **once** from an ADK agent. If it works, the project is de-risked. (Decide REST fallback by end of Day 2.)
- **Days 3–5:** Happy path — goal → provision (Google Sheet source) → setup tests → sync → query BigQuery → answer. Build on Flash.
- **Days 6–8:** Differentiators — intent-scoping (`modify_connection_table_config`), self-heal, lineage on answers, readiness meter, approval gate.
- **Days 9–10:** Web UI polish, make the happy path bulletproof, switch final runs to Gemini 3 Pro. Start the Fivetran trial timing so it covers recording.
- **Days 11–12:** Record the 3-min video (single scripted take), write the Devpost text description (features, tech, data sources, learnings), clean repo + LICENSE + README, host the app, **submit with a buffer day.**

Solo is feasible but has no slack. A second person on UI + video removes real risk. Team max = 4.

---

## 11. Submission Checklist (Definition of Done)

- [ ] Public **hosted URL**, agent runs on web, happy path works on a fresh load.
- [ ] **Public repo**, OSI LICENSE visible at top, README with run instructions, all source/assets present.
- [ ] **Demo video** ≤3 min on YouTube/Vimeo, English, shows the app functioning.
- [ ] **Text description:** features/functionality, technologies, data sources, findings/learnings.
- [ ] Uses **Gemini 3 + Agent Builder** (obvious) AND a **Fivetran product** (obvious). No prohibited AI or competing services.
- [ ] Submitted on Devpost to the **Fivetran track** before **June 11, 2026, 2:00 PM PDT**.

---

## 12. Key Links

- Hackathon overview / rules / Fivetran resources: `rapid-agent.devpost.com` (`/rules`, `/details/fivetran-resources`)
- Fivetran MCP server (MIT): `github.com/fivetran/fivetran-mcp`
- ADK deploy docs: `google.github.io/adk-docs/deploy/agent-engine/deploy/`
- $100 credit request form: linked from the rules page — **submit by June 4, 2026**

---

## North Star

Not a chatbot that *talks about* data. The **data engineer that builds and maintains the data foundation by itself**, on an open protocol — proven in one unbroken 3-minute take, with a readiness meter going red→green.
