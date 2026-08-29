"""
EARS requirements generation and feature.md merge service.

Generates WHEN/THE SYSTEM SHALL requirements from feature text using the
configured LLM provider, with a deterministic fallback when the LLM is unavailable.
"""

import json
import re
from pathlib import Path
from typing import Any

from ..config.logfire_config import get_logger
from .llm_provider_service import extract_message_text, get_llm_client

logger = get_logger(__name__)

_EARS_LINE_PATTERN = re.compile(
	r"WHEN\s+(.+?)\s+THE\s+SYSTEM\s+SHALL\s+(.+?)(?:\.|$)",
	re.IGNORECASE | re.MULTILINE,
)

_REQUIREMENTS_SECTION_PATTERN = re.compile(
	r"^##\s+(Requirements|EARS)\s*$",
	re.IGNORECASE | re.MULTILINE,
)


def normalize_ears_line(condition: str, behavior: str) -> str:
	"""Build a canonical EARS requirement line."""
	return f"WHEN {condition.strip()} THE SYSTEM SHALL {behavior.strip()}."


def _normalize_for_dedup(text: str) -> str:
	"""Normalize EARS text for idempotent deduplication."""
	return re.sub(r"\s+", " ", text.strip().rstrip(".").lower())


def existing_ears_texts(existing_ears: list[Any]) -> set[str]:
	"""Collect normalized EARS texts from dict or string entries."""
	texts: set[str] = set()
	for item in existing_ears:
		if isinstance(item, dict):
			text = item.get("text") or normalize_ears_line(
				item.get("condition", ""),
				item.get("behavior", ""),
			)
		else:
			text = str(item)
		if text.strip():
			texts.add(_normalize_for_dedup(text))
	return texts


def parse_ears_line(line: str) -> dict[str, str] | None:
	"""Parse a single EARS line into structured fields."""
	match = _EARS_LINE_PATTERN.search(line.strip())
	if not match:
		return None
	condition = match.group(1).strip()
	behavior = match.group(2).strip()
	return {
		"condition": condition,
		"behavior": behavior,
		"text": normalize_ears_line(condition, behavior),
	}


def _extract_feature_name(feature_text: str) -> str:
	"""Derive a short feature label from markdown or plain text."""
	title_match = re.search(
		r"^#\s+(?:Feature\s+\d+:\s+)?(.+?)(?:\s*\(|$)",
		feature_text,
		re.MULTILINE,
	)
	if title_match:
		return re.sub(r"\s+", " ", title_match.group(1).strip())[:80]

	first_line = feature_text.strip().split("\n", 1)[0].strip()
	if first_line:
		return re.sub(r"\s+", " ", first_line)[:80]
	return "the feature"


def _fallback_ears_requirements(feature_text: str) -> list[str]:
	"""Deterministic fallback when LLM generation is unavailable."""
	feature_name = _extract_feature_name(feature_text)
	return [
		f"WHEN a user requests {feature_name} THE SYSTEM SHALL provide the requested capability.",
		f"WHEN the primary {feature_name} flow completes successfully THE SYSTEM SHALL confirm success with actionable feedback.",
		f"WHEN an error occurs during {feature_name} THE SYSTEM SHALL surface a clear error message and recovery options.",
	]


def _build_generation_prompt(feature_text: str, existing_ears: list[Any]) -> str:
	existing_lines: list[str] = []
	for item in existing_ears:
		if isinstance(item, dict):
			existing_lines.append(item.get("text", ""))
		else:
			existing_lines.append(str(item))
	existing_block = "\n".join(f"- {line}" for line in existing_lines if line) or "(none)"

	return f"""Generate EARS requirements for the following feature description.

Use ONLY this exact grammar for each requirement:
WHEN <condition/event> THE SYSTEM SHALL <observable behavior>.

Rules:
- Output 3-6 requirements covering happy path, edge cases, and error handling
- Each requirement on its own line, no bullet prefix
- Always use English WHEN/THE SYSTEM SHALL form (even if the feature description is German)
- Do NOT duplicate these existing requirements:
{existing_block}

Feature description:
{feature_text[:8000]}

Respond with JSON: {{"requirements": ["WHEN ... THE SYSTEM SHALL ...", ...]}}
"""


