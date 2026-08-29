"""
Tracks recent RAG research per MCP client session.

Used to gate task status transitions that imply implementation or research work.
Trivial updates (status-only, rename, chores) are not blocked.
"""

import re
from datetime import datetime, timedelta

# session_key -> last research timestamp
_session_research: dict[str, datetime] = {}
_DEFAULT_SESSION = "default"
_RESEARCH_TTL_SECONDS = 3600

# Task text suggesting knowledge-base research before starting work.
_IMPLEMENTATION_KEYWORD_PATTERN = re.compile(
	r"\b("
	r"implement(?:ation)?|code|fix|feature|docs?|documentation|schema|api|architecture|"
	r"refactor|debug|build|develop|research|design|migrate|integrat(?:e|ion)"
	r")\b",
	re.IGNORECASE,
)

_SUBSTANTIVE_UPDATE_FIELDS = frozenset({"title", "description", "feature"})
_NON_SUBSTANTIVE_UPDATE_FIELDS = frozenset({"assignee", "task_order"})


def _session_key(ctx) -> str:
	"""Derive a session key from MCP context when available."""
	try:
		request_context = getattr(ctx, "request_context", None)
		if request_context is not None:
			client_id = getattr(request_context, "client_id", None)
			if client_id:
				return str(client_id)
			session_id = getattr(request_context, "session_id", None)
			if session_id:
				return str(session_id)
	except Exception:
		pass
	return _DEFAULT_SESSION


def mark_research_performed(ctx) -> None:
	"""Record that the session performed a knowledge-base search."""
	_session_research[_session_key(ctx)] = datetime.now()


def has_recent_research(ctx, max_age_seconds: int = _RESEARCH_TTL_SECONDS) -> bool:
	"""Return True if the session searched the knowledge base recently."""
	last = _session_research.get(_session_key(ctx))
	if last is None:
		return False
	return datetime.now() - last < timedelta(seconds=max_age_seconds)


def clear_research(ctx) -> None:
	"""Clear research flag for a session (mainly for tests)."""
	_session_research.pop(_session_key(ctx), None)


def task_text_indicates_research_needed(*texts: str | None) -> bool:
	"""Return True when task title/description/feature implies KB research."""
	combined = " ".join(text.strip() for text in texts if text and text.strip())
	if not combined:
		return False
	return _IMPLEMENTATION_KEYWORD_PATTERN.search(combined) is not None


def is_trivial_doing_update(
	update_fields: dict[str, object],
	*,
	task_title: str | None = None,
	task_description: str | None = None,
	task_feature: str | None = None,
) -> bool:
	"""
	Return True when moving to 'doing' is a lightweight change that should not require RAG.

	Trivial: status-only, assignee/order-only, or title rename without implementation keywords.
	"""
	changed_fields = set(update_fields.keys())
	substantive_changes = _SUBSTANTIVE_UPDATE_FIELDS & changed_fields

	effective_title = str(update_fields.get("title", task_title) or "")
	effective_description = str(update_fields.get("description", task_description) or "")
	effective_feature = str(update_fields.get("feature", task_feature) or "")
	effective_text = f"{effective_title} {effective_description} {effective_feature}"

	if task_text_indicates_research_needed(effective_text):
		return False

	if not substantive_changes:
		non_status = changed_fields - {"status"}
		return non_status <= _NON_SUBSTANTIVE_UPDATE_FIELDS

	if substantive_changes == {"title"}:
		new_title = str(update_fields.get("title") or "")
		return not task_text_indicates_research_needed(new_title)

	return False


def project_has_linked_sources(project: dict | None) -> bool:
	"""Return True when a project has linked technical or business knowledge sources."""
	if not project:
		return False
	technical = project.get("technical_sources") or []
	business = project.get("business_sources") or []
	return bool(technical or business)


def requires_research_before_doing(
	*,
	update_fields: dict[str, object],
	task_title: str | None = None,
	task_description: str | None = None,
	task_feature: str | None = None,
	project: dict | None = None,
) -> bool:
	"""
	Return True when status=doing should be blocked without a recent rag_search_* call.

	Research is required when task text implies implementation work, or when the project
	has linked knowledge sources and the update is not trivial.
	"""
	effective_title = str(update_fields.get("title", task_title) or "")
	effective_description = str(update_fields.get("description", task_description) or "")
	effective_feature = str(update_fields.get("feature", task_feature) or "")

	if task_text_indicates_research_needed(effective_title, effective_description, effective_feature):
		return True

	if project_has_linked_sources(project) and not is_trivial_doing_update(
		update_fields,
		task_title=task_title,
		task_description=task_description,
		task_feature=task_feature,
	):
		return True

	return False
