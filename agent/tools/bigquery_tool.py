"""BigQuery query tool for the Zeus agent."""

from google.cloud import bigquery

from .. import config


def query_bigquery(sql: str) -> dict:
    """Execute a SQL query on BigQuery and return results with metadata.

    Use this tool to query data that has been synced into BigQuery by Fivetran.
    Always include the dataset prefix in table references.

    Args:
        sql: The SQL query to execute. Tables should be referenced as
             `project.dataset.table` or `dataset.table`.

    Returns:
        A dict containing:
        - rows: List of result rows as dicts
        - total_rows: Total number of rows returned
        - schema: List of column definitions (name + type)
        - bytes_processed: Bytes scanned by the query
    """
    client = bigquery.Client(project=config.GOOGLE_CLOUD_PROJECT)

    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{config.GOOGLE_CLOUD_PROJECT}.{config.BIGQUERY_DATASET}",
        maximum_bytes_billed=100 * 1024 * 1024,  # 100 MB safety limit
    )

    try:
        job = client.query(sql, job_config=job_config)
        results = job.result()

        rows = [dict(row) for row in results]

        return {
            "success": True,
            "rows": rows[:100],  # Cap at 100 rows for context window
            "total_rows": results.total_rows,
            "schema": [
                {"name": field.name, "type": field.field_type}
                for field in results.schema
            ],
            "bytes_processed": job.total_bytes_processed,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "rows": [],
            "total_rows": 0,
        }
