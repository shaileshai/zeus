"""Tests for the readiness meter."""

import pytest
from agent.readiness import (
    ReadinessState,
    get_state,
    reset_state,
    on_mcp_call,
    on_connection_created,
    on_sync_completed,
    on_webhook_created,
    on_lineage_answer,
)


@pytest.fixture(autouse=True)
def fresh_state():
    reset_state()
    yield


def test_initial_state():
    state = get_state()
    assert state.freshness.value == 0
    assert state.governance.value == 10
    assert state.interoperability.value == 25
    assert state.overall == 8.8


def test_mcp_call_increases_interoperability():
    on_mcp_call("list_connections")
    state = get_state()
    assert state.interoperability.value > 25
    assert state.mcp_calls_made == 1


def test_connection_created():
    on_connection_created("conn_123", "google_sheets")
    state = get_state()
    assert state.freshness.value >= 20
    assert len(state.connections) == 1


def test_sync_completed():
    on_connection_created("conn_123", "google_sheets")
    on_sync_completed("conn_123")
    state = get_state()
    assert state.freshness.value >= 60


def test_webhook_boosts_freshness():
    on_connection_created("conn_123", "google_sheets")
    on_sync_completed("conn_123")
    before = get_state().freshness.value
    on_webhook_created()
    assert get_state().freshness.value > before
    assert get_state().webhook_active is True


def test_lineage_answers_increase_score():
    on_lineage_answer()
    assert get_state().lineage.value >= 60
    on_lineage_answer()
    assert get_state().lineage.value >= 80


def test_overall_score():
    state = get_state()
    expected = (
        state.freshness.value
        + state.lineage.value
        + state.governance.value
        + state.interoperability.value
    ) / 4
    assert abs(state.overall - expected) < 0.1


def test_to_dict():
    d = get_state().to_dict()
    assert "pillars" in d
    assert "overall" in d
    assert set(d["pillars"].keys()) == {"freshness", "lineage", "governance", "interoperability"}
