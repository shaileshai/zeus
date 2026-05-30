# Demo data sources

Tiny, MB-scale sample data for the demo arc *"Analyze my sales pipeline against support tickets."*
These mirror the rows already seeded into BigQuery `zeus_data` for local testing, so numbers are
consistent across local runs and the live Fivetran-synced demo.

- `opportunities.csv` — sales pipeline (6 rows): `opportunity_id, account_name, stage, amount, owner, close_date`
- `support_tickets.csv` — support tickets (6 rows): `ticket_id, account_name, status, priority, subject, created_date`

Joinable on `account_name`. Expected answer for *"total pipeline for accounts with an open Critical
ticket"* is **$497,000** (Acme $187k + Hooli $310k) — handy for sanity-checking the demo live.

## Set up the Google Sheets source (primary)

1. Create a new Google Sheet named **`zeus-demo`**.
2. Make two tabs: **`opportunities`** and **`support_tickets`**.
3. Paste each CSV into its tab (File → Import → Upload → *Replace current sheet*, or just paste and
   use Data → Split text to columns).
4. Share the sheet so Fivetran can read it (per the Fivetran Google Sheets connector setup — either
   share with the connector's service account email or use the "named range / shared link" flow the
   connector prompts for).
5. In the demo, Zeus will create the Fivetran connection to this sheet and sync it into
   `zeus_data` — scoping to just these tables via `modify_connection_table_config`.

## Backup source (for the self-heal beat / fallback)

Load `opportunities.csv` into a free Postgres (Neon or Supabase) as table `opportunities`, and use
that connection if the Sheets connector misbehaves on camera. Breaking this source (revoke the role /
rotate the password) is a clean way to trigger the self-heal demonstration.

## Re-seed BigQuery directly (local testing without Fivetran)

```bash
bq query --project_id="$GOOGLE_CLOUD_PROJECT" --use_legacy_sql=false \
  "LOAD DATA OVERWRITE zeus_data.opportunities FROM FILES (format='CSV', uris=['gs://.../opportunities.csv'])"
```
(or use the inline `CREATE OR REPLACE TABLE ... SELECT * FROM UNNEST([...])` form used during setup).
