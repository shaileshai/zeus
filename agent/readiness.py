"""Readiness meter — computes the four-pillar data foundation health score.

Pillars:
  Freshness       — are syncs succeeding and recent? webhook active?
  Lineage         — can every answer be traced to its source?
  Governance      — are teams/access controls configured?
  Interoperability — is the open MCP protocol being used?
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PillarScore:
    value: int = 0  # 0-100
    label: str = ""
    detail: str = ""


@dataclass
class ReadinessState:
    freshness: PillarScore = field(default_factory=PillarScore)
    lineage: PillarScore = field(default_factory=PillarScore)
    governance: PillarScore = field(default_factory=PillarScore)
    interoperability: PillarScore = field(default_factory=PillarScore)

    # Tracking data
    connections: list = field(default_factory=list)
    last_updated: Optional[datetime] = None
    webhook_active: bool = False
    mcp_calls_made: int = 0
    lineage_answers: int = 0

    @property
    def overall(self) -> float:
        scores = [
            self.freshness.value,
            self.lineage.value,
            self.governance.value,
            self.interoperability.value,
        ]
        return round(sum(scores) / 4, 1)

    def to_dict(self) -> dict:
        return {
            "pillars": {
                "freshness": {"value": self.freshness.value, "label": self.freshness.label, "detail": self.freshness.detail},
                "lineage": {"value": self.lineage.value, "label": self.lineage.label, "detail": self.lineage.detail},
                "governance": {"value": self.governance.value, "label": self.governance.label, "detail": self.governance.detail},
                "interoperability": {"value": self.interoperability.value, "label": self.interoperability.label, "detail": self.interoperability.detail},
            },
            "overall": self.overall,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "webhook_active": self.webhook_active,
            "mcp_calls_made": self.mcp_calls_made,
            "connections_count": len(self.connections),
        }


# Global state — updated by agent actions
_state = ReadinessState()


def get_state() -> ReadinessState:
    return _state


def reset_state():
    global _state
    _state = ReadinessState()
    _state.interoperability.value = 25  # Base: ADK + MCP architecture in use
    _state.interoperability.label = "MCP architecture configured"
    _state.interoperability.detail = "Agent connects to Fivetran via open MCP protocol"
    _state.governance.value = 10
    _state.governance.label = "Base configuration"
    _state.governance.detail = "No access controls configured yet"


def on_mcp_call(tool_name: str):
    """Called when any MCP tool is invoked."""
    _state.mcp_calls_made += 1
    _state.last_updated = datetime.now(timezone.utc)

    # Every MCP call demonstrates open protocol interoperability
    _state.interoperability.value = min(100, 25 + (_state.mcp_calls_made * 5))
    _state.interoperability.label = f"{_state.mcp_calls_made} MCP operations executed"
    _state.interoperability.detail = "Fivetran control plane driven via open MCP protocol"


def on_connection_created(connection_id: str, connector_type: str):
    """Called when a new Fivetran connection is created."""
    _state.connections.append({"id": connection_id, "type": connector_type, "status": "created"})
    _state.freshness.value = max(_state.freshness.value, 20)
    _state.freshness.label = f"{len(_state.connections)} connection(s) created"
    _state.freshness.detail = "Waiting for initial sync"


def on_sync_started(connection_id: str):
    """Called when a sync is triggered."""
    for c in _state.connections:
        if c["id"] == connection_id:
            c["status"] = "syncing"
    _state.freshness.value = max(_state.freshness.value, 40)
    _state.freshness.label = "Sync in progress"
    _state.freshness.detail = f"Connection {connection_id[:8]}... syncing"


def on_sync_completed(connection_id: str, last_sync_ts: Optional[datetime] = None):
    """Called when a sync completes successfully."""
    for c in _state.connections:
        if c["id"] == connection_id:
            c["status"] = "synced"
            c["last_sync"] = last_sync_ts.isoformat() if last_sync_ts else "just now"

    synced_count = sum(1 for c in _state.connections if c["status"] == "synced")
    total = len(_state.connections)

    freshness_pct = 60 + (synced_count / total * 30) if total > 0 else 60
    _state.freshness.value = int(freshness_pct)
    _state.freshness.label = f"{synced_count}/{total} connections synced"
    _state.freshness.detail = "Data is fresh. Set up webhook for continuous monitoring."


def on_webhook_created():
    """Called when a webhook is successfully configured."""
    _state.webhook_active = True
    _state.freshness.value = min(100, _state.freshness.value + 25)
    _state.freshness.label = "Webhook active — continuous monitoring enabled"
    _state.freshness.detail = "Freshness SLA: agent notified on every sync event"


def on_lineage_answer():
    """Called when agent answers a question with lineage attached."""
    _state.lineage_answers += 1
    _state.lineage.value = min(100, 60 + (_state.lineage_answers * 20))
    _state.lineage.label = f"{_state.lineage_answers} answer(s) with lineage"
    _state.lineage.detail = "Every data point traced to source connection, table, and sync time"


def on_governance_configured(teams_count: int = 0):
    """Called when teams/access controls are configured."""
    base = 40 + min(60, teams_count * 20)
    _state.governance.value = base
    _state.governance.label = f"{teams_count} team(s) configured"
    _state.governance.detail = "Access scoped to required connections"


# Initialize with base scores
reset_state()
