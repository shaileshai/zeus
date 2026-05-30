# Zeus — 3-Minute Demo Script (single take)

**Goal:** one continuous screen recording, ≤3:00, no cuts that hide failure. The **readiness meter**
(Freshness / Lineage / Governance / Interoperability) is visible the whole time, moving red→green.
Record at the deployed public URL. Keep the dataset tiny so syncs finish fast.

**Pre-roll checklist (do NOT record this):**
- Deployed `zeus-web` Cloud Run service warm (`--min-instances=1` for the recording).
- Fivetran trial active; API key/secret in Secret Manager. Google Sheet source ready (sales pipeline).
- `zeus_data` BigQuery dataset exists. Meter reset via the ↺ button (or `/api/reset`).
- A second browser tab / terminal ready to "break" the source for the self-heal beat.
- Model set to `GEMINI_MODEL=gemini-3.1-pro-preview` (latest Gemini 3 Pro) with `GOOGLE_CLOUD_LOCATION=global`.

---

### 0:00 — Hook (10s)
**On screen:** Zeus UI, idle state, meter low (~9%, red).
**Narration:**
> "60% of AI projects die on bad data, and data teams lose weeks babysitting pipelines. So we didn't
> build another chatbot — we built the data engineer. This is Zeus. It runs on Gemini and Google ADK,
> and it operates a Fivetran data foundation by itself."

### 0:10 — State the goal (15s)
**Action:** Type the goal and send:
> `Analyze my sales pipeline against our support tickets.`

**Narration:**
> "I give it a plain-English goal. Watch the orchestrator wake up and hand off to the planner."
**On screen:** orchestrator → planner pulses (real `agent_state` events); a plan appears.

### 0:25 — Provision under approval (45s)
**Action:** Confirm/continue so the provisioner executes. When the **approval modal** appears for
`create_destination` / `create_connection`, pause and point at it.
**Narration:**
> "It doesn't just talk — it acts. But every write to my data platform stops for my approval. Here it
> wants to create a BigQuery destination and a Fivetran connection to my sales sheet. I can see the
> exact action and parameters. I approve."
**Action:** Click **Approve & Execute**. Let it run `modify_connection_table_config` (scopes to only
the needed tables), `run_connection_setup_tests`, `sync_connection`, and scope access via
`create_group`/`add_user_to_group` — approving each write.
**Narration (over the access-scoping step):**
> "...and it scopes access to just the analytics team — least privilege. That's the Governance pillar."
**On screen:** tool-activity pills show real MCP calls; **Interoperability**, **Freshness**, and
**Governance** all climb.

### 1:10 — Answer with lineage (35s)
**On screen:** sync completes; analyst pulses; an answer appears.
**Narration:**
> "Now it answers the original question — querying BigQuery directly. And every number carries its
> lineage: which source, which table, how fresh. No naked metrics. The **Lineage** pillar goes green."
**On screen:** e.g. *"Hooli: $310k pipeline with 2 open critical tickets (source: Sales Sheet →
BigQuery, table: opportunities, synced just now)."* Lineage pillar → green.

### 1:45 — Break it, watch it self-heal (50s)
**Action:** In the other tab, revoke the source credential / rename the sheet to break the connection.
Back in Zeus, type:
> `One of my sources just broke — check and fix it.`

**Narration:**
> "Real pipelines break. So I'll break one — revoke the source's access. Zeus detects the failure,
> diagnoses it, re-tests, and re-syncs — re-verifying that it's actually healthy again."
**On screen:** healer pulses; `list_connections` → `get_connection_details` → `run_connection_setup_tests`
→ `sync_connection`; **Freshness** recovers to green.

### 2:35 — Keep it fresh going forward (15s)
**Action:** Approve the webhook creation (`create_account_webhook` + `test_webhook`).
**Narration:**
> "Finally it sets a webhook so the foundation stays fresh after I walk away — a freshness SLA it
> monitors itself."
**On screen:** webhook dot lights; meter ~92% green across all four pillars.

### 2:50 — Close (10s)
**On screen:** full green meter.
**Narration:**
> "You didn't hire a data engineer. The agent *is* the data engineer — and because Fivetran exposed
> its control plane as an open MCP protocol, any agent could drive it. This is ETL for the AI era."

---

**Backups if a live step fights you:** keep a Neon/Supabase Postgres source as an alternate; keep a
known-good recorded take of each risky beat; the ↺ reset lets you re-run cleanly between takes.
