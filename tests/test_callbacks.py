"""Unit tests for the write-tool approval gate in before_tool_callback.

Regression guard: the gate must (a) let reads through, (b) request confirmation
and short-circuit the first time a write is attempted, (c) reject when the
operator declines, and (d) proceed once confirmation is granted.
"""

from agent.callbacks import before_tool_callback, is_write_tool


class _FakeTool:
    def __init__(self, name):
        self.name = name


class _FakeConfirmation:
    def __init__(self, confirmed):
        self.confirmed = confirmed


class _FakeContext:
    def __init__(self, confirmation=None):
        self.tool_confirmation = confirmation
        self.requested = []

    def request_confirmation(self, hint=""):
        self.requested.append(hint)


def test_is_write_tool_detection():
    assert is_write_tool("create_connection")
    assert is_write_tool("sync_connection")
    assert is_write_tool("run_connection_setup_tests")
    assert not is_write_tool("list_connections")
    assert not is_write_tool("get_connection_details")
    assert not is_write_tool("query_bigquery")


def test_read_tool_proceeds_without_confirmation():
    ctx = _FakeContext()
    result = before_tool_callback(_FakeTool("list_connections"), {}, ctx)
    assert result is None
    assert ctx.requested == []


def test_write_tool_requests_confirmation_and_blocks():
    ctx = _FakeContext(confirmation=None)
    result = before_tool_callback(_FakeTool("create_connection"), {"service": "google_sheets"}, ctx)
    assert isinstance(result, dict) and "error" in result  # short-circuited
    assert len(ctx.requested) == 1  # confirmation was requested


def test_write_tool_proceeds_when_confirmed():
    ctx = _FakeContext(confirmation=_FakeConfirmation(confirmed=True))
    result = before_tool_callback(_FakeTool("create_connection"), {}, ctx)
    assert result is None  # approved → proceed


def test_write_tool_rejected_when_declined():
    ctx = _FakeContext(confirmation=_FakeConfirmation(confirmed=False))
    result = before_tool_callback(_FakeTool("create_connection"), {}, ctx)
    assert isinstance(result, dict)
    assert result.get("status") == "rejected"
