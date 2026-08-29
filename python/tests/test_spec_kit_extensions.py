"""Tests for spec-kit EARS parsing, generation, and plan refinement."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.ears_service import (
	generate_and_merge_feature_ears,
	generate_ears_requirements,
	merge_ears_into_feature_md,
)
from src.server.services.plan_refine_service import (
	apply_plan_refinement,
	is_plan_refine_request,
)
from src.server.services.spec_kit_parser import SpecKitParser


@pytest.mark.asyncio
async def test_parse_ears_requirements_from_feature_md(tmp_path: Path):
	feature = tmp_path / "feature.md"
	feature.write_text(
		"# Feature 001: Login\n\n"
		"WHEN a user submits valid credentials THE SYSTEM SHALL issue a JWT.\n"
		"WHEN credentials are invalid THE SYSTEM SHALL return 401.\n"
	)
	parser = SpecKitParser()
	spec = await parser.parse_feature_spec(feature)

	assert len(spec["ears_requirements"]) == 2
	assert spec["ears_requirements"][0]["condition"].lower().startswith("a user submits")
	assert "JWT" in spec["ears_requirements"][0]["behavior"]


@pytest.mark.asyncio
async def test_parse_plan_md_sections(tmp_path: Path):
	plan = tmp_path / "plan.md"
	plan.write_text("## Architecture\n\nUse FastAPI.\n\n## Risks\n\nLatency.\n")
	parser = SpecKitParser()
	sections = await parser.parse_plan_md(plan)
	assert "architecture" in sections
	assert "FastAPI" in sections["architecture"]


def test_plan_refine_intent_en_de():
	assert is_plan_refine_request("please refine the project plan with new scope")
	assert is_plan_refine_request("Plan ändern: API zuerst implementieren")
	assert not is_plan_refine_request("create a new task")


def test_apply_plan_refinement_appends_dated_section():
	original = "## Overview\n\nPhase 1 only.\n"
	refined = apply_plan_refinement(original, "Move auth to phase 1")
	assert "Move auth to phase 1" in refined
	assert "## Refinement (" in refined


@pytest.mark.asyncio
async def test_generate_ears_requirements_produces_when_shall_lines():
	mock_response = MagicMock()
	mock_response.choices = [MagicMock()]
	mock_response.choices[0].message.content = (
		'{"requirements": ['
		'"WHEN the user requests a magic link THE SYSTEM SHALL send a one-time sign-in email", '
		'"WHEN the user opens a valid magic link THE SYSTEM SHALL create a session and redirect to the app"'
		"]}"
	)

	mock_client = AsyncMock()
	mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

	with patch(
		"src.server.services.ears_service.get_llm_client",
	) as mock_get_client, patch(
		"src.server.services.credential_service.credential_service.get_credentials_by_category",
		new=AsyncMock(return_value={"MODEL_CHOICE": "gpt-4.1-nano"}),
	), patch(
		"src.server.services.ears_service.extract_message_text",
		return_value=(
			mock_response.choices[0].message.content,
			"",
			False,
		),
	):
		mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
		mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

		generated = await generate_ears_requirements("Magic-link login")

	assert len(generated) == 2
	assert all(line.startswith("WHEN ") for line in generated)
	assert all("THE SYSTEM SHALL" in line for line in generated)


@pytest.mark.asyncio
async def test_generate_ears_fallback_when_llm_fails():
	with patch(
		"src.server.services.ears_service.get_llm_client",
		side_effect=RuntimeError("LLM unavailable"),
	):
		generated = await generate_ears_requirements("Magic-link login")

	assert 2 <= len(generated) <= 4
	assert all(line.startswith("WHEN ") for line in generated)
	assert all("THE SYSTEM SHALL" in line for line in generated)


def test_merge_ears_creates_requirements_section():
	content = "# Feature 002: Magic Link\n\n### Problem\n\nUsers need passwordless login.\n"
	new_ears = [
		"WHEN the user requests a magic link THE SYSTEM SHALL send a one-time sign-in email.",
	]
	merged = merge_ears_into_feature_md(content, new_ears)

	assert "## Requirements" in merged
	assert "WHEN the user requests a magic link THE SYSTEM SHALL send a one-time sign-in email." in merged


def test_merge_ears_does_not_duplicate():
	content = (
		"# Feature\n\n"
		"WHEN the user requests a magic link THE SYSTEM SHALL send a one-time sign-in email.\n"
	)
	new_ears = [
		"WHEN the user requests a magic link THE SYSTEM SHALL send a one-time sign-in email.",
		"WHEN the magic link is expired THE SYSTEM SHALL reject it and offer to request a new link.",
	]
	merged = merge_ears_into_feature_md(content, new_ears)

	assert merged.count("WHEN the user requests a magic link") == 1
	assert "WHEN the magic link is expired" in merged


def test_merge_ears_preserves_existing_section_content():
	content = (
		"# Feature\n\n"
		"## Requirements\n\n"
		"- WHEN existing requirement THE SYSTEM SHALL stay unchanged.\n"
	)
	new_ears = [
		"WHEN a new event occurs THE SYSTEM SHALL handle it.",
	]
	merged = merge_ears_into_feature_md(content, new_ears)

	assert "WHEN existing requirement THE SYSTEM SHALL stay unchanged." in merged
	assert "WHEN a new event occurs THE SYSTEM SHALL handle it." in merged


@pytest.mark.asyncio
async def test_generate_and_merge_skips_when_existing_ears(tmp_path: Path):
	feature = tmp_path / "feature.md"
	feature.write_text(
		"# Feature 003: Auth\n\n"
		"WHEN a user logs in THE SYSTEM SHALL create a session.\n"
	)
	generated, updated = await generate_and_merge_feature_ears(feature)

	assert generated == []
	assert updated == feature.read_text()


@pytest.mark.asyncio
async def test_generate_and_merge_writes_new_requirements(tmp_path: Path):
	feature = tmp_path / "feature.md"
	feature.write_text(
		"# Feature 004: Magic Link\n\n"
		"### Problem\n\nPasswordless sign-in for returning users.\n"
	)

	mock_response = MagicMock()
	mock_response.choices = [MagicMock()]
	payload = (
		'{"requirements": ['
		'"WHEN the user requests a magic link THE SYSTEM SHALL send a one-time sign-in email"'
		"]}"
	)

	mock_client = AsyncMock()
	mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

	with patch(
		"src.server.services.ears_service.get_llm_client",
	) as mock_get_client, patch(
		"src.server.services.credential_service.credential_service.get_credentials_by_category",
		new=AsyncMock(return_value={"MODEL_CHOICE": "gpt-4.1-nano"}),
	), patch(
		"src.server.services.ears_service.extract_message_text",
		return_value=(payload, "", False),
	):
		mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
		mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

		generated, updated = await generate_and_merge_feature_ears(feature)

	assert len(generated) == 1
	assert "## Requirements" in updated
	parser = SpecKitParser()
	assert len(parser.parse_ears_requirements(updated)) >= 1
