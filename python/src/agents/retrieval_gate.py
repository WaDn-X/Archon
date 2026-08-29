"""
Programmatic retrieval gate for RAG agents.

Ensures factual answers are grounded in knowledge-base retrieval before synthesis.
Meta queries (list sources, availability) bypass the gate.
"""

import re

# Queries that only need source listing / metadata — no document retrieval required.
_META_QUERY_PATTERNS: tuple[re.Pattern[str], ...] = (
	re.compile(r"\b(list|show|display|what are)\b.*\b(sources?|knowledge\s*base)\b", re.I),
	re.compile(r"\bwhat\s+(docs?|documentation)\s+do\s+you\s+have\b", re.I),
	re.compile(r"\bwhich\s+sources?\b", re.I),
	re.compile(r"\bavailable\s+sources?\b", re.I),
	re.compile(r"\bsources?\s+available\b", re.I),
	re.compile(r"^sources?\??$", re.I),
	re.compile(r"\b(zeige?|liste?)\b.*\b(quellen|sources)\b", re.I),
	re.compile(r"\bwelche\s+quellen\b", re.I),
)

# Tool names that count as knowledge retrieval (not meta listing).
RETRIEVAL_TOOL_NAMES: frozenset[str] = frozenset({
	"search_documents",
	"search_code_examples",
	"rag_search_knowledge_base",
	"rag_search_code_examples",
	"rag_read_full_page",
})


def is_meta_query(query: str) -> bool:
	"""Return True when the query only needs source/metadata listing."""
	normalized = query.strip()
	if not normalized:
		return True
	return any(pattern.search(normalized) for pattern in _META_QUERY_PATTERNS)


def requires_retrieval_before_answer(query: str) -> bool:
	"""Return True when a factual answer must be preceded by retrieval."""
	return not is_meta_query(query)


def build_retrieval_required_failure(query: str) -> dict[str, object]:
	"""Structured failure payload when retrieval was skipped."""
	return {
		"success": False,
		"error": "retrieval_required",
		"message": (
			"Cannot provide a factual answer without searching the knowledge base first. "
			"Call search_documents or rag_search_knowledge_base, then retry."
		),
		"query": query,
		"auto_retrieval_attempted": False,
	}
