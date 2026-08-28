"""
Supabase schema generation helpers for DocumentAgent.

Builds PostgreSQL tables with conservative RLS policies using RAG context.
"""

import re
from typing import Any


def find_supabase_source(sources: list[dict[str, Any]]) -> dict[str, Any] | None:
	"""Pick a crawled source that looks like Supabase documentation."""
	for source in sources:
		title = (source.get("title") or "").lower()
		url = (source.get("url") or source.get("source_url") or "").lower()
		source_id = (source.get("source_id") or source.get("id") or "").lower()
		haystack = f"{title} {url} {source_id}"
		if "supabase" in haystack:
			return source
	return None


def parse_entity_lines(entity_descriptions: str) -> list[dict[str, Any]]:
	"""Parse entity description text into structured entities (same shape as create_erd)."""
	entities: list[dict[str, Any]] = []
	current_entity: dict[str, Any] | None = None

	for line in entity_descriptions.split("\n"):
		line = line.strip()
		if line and not line.startswith("-"):
			current_entity = {
				"name": line,
				"attributes": [],
				"primary_key": "id",
			}
			entities.append(current_entity)
		elif line.startswith("-") and current_entity is not None:
			attr_name = line[1:].strip()
			attr_type = _infer_column_type(attr_name)
			current_entity["attributes"].append({
				"name": attr_name,
				"type": attr_type,
				"nullable": True,
			})

	return entities


def _infer_column_type(attr_name: str) -> str:
	name = attr_name.lower()
	if name == "id" or name.endswith("_id"):
		return "UUID"
	if "email" in name:
		return "VARCHAR(255) UNIQUE"
	if "password" in name or "secret" in name or "token" in name:
		return "TEXT"
	if "created" in name or "updated" in name:
		return "TIMESTAMPTZ"
	if "count" in name or "number" in name or name.endswith("_qty"):
		return "INTEGER"
	if "price" in name or "amount" in name or "cost" in name:
		return "NUMERIC(12,2)"
	if name.startswith("is_") or name.startswith("has_"):
		return "BOOLEAN"
	if "json" in name or "metadata" in name or "settings" in name:
		return "JSONB"
	return "TEXT"


def _table_name(entity_name: str) -> str:
	return re.sub(r"[^a-z0-9_]+", "_", entity_name.lower()).strip("_")


def build_supabase_schema(
	*,
	system_name: str,
	entity_descriptions: str,
	rag_snippets: list[str],
	has_supabase_docs: bool,
) -> dict[str, Any]:
	"""
	Build Supabase-oriented schema output with RLS and auth notes.

	Always emits deny-by-default RLS when no project-specific policies are known.
	"""
	entities = parse_entity_lines(entity_descriptions)
	sql_statements: list[str] = []
	rls_statements: list[str] = []
	policy_statements: list[str] = []

	for entity in entities:
		table = _table_name(entity["name"])
		columns = ["    id UUID PRIMARY KEY DEFAULT gen_random_uuid()"]
		for attr in entity["attributes"]:
			col = _table_name(attr["name"])
			nullable = "" if attr["name"].lower() == "id" else " NULL"
			columns.append(f"    {col} {attr['type']}{nullable}")
		columns.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT now()")
		columns.append("    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")

		create_sql = f"CREATE TABLE public.{table} (\n" + ",\n".join(columns) + "\n);"
		sql_statements.append(create_sql)

		rls_statements.append(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")
		policy_statements.append(
			f'CREATE POLICY "{table}_deny_by_default" ON public.{table}\n'
			f"  FOR ALL TO authenticated, anon\n"
			f"  USING (false)\n"
			f"  WITH CHECK (false);"
		)

	auth_notes = [
		"Use Supabase Auth (auth.users) for identity; reference auth.uid() in RLS policies.",
		"Replace deny-by-default policies with role-specific SELECT/INSERT/UPDATE/DELETE rules.",
		"Service-role key bypasses RLS — use only on trusted server-side paths.",
		"Enable Row Level Security on every public table before exposing via PostgREST.",
	]

	if not has_supabase_docs:
		auth_notes.insert(
			0,
			"No Supabase documentation found in the knowledge base. "
			"Crawl https://supabase.com/docs for RLS/auth best practices.",
		)

	rag_context = "\n\n".join(s.strip() for s in rag_snippets if s and s.strip())

	return {
		"system_overview": {
			"name": system_name,
			"database": "Supabase (PostgreSQL)",
			"has_supabase_docs": has_supabase_docs,
		},
		"entities": entities,
		"database_schema": {
			"sql_statements": sql_statements,
			"rls_statements": rls_statements,
			"policy_statements": policy_statements,
			"full_sql": "\n\n".join(sql_statements + rls_statements + policy_statements),
		},
		"auth_notes": auth_notes,
		"rag_context_used": rag_context[:4000] if rag_context else "",
		"supabase_apis": {
			"client_js": "createClient(SUPABASE_URL, SUPABASE_ANON_KEY)",
			"rls_docs": "https://supabase.com/docs/guides/database/postgres/row-level-security",
			"auth_docs": "https://supabase.com/docs/guides/auth",
		},
	}
