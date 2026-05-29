"""Lineage tool — formats and presents data provenance for analyst answers."""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def format_lineage(
    connection_name: str,
    connector_type: str,
    table_name: str,
    last_sync_at: Optional[str] = None,
    sync_frequency: Optional[str] = None,
    status: str = "connected",
) -> dict:
    """Format lineage metadata into a structured provenance record.

    Call this after get_connection_details (MCP tool) to build the lineage
    annotation that should accompany every data answer.

    Args:
        connection_name: Human-readable Fivetran connection name
        connector_type: Fivetran connector type (e.g., "google_sheets")
        table_name: The BigQuery table name being cited
        last_sync_at: ISO8601 timestamp of last successful sync
        sync_frequency: Schedule description (e.g., "every 6 hours")
        status: Connection status ("connected", "broken", "paused")

    Returns:
        A structured lineage record with a human-readable annotation string.
    """
    # Compute freshness
    freshness_label = "unknown freshness"
    if last_sync_at:
        try:
            last_sync = datetime.fromisoformat(last_sync_at.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - last_sync
            if delta.total_seconds() < 60:
                freshness_label = "synced just now"
            elif delta.total_seconds() < 3600:
                mins = int(delta.total_seconds() / 60)
                freshness_label = f"synced {mins} min ago"
            elif delta.total_seconds() < 86400:
                hours = int(delta.total_seconds() / 3600)
                freshness_label = f"synced {hours}h ago"
            else:
                days = int(delta.total_seconds() / 86400)
                freshness_label = f"synced {days}d ago"
        except (ValueError, TypeError):
            freshness_label = f"synced at {last_sync_at}"

    # Human-readable connector type
    connector_labels = {
        "google_sheets": "Google Sheets",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "salesforce": "Salesforce",
        "hubspot": "HubSpot",
        "github": "GitHub",
    }
    source_label = connector_labels.get(connector_type, connector_type)

    annotation = (
        f"*source: {connection_name} ({source_label} → BigQuery), "
        f"table: {table_name}, {freshness_label}*"
    )

    return {
        "connection_name": connection_name,
        "connector_type": connector_type,
        "source_label": source_label,
        "table_name": table_name,
        "last_sync_at": last_sync_at,
        "freshness_label": freshness_label,
        "sync_frequency": sync_frequency,
        "status": status,
        "annotation": annotation,
    }
