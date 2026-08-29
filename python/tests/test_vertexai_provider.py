"""
Tests for Vertex AI provider helpers and integration hooks.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.vertex_ai_service import (
	build_vertex_ai_openai_base_url,
	check_vertex_ai_connection,
	validate_gcp_project_id,
	validate_gcp_region,
)


def test_build_vertex_ai_openai_base_url():
	url = build_vertex_ai_openai_base_url("my-gcp-project", "us-central1")
	assert url == (
		"https://us-central1-aiplatform.googleapis.com/v1/projects/my-gcp-project"
		"/locations/us-central1/endpoints/openapi"
	)


def test_validate_gcp_project_id_rejects_invalid_values():
	with pytest.raises(ValueError):
		validate_gcp_project_id("Bad Project!")


def test_validate_gcp_region_rejects_invalid_values():
	with pytest.raises(ValueError):
		validate_gcp_region("not-a-region")


@pytest.mark.asyncio
async def test_vertex_ai_connection_requires_project_id():
	with patch(
		"src.server.services.vertex_ai_service.get_gcp_project_id",
		new_callable=AsyncMock,
		return_value=None,
	):
		result = await check_vertex_ai_connection()

	assert result == {"ok": False, "reason": "no_project_id"}


@pytest.mark.asyncio
async def test_vertex_ai_connection_success():
	mock_response = MagicMock()
	mock_response.status_code = 200

	mock_client = MagicMock()
	mock_client.get = AsyncMock(return_value=mock_response)
	mock_client.__aenter__ = AsyncMock(return_value=mock_client)
	mock_client.__aexit__ = AsyncMock(return_value=None)

	with (
		patch(
			"src.server.services.vertex_ai_service.get_gcp_project_id",
			new_callable=AsyncMock,
			return_value="my-gcp-project",
		),
		patch(
			"src.server.services.vertex_ai_service.get_gcp_region",
			new_callable=AsyncMock,
			return_value="us-central1",
		),
		patch(
			"src.server.services.vertex_ai_service.get_vertex_ai_access_token",
			new_callable=AsyncMock,
			return_value="test-token",
		),
		patch("src.server.services.vertex_ai_service.httpx.AsyncClient", return_value=mock_client),
	):
		result = await check_vertex_ai_connection()

	assert result["ok"] is True
	assert result["reason"] == "connected"
	assert result["provider"] == "vertexai"


@pytest.mark.asyncio
async def test_vertex_ai_llm_client_creation():
	mock_client_ctor = MagicMock(return_value=MagicMock())

	with (
		patch(
			"src.server.services.vertex_ai_service.get_gcp_project_id",
			new_callable=AsyncMock,
			return_value="my-gcp-project",
		),
		patch(
			"src.server.services.vertex_ai_service.get_gcp_region",
			new_callable=AsyncMock,
			return_value="us-central1",
		),
		patch(
			"src.server.services.vertex_ai_service.get_vertex_ai_access_token",
			new_callable=AsyncMock,
			return_value="test-token",
		),
		patch("src.server.services.llm_provider_service.openai.AsyncOpenAI", mock_client_ctor),
		patch(
			"src.server.services.llm_provider_service.credential_service._get_provider_api_key",
			new_callable=AsyncMock,
			return_value=None,
		),
	):
		from src.server.services.llm_provider_service import get_llm_client

		async with get_llm_client(provider="vertexai") as client:
			assert client is mock_client_ctor.return_value

	mock_client_ctor.assert_called_once()
	call_kwargs = mock_client_ctor.call_args.kwargs
	assert call_kwargs["api_key"] == "test-token"
	assert call_kwargs["base_url"].endswith("/endpoints/openapi")
