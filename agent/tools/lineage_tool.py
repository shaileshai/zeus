"""Lineage tool — fetches provenance metadata for data answers."""

from typing import Optional


def get_lineage_info(connection_id: str, table_name: str) -> dict:
    """Get lineage information for a specific table from a Fivetran connection.

    Use this after querying BigQuery to attach provenance to your answer.
    Call get_connection_details via MCP first, then use this to format lineage.

    Args:
        connection_id: The Fivetran connection ID that synced this table
        table_name: The name of the table in BigQuery

    Returns:
        A dict with lineage metadata:
        - source_connection: Connection name and type
        - source_table: Original table name in the source
        - last_sync: Timestamp of last successful sync
        - sync_frequency: How often the data refreshes
        - status: Current connection health status
    """
    # This tool is a helper that formats lineage from MCP responses.
    # The actual data comes from calling get_connection_details via MCP.
    # In production, this queries cached connection metadata.
    return {
        "source_connection": f"connection_{connection_id}",
        "source_table": table_name,
        "last_sync": "pending — call get_connection_details for live data",
        "sync_frequency": "pending",
        "status": "pending",
    }
