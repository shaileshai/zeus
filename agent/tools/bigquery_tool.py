"""BigQuery query tool for the Zeus agent."""

import logging
from datetime import datetime, timezone

from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

from .. import config

logger = logging.getLogger(__name__)


def query_bigquery(sql: str, dataset: str = "") -> dict:
    """Execute a SQL query on BigQuery and return results with metadata.

    Use this tool to query data that has been synced into BigQuery by Fivetran.
    Tables should be referenced as `dataset.table` or just `table` (default dataset used).

    Args:
        sql: The SQL query to execute. Use standard BigQuery SQL syntax.
             Reference tables as `dataset.table` or just `table`.
        dataset: Optional dataset override. Defaults to the configured BIGQUERY_DATASET.

    Returns:
        A dict with:
        - success: bool
        - rows: list of dicts (up to 100 rows)
        - total_rows: int
        - schema: list of {name, type}
        - bytes_processed: int
        - query_time_ms: int
        - error: str (only if success=False)
    """
    effective_dataset = dataset or config.BIGQUERY_DATASET
    project = config.GOOGLE_CLOUD_PROJECT

    if not project:
        return {
            "success": False,
            "error": "GOOGLE_CLOUD_PROJECT not configured",
            "rows": [],
            "total_rows": 0,
        }

    try:
        client = bigquery.Client(project=project)

        job_config = bigquery.QueryJobConfig(
            default_dataset=f"{project}.{effective_dataset}",
            maximum_bytes_billed=100 * 1024 * 1024,  # 100 MB safety limit
        )

        start = datetime.now(timezone.utc)
        job = client.query(sql, job_config=job_config)
        results = job.result()
        elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

        rows = [dict(row) for row in results]

        logger.info(
            "BigQuery query: %d rows, %d bytes, %dms",
            len(rows),
            job.total_bytes_processed or 0,
            elapsed_ms,
        )

        return {
            "success": True,
            "rows": rows[:100],
            "total_rows": results.total_rows,
            "returned_rows": min(len(rows), 100),
            "schema": [
                {"name": field.name, "type": field.field_type}
                for field in results.schema
            ],
            "bytes_processed": job.total_bytes_processed or 0,
            "query_time_ms": elapsed_ms,
            "dataset": effective_dataset,
            "project": project,
        }

    except GoogleAPIError as e:
        logger.error("BigQuery API error: %s", e)
        return {
            "success": False,
            "error": f"BigQuery API error: {e.message}",
            "rows": [],
            "total_rows": 0,
        }
    except Exception as e:
        logger.error("BigQuery query failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "rows": [],
            "total_rows": 0,
        }


def list_bigquery_tables(dataset: str = "") -> dict:
    """List all tables in the configured BigQuery dataset.

    Use this to discover what data is available before writing queries.

    Args:
        dataset: Dataset to inspect. Defaults to configured BIGQUERY_DATASET.

    Returns:
        A dict with:
        - success: bool
        - tables: list of {name, num_rows, last_modified, size_bytes}
        - dataset: the dataset that was queried
    """
    effective_dataset = dataset or config.BIGQUERY_DATASET
    project = config.GOOGLE_CLOUD_PROJECT

    if not project:
        return {"success": False, "error": "GOOGLE_CLOUD_PROJECT not configured", "tables": []}

    try:
        client = bigquery.Client(project=project)
        dataset_ref = client.dataset(effective_dataset, project=project)
        tables = list(client.list_tables(dataset_ref))

        table_list = []
        for t in tables:
            table_ref = client.get_table(t)
            table_list.append({
                "name": t.table_id,
                "full_name": f"{project}.{effective_dataset}.{t.table_id}",
                "num_rows": table_ref.num_rows,
                "size_bytes": table_ref.num_bytes,
                "last_modified": table_ref.modified.isoformat() if table_ref.modified else None,
            })

        return {
            "success": True,
            "tables": table_list,
            "dataset": effective_dataset,
            "project": project,
            "count": len(table_list),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "tables": []}