async def generate_ears_requirements(
	feature_text: str,
	existing_ears: list[Any] | None = None,
) -> list[str]:
	"""
	Generate EARS requirement strings from feature text.

	Skips duplicates against existing_ears. Falls back to generic requirements
	when the LLM is unavailable.
	"""
	existing_ears = existing_ears or []
	existing_normalized = existing_ears_texts(existing_ears)

	try:
		from .credential_service import credential_service

		rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
		model_choice = rag_settings.get("MODEL_CHOICE", "gpt-4.1-nano")

		async with get_llm_client() as client:
			response = await client.chat.completions.create(
				model=model_choice,
				messages=[
					{
						"role": "system",
						"content": "You are a requirements engineer. Output valid JSON only.",
					},
					{"role": "user", "content": _build_generation_prompt(feature_text, existing_ears)},
				],
				response_format={"type": "json_object"},
			)

			if not response or not response.choices:
				raise ValueError("Empty LLM response")

			choice = response.choices[0]
			text, _, _ = extract_message_text(choice)
			if not text:
				raise ValueError("No content in LLM response")

			data = json.loads(text)
			raw_requirements = data.get("requirements", [])

			generated: list[str] = []
			for raw in raw_requirements:
				raw_line = str(raw).strip()
				if not raw_line.upper().startswith("WHEN"):
					continue

				parsed = parse_ears_line(raw_line)
				line = parsed["text"] if parsed else (raw_line if raw_line.endswith(".") else f"{raw_line}.")
				normalized = _normalize_for_dedup(line)
				if normalized in existing_normalized:
					continue

				generated.append(line)
				existing_normalized.add(normalized)

			if generated:
				return generated

	except Exception as exc:
		logger.warning("LLM EARS generation failed, using fallback: %s", exc, exc_info=True)

	return [
		line
		for line in _fallback_ears_requirements(feature_text)
		if _normalize_for_dedup(line) not in existing_normalized
	]


def merge_ears_into_feature_md(content: str, new_ears: list[str]) -> str:
	"""
	Merge EARS requirements into feature.md under ## Requirements (or ## EARS).

	Idempotent: identical WHEN/SHALL lines are not duplicated. Existing EARS
	lines elsewhere in the document are preserved.
	"""
	if not new_ears:
		return content

	content_normalized = existing_ears_texts_from_content(content)
	unique_new: list[str] = []
	for line in new_ears:
		line = line.strip()
		if not line:
			continue

		parsed = parse_ears_line(line)
		normalized_line = parsed["text"] if parsed else (line if line.endswith(".") else f"{line}.")
		normalized = _normalize_for_dedup(normalized_line)
		if normalized in content_normalized:
			continue

		unique_new.append(normalized_line)
		content_normalized.add(normalized)

	if not unique_new:
		return content

	bullet_lines = "\n".join(f"- {line}" for line in unique_new)
	section_match = _REQUIREMENTS_SECTION_PATTERN.search(content)

	if section_match:
		section_header_end = section_match.end()
		rest = content[section_header_end:]
		next_section = re.search(r"\n##\s+", rest)
		if next_section:
			insert_pos = section_header_end + next_section.start()
			before = content[:insert_pos].rstrip()
			after = content[insert_pos:]
			return f"{before}\n{bullet_lines}\n{after}"

		return f"{content.rstrip()}\n{bullet_lines}\n"

	section = f"\n\n## Requirements\n\n{bullet_lines}\n"
	return content.rstrip() + section


def existing_ears_texts_from_content(content: str) -> set[str]:
	"""Collect normalized EARS texts already present in markdown content."""
	texts: set[str] = set()
	for match in _EARS_LINE_PATTERN.finditer(content):
		line = normalize_ears_line(match.group(1), match.group(2))
		texts.add(_normalize_for_dedup(line))
	return texts


def resolve_feature_file(feature_dir: str | None, specs_dir: str = "specs") -> Path | None:
	"""Resolve feature.md path from spec-kit feature directory metadata."""
	if not feature_dir:
		return None

	path = Path(feature_dir)
	if path.is_absolute() and (path / "feature.md").exists():
		return path / "feature.md"

	candidate = Path(specs_dir) / Path(feature_dir).name / "feature.md"
	if candidate.exists():
		return candidate

	nested = Path(specs_dir) / feature_dir / "feature.md"
	if nested.exists():
		return nested

	return None


async def generate_and_merge_feature_ears(
	feature_file: Path,
	*,
	allow_when_existing: bool = False,
) -> tuple[list[str], str]:
	"""
	Generate EARS for a feature.md file and merge them into the content.

	By default, skips generation when EARS already exist (allow_when_existing=False).
	Returns (generated_lines, updated_content). Does not write to disk.
	"""
	from .spec_kit_parser import SpecKitParser

	content = feature_file.read_text()
	parser = SpecKitParser()
	existing_ears = parser.parse_ears_requirements(content)

	if existing_ears and not allow_when_existing:
		return [], content

	generated = await generate_ears_requirements(content, existing_ears)
	if not generated:
		return [], content

	updated = merge_ears_into_feature_md(content, generated)
	return generated, updated


def build_ears_document_body(ears_requirements: list[Any]) -> str:
	"""Format EARS requirements as markdown bullet list for document storage."""
	lines: list[str] = []
	for req in ears_requirements:
		if isinstance(req, dict):
			lines.append(
				f"WHEN {req['condition']} THE SYSTEM SHALL {req['behavior']}."
			)
		else:
			text = str(req).strip()
			if text:
				lines.append(text if text.endswith(".") else f"{text}.")
	return "\n".join(f"- {line}" for line in lines)
