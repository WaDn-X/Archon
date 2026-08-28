"""Tests for MCP research tracker used by task status gate."""

from src.mcp_server.utils.research_tracker import (
	clear_research,
	has_recent_research,
	mark_research_performed,
)


class DummyCtx:
	def __init__(self, client_id: str = "test-session"):
		self.request_context = type("RC", (), {"client_id": client_id})()


def test_research_tracker_session_flow():
	ctx = DummyCtx("session-a")
	clear_research(ctx)
	assert has_recent_research(ctx) is False
	mark_research_performed(ctx)
	assert has_recent_research(ctx) is True
