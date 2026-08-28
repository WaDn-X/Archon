"""
Plan refinement for spec-kit projects.

Updates plan.md content from user feedback without a separate agent graph.
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# English + German keywords for plan-refine intent detection
_PLAN_REFINE_PATTERNS: tuple[re.Pattern[str], ...] = (
	re.compile(r"\b(refine|update|revise|change|adjust)\b.*\bplan\b", re.I),
	re.compile(r"\bplan\b.*\b(refine|update|revise|change|adjust)\b", re.I),
	re.compile(r"\b(ändern|aktualisieren|anpassen|überarbeiten|ueberarbeiten)\b.*\bplan\b", re.I),
	re.compile(r"\bplan\b.*\b(ändern|aktualisieren|anpassen|überarbeiten|ueberarbeiten)\b", re.I),
)


def is_plan_refine_request(message: str) -> bool:
	"""Detect EN/DE plan-refine intent in user text."""
	return any(pattern.search(message) for pattern in _PLAN_REFINE_PATTERNS)


def apply_plan_refinement(plan_content: str, feedback: str) -> str:
	"""
	Merge user feedback into an existing plan.md body.

	Appends a dated refinement section and patches matching ## sections when possible.
	"""
	feedback = feedback.strip()
	if not feedback:
		return plan_content

	timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
	refinement_block = (
		f"\n\n## Refinement ({timestamp})\n\n"
		f"{feedback}\n"
	)

	# Try to update a section mentioned in feedback (e.g. "update architecture section")
	section_match = re.search(
		r"\b(?:section|abschnitt)\s+[\"']?([a-z0-9 _-]+)[\"']?",
		feedback,
		re.I,
	)
	if section_match:
		section_name = section_match.group(1).strip().title()
		section_header = f"## {section_name}"
		if section_header.lower() in plan_content.lower():
			pattern = re.compile(
				rf"(##\s+{re.escape(section_name)}\s*\n)(.*?)(?=\n##\s+|\Z)",
				re.I | re.S,
			)
			plan_content = pattern.sub(
				rf"\1{feedback}\n",
				plan_content,
				count=1,
			)
			return plan_content + refinement_block

	return plan_content + refinement_block


def resolve_plan_file(feature_dir: str | None, specs_dir: str = "specs") -> Path | None:
	"""Resolve plan.md path from spec-kit feature directory metadata."""
	if not feature_dir:
		return None
	path = Path(feature_dir)
	if path.is_absolute() and (path / "plan.md").exists():
		return path / "plan.md"
	candidate = Path(specs_dir) / Path(feature_dir).name / "plan.md"
	if candidate.exists():
		return candidate
	nested = Path(specs_dir) / feature_dir / "plan.md"
	if nested.exists():
		return nested
	return None


def build_plan_document_blocks(title: str, plan_content: str) -> list[dict[str, Any]]:
	"""Convert plan markdown into document blocks for Archon storage."""
	blocks: list[dict[str, Any]] = [
		{
			"id": "plan-title",
			"type": "heading_1",
			"content": title,
			"properties": {"text": title},
		},
	]
	for line in plan_content.split("\n"):
		if line.startswith("## "):
			blocks.append({
				"id": f"plan-{len(blocks)}",
				"type": "heading_2",
				"content": line[3:].strip(),
				"properties": {"text": line[3:].strip()},
			})
		elif line.strip():
			blocks.append({
				"id": f"plan-{len(blocks)}",
				"type": "paragraph",
				"content": line.strip(),
				"properties": {"text": line.strip()},
			})
	return blocks
