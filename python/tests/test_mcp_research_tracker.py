"""Tests for MCP research tracker and softer doing-status gate."""

from src.mcp_server.utils.research_tracker import (
	clear_research,
	has_recent_research,
	is_trivial_doing_update,
	mark_research_performed,
	project_has_linked_sources,
	requires_research_before_doing,
	task_text_indicates_research_needed,
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


class TestTaskTextKeywords:
	def test_implementation_keywords_detected(self):
		assert task_text_indicates_research_needed("Implement OAuth login")
		assert task_text_indicates_research_needed("Fix API timeout bug")
		assert task_text_indicates_research_needed("Update schema migration")

	def test_trivial_chore_text_not_flagged(self):
		assert not task_text_indicates_research_needed("Weekly standup notes")
		assert not task_text_indicates_research_needed("Rename task label")


class TestTrivialDoingUpdate:
	def test_status_only_is_trivial(self):
		assert is_trivial_doing_update(
			{"status": "doing"},
			task_title="Weekly standup notes",
			task_description="",
		)

	def test_assignee_only_is_trivial(self):
		assert is_trivial_doing_update(
			{"status": "doing", "assignee": "User"},
			task_title="Housekeeping",
		)

	def test_title_rename_without_keywords_is_trivial(self):
		assert is_trivial_doing_update(
			{"status": "doing", "title": "Standup notes (Tuesday)"},
			task_title="Standup notes",
		)

	def test_implementation_task_is_not_trivial(self):
		assert not is_trivial_doing_update(
			{"status": "doing"},
			task_title="Implement JWT refresh tokens",
		)


class TestRequiresResearchBeforeDoing:
	def test_keyword_task_requires_research_even_without_project_sources(self):
		assert requires_research_before_doing(
			update_fields={"status": "doing"},
			task_title="Implement caching layer",
		)

	def test_trivial_status_only_allowed_without_research(self):
		assert not requires_research_before_doing(
			update_fields={"status": "doing"},
			task_title="Weekly standup notes",
			project={"technical_sources": [{"id": "src-1"}], "business_sources": []},
		)

	def test_non_trivial_update_with_linked_sources_requires_research(self):
		assert requires_research_before_doing(
			update_fields={"status": "doing", "description": "Expanded scope for Q3"},
			task_title="Quarterly planning",
			project={"technical_sources": ["src-1"], "business_sources": []},
		)

	def test_project_without_sources_and_trivial_task_allowed(self):
		assert not requires_research_before_doing(
			update_fields={"status": "doing"},
			task_title="Rename column header",
			project={"technical_sources": [], "business_sources": []},
		)


def test_project_has_linked_sources():
	assert project_has_linked_sources({"technical_sources": ["a"], "business_sources": []})
	assert project_has_linked_sources({"technical_sources": [], "business_sources": ["b"]})
	assert not project_has_linked_sources({"technical_sources": [], "business_sources": []})
	assert not project_has_linked_sources(None)
