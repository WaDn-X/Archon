"""Tests for programmatic RAG retrieval gate."""

import pytest

from src.agents.retrieval_gate import (
	build_retrieval_required_failure,
	is_meta_query,
	requires_retrieval_before_answer,
)


class TestRetrievalGateHelpers:
	def test_meta_queries_skip_retrieval(self):
		assert is_meta_query("list available sources")
		assert is_meta_query("What documentation do you have?")
		assert is_meta_query("zeige mir die Quellen")
		assert not requires_retrieval_before_answer("list available sources")

	def test_factual_queries_require_retrieval(self):
		assert requires_retrieval_before_answer("How does JWT authentication work?")
		assert not is_meta_query("How does JWT authentication work?")

	def test_failure_payload_shape(self):
		payload = build_retrieval_required_failure("explain vector search")
		assert payload["success"] is False
		assert payload["error"] == "retrieval_required"


@pytest.mark.asyncio
async def test_rag_agent_auto_retrieves_when_tools_skipped(monkeypatch):
	from src.agents.rag_agent import RagAgent, RagDependencies

	agent = RagAgent(model="test")
	agent.rate_limiter = None

	async def fake_run(prompt: str, deps: RagDependencies) -> str:
		if deps.retrieval_performed:
			return "Answer grounded in retrieved docs about vector search."
		return "Here is a factual answer without citations."

	async def fake_auto_retrieve(query: str, deps: RagDependencies) -> str:
		deps.retrieval_performed = True
		deps.auto_retrieval_used = True
		return "Auto-retrieved knowledge base context:\n[1] Source: docs\nvector search with pgvector"

	monkeypatch.setattr(agent, "run", fake_run)
	monkeypatch.setattr(agent, "_auto_retrieve_context", fake_auto_retrieve)

	result = await agent.run_conversation("explain vector search in our stack")

	assert result.success is True
	assert result.message.endswith("automatic knowledge-base retrieval")
	assert "grounded" in result.answer.lower()


@pytest.mark.asyncio
async def test_rag_agent_meta_query_bypasses_gate(monkeypatch):
	from src.agents.rag_agent import RagAgent, RagDependencies

	agent = RagAgent(model="test")
	agent.rate_limiter = None
	calls = {"count": 0}

	async def fake_run(prompt: str, deps: RagDependencies) -> str:
		calls["count"] += 1
		return "Available sources (2 total):\n- src_a: Docs"

	monkeypatch.setattr(agent, "run", fake_run)

	result = await agent.run_conversation("list available sources")

	assert result.success is True
	assert calls["count"] == 1
	assert result.query_type == "list_sources"
