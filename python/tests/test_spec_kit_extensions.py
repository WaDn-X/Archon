"""Tests for spec-kit EARS parsing and plan refinement."""

from pathlib import Path

import pytest

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
