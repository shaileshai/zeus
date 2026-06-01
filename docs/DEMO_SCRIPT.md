# Zeus — 3-Minute Demo Script (single take)

**Goal:** one continuous screen recording, ≤3:00, no cuts that hide failure. The **readiness meter**
(Freshness / Lineage / Governance / Interoperability) is visible the whole time, moving red→green.
Record at the deployed public URL.

**Live URL:** https://zeus-web-pe7cp6h2la-uc.a.run.app

**What is real here:** Zeus operates a *live* Fivetran account through the Fivetran MCP control plane.
Every Fivetran action below (setup tests, sync, group creation, user grant, self-heal, webhook) is a
real API write, gated by your approval. The foundation already has one healthy connection
(`sales_pipeline`, a Fivetran connector) landing data in BigQuery. The business answer is computed
live in BigQuery from the `zeus_data` tables (`opportunities`, `support_tickets`).

**Pre-roll checklist (do NOT record this):**
- `zeus-web` Cloud Run service warm — set `--min-instances=1` for the recording (revert after).
- Meter reset: open `…/api/reset` (or click ↺) so all pillars start low/red.
- Fivetran connection `octavo_impedance` (schema `sales_pipeline`) is **active/connected** (not paused).
- No extra Fivetran groups beyond **Warehouse**; no existing account webhooks (so the live creates are clean).
- A second tab open on the Fivetran dashboard, ready to **pause** the connection for the self-heal beat.
- Model is `gemini-3.1-pro-preview`, `GOOGLE_CLOUD_LOCATION=global` (already set on the service).

---

### 0:00 — Hook (10s)
**On screen:** Zeus UI, idle, meter low (red).
**Narration:**
> "60% of AI projects die on bad data, and data teams lose weeks babysitting pipelines. So we didn't
> build another chatbot — we built the data engineer. This is Zeus. It runs on Gemini 3 and Google
> ADK, and it operates a Fivetran data foundation by itself."

### 0:10 — State the goal (15s)
**Action:** Type and send:
> `Analyze my sales pipeline against our support tickets.`

**Narration:**
> "I give it a plain-English goal. Watch the orchestrator wake up, lay out a plan, and start operating
> my real Fivetran account."
**On screen:** zeus states a 1–2 line plan; tool pills begin (`list_connections`).

### 0:25 — Activate the foundation under approval (40s)
**Action:** As Zeus calls `run_connection_setup_tests` and `sync_connection`, the **approval modal**
appears. Pause and point at it.
**Narration:**
> "It doesn't just talk — it acts. But every write to my data platform stops for my approval. Here it
> wants to re-validate the connection and trigger a fresh sync into BigQuery. I can see the exact
> action and parameters. I approve."
**Action:** Click **Approve & Execute** for each. Then it creates a dedicated **"Analytics Team"**
group and grants only the needed user — approve those too.
**Narration (over the governance step):**
> "…and it scopes access to just the analytics team — least privilege. That's the Governance pillar."
**On screen:** real MCP call pills; **Interoperability**, **Freshness**, and **Governance** climb.

### 1:05 — Answer with lineage (35s)
**On screen:** the `analyst` lights up; an answer appears.
**Narration:**
> "Now it answers the original question — querying BigQuery directly. And every number carries its
> lineage: which tables, and how fresh. No naked metrics. The **Lineage** pillar goes green."
**On screen (real output):**
> **"$497k of open pipeline is at risk — Hooli ($310k) and Acme Corp ($187k) both have open
> critical/high support tickets** (source: BigQuery `zeus_data.opportunities ⨝ support_tickets`,
> refreshed just now via Fivetran connection `octavo_impedance`)."

### 1:40 — Break it, watch it self-heal (55s)
**Action:** In the Fivetran dashboard tab, **pause** the `sales_pipeline` connection (it stops
syncing). Back in Zeus, type:
> `One of my data sources just broke and stopped syncing — check and fix it.`

**Narration:**
> "Real pipelines break. So I'll break one — I'll pause the source so it stops syncing. Zeus detects
> it, diagnoses it, resumes the connection, re-tests, and re-syncs — verifying it's actually healthy
> again."
**On screen:** the `healer` lights up; `list_connections` → `get_connection_details` (detects
**paused**) → `modify_connection {paused:false}` → `run_connection_setup_tests` → `sync_connection`
→ verify. **Freshness** recovers to green. Approve each write.

### 2:35 — Keep it fresh going forward (15s)
**Action:** When Zeus offers a webhook, approve `create_account_webhook` (pointing at this app's
`/api/webhook`) and `test_webhook`.
**Narration:**
> "Finally it sets a webhook so the foundation stays fresh after I walk away — a freshness SLA it
> monitors itself."
**On screen:** webhook test returns success; meter ~90%+ green across all four pillars.

### 2:50 — Close (10s)
**On screen:** full green meter.
**Narration:**
> "You didn't hire a data engineer. The agent *is* the data engineer — and because Fivetran exposed
> its control plane as an open MCP protocol, any agent could drive it. This is ETL for the AI era."

---

**Resilience notes:**
- Each write is human-gated, so if the model proposes a duplicate (e.g. a second group), just **reject**
  it and continue — the demo stays clean.
- The ↺ reset (`/api/reset`) lets you re-run cleanly between takes; re-activate (unpause) the
  connection and delete any extra groups/webhooks the agent created before the next take.
- Keep a known-good recorded take of each risky beat as backup.
