"""Tests for Supabase schema generation helpers."""

from src.agents.supabase_schema import (
	build_supabase_schema,
	find_supabase_source,
	parse_entity_lines,
)


def test_find_supabase_source():
	sources = [
		{"title": "React Docs", "url": "https://react.dev"},
		{"title": "Supabase Reference", "source_id": "src_supa"},
	]
	match = find_supabase_source(sources)
	assert match is not None
	assert match["source_id"] == "src_supa"


def test_build_schema_includes_rls_and_auth_notes():
	entities = "Users\n- email\n- display_name"
	schema = build_supabase_schema(
		system_name="Auth",
		entity_descriptions=entities,
		rag_snippets=["Use auth.uid() in policies"],
		has_supabase_docs=False,
	)

	sql = schema["database_schema"]["full_sql"]
	assert "CREATE TABLE public.users" in sql
	assert "ENABLE ROW LEVEL SECURITY" in sql
	assert "deny_by_default" in sql
	assert any("supabase.com/docs" in note for note in schema["auth_notes"])


def test_parse_entity_lines_types():
	entities = parse_entity_lines("Orders\n- total_amount\n- is_paid")
	assert entities[0]["name"] == "Orders"
	types = {attr["name"]: attr["type"] for attr in entities[0]["attributes"]}
	assert types["total_amount"] == "NUMERIC(12,2)"
	assert types["is_paid"] == "BOOLEAN"


def test_build_schema_uses_rag_context_field():
	schema = build_supabase_schema(
		system_name="Shop",
		entity_descriptions="Products\n- name",
		rag_snippets=["CREATE POLICY example USING (auth.uid() = user_id)"],
		has_supabase_docs=True,
	)
	assert "auth.uid()" in schema["rag_context_used"]
	assert schema["system_overview"]["has_supabase_docs"] is True
