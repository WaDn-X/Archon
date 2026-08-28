"""
Vertex AI helpers for OpenAI-compatible client configuration.

Uses Application Default Credentials (ADC) for authentication against
Google Cloud Vertex AI's OpenAI-compatible endpoint.
"""

import os
import re
from typing import Any

import httpx

from ..config.logfire_config import get_logger
from .credential_service import credential_service

logger = get_logger(__name__)

GCP_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
DEFAULT_GCP_REGION = "us-central1"
GCP_PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
GCP_REGION_PATTERN = re.compile(r"^[a-z]+(?:-[a-z]+)?[0-9]$")


async def get_gcp_project_id() -> str | None:
	"""Resolve GCP project ID from credentials store or environment."""
	project_id = await credential_service.get_credential("GCP_PROJECT_ID")
	if project_id and isinstance(project_id, str) and project_id.strip():
		return project_id.strip()
	env_project_id = os.getenv("GCP_PROJECT_ID", "").strip()
	return env_project_id or None


async def get_gcp_region() -> str:
	"""Resolve GCP region from credentials store or environment."""
	region = await credential_service.get_credential("GCP_REGION")
	if region and isinstance(region, str) and region.strip():
		return region.strip()
	return os.getenv("GCP_REGION", DEFAULT_GCP_REGION).strip() or DEFAULT_GCP_REGION


def validate_gcp_project_id(project_id: str) -> bool:
	if not project_id or not GCP_PROJECT_ID_PATTERN.match(project_id):
		raise ValueError(
			"GCP_PROJECT_ID must be a valid Google Cloud project ID "
			"(6-30 lowercase letters, digits, or hyphens)"
		)
	return True


def validate_gcp_region(region: str) -> bool:
	if not region or not GCP_REGION_PATTERN.match(region):
		raise ValueError(
			f"GCP_REGION must be a valid Google Cloud region (e.g. {DEFAULT_GCP_REGION})"
		)
	return True


def build_vertex_ai_openai_base_url(project_id: str, region: str) -> str:
	validate_gcp_project_id(project_id)
	validate_gcp_region(region)
	return (
		f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}"
		f"/locations/{region}/endpoints/openapi"
	)


async def get_vertex_ai_access_token() -> str:
	"""Fetch a short-lived OAuth token using Application Default Credentials."""
	try:
		import google.auth
		import google.auth.transport.requests
	except ImportError as exc:
		raise RuntimeError(
			"google-auth is required for Vertex AI. Install server dependencies with uv sync --group server."
		) from exc

	credentials, _ = google.auth.default(scopes=[GCP_CLOUD_PLATFORM_SCOPE])
	request = google.auth.transport.requests.Request()
	credentials.refresh(request)

	token = credentials.token
	if not token or not isinstance(token, str):
		raise RuntimeError("Failed to obtain Vertex AI access token from Application Default Credentials")

	return token


async def check_vertex_ai_connection() -> dict[str, Any]:
	"""
	Validate Vertex AI connectivity using ADC and a lightweight models list call.

	Returns a result dict compatible with provider status responses.
	"""
	project_id = await get_gcp_project_id()
	if not project_id:
		return {"ok": False, "reason": "no_project_id"}

	region = await get_gcp_region()
	try:
		validate_gcp_project_id(project_id)
		validate_gcp_region(region)
		token = await get_vertex_ai_access_token()
		base_url = build_vertex_ai_openai_base_url(project_id, region)

		async with httpx.AsyncClient(timeout=15.0) as client:
			response = await client.get(
				f"{base_url}/models",
				headers={"Authorization": f"Bearer {token}"},
			)

		if response.status_code == 200:
			return {"ok": True, "reason": "connected", "provider": "vertexai"}

		logger.warning(
			"Vertex AI connectivity test failed with HTTP %s for project %s in %s",
			response.status_code,
			project_id,
			region,
		)
		return {"ok": False, "reason": "connection_failed", "provider": "vertexai"}

	except Exception as exc:
		logger.warning("Vertex AI connectivity test failed: %s", exc)
		return {"ok": False, "reason": "connection_failed", "provider": "vertexai"}
