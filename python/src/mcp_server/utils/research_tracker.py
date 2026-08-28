"""
Tracks recent RAG research per MCP client session.

Used to gate task status transitions that imply implementation work.
"""

from datetime import datetime, timedelta

# session_key -> last research timestamp
_session_research: dict[str, datetime] = {}
_DEFAULT_SESSION = "default"
_RESEARCH_TTL_SECONDS = 3600


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
