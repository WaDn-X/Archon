"""
Provider status API endpoints for testing connectivity

Handles server-side provider connectivity testing without exposing API keys to frontend.
"""

import httpx
from fastapi import APIRouter, HTTPException, Path

from ..config.logfire_config import logfire
from ..services.credential_service import credential_service
from ..services.vertex_ai_service import check_vertex_ai_connection

router = APIRouter(prefix="/api/providers", tags=["providers"])


async def test_openai_connection(api_key: str) -> bool:
    """Test OpenAI API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.status_code == 200
    except Exception as e:
        logfire.warning(f"OpenAI connectivity test failed: {e}")
        return False


async def test_google_connection(api_key: str) -> bool:
    """Test Google AI API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1/models",
                headers={"x-goog-api-key": api_key}
            )
            return response.status_code == 200
    except Exception:
        logfire.warning("Google AI connectivity test failed")
        return False


async def test_anthropic_connection(api_key: str) -> bool:
    """Test Anthropic API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            return response.status_code == 200
    except Exception as e:
        logfire.warning(f"Anthropic connectivity test failed: {e}")
        return False


async def test_openrouter_connection(api_key: str) -> bool:
    """Test OpenRouter API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.status_code == 200
    except Exception as e:
        logfire.warning(f"OpenRouter connectivity test failed: {e}")
        return False


async def test_grok_connection(api_key: str) -> bool:
    """Test Grok API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.status_code == 200
    except Exception as e:
        logfire.warning(f"Grok connectivity test failed: {e}")
        return False


PROVIDER_TESTERS = {
    "openai": test_openai_connection,
    "google": test_google_connection,
    "anthropic": test_anthropic_connection,
    "openrouter": test_openrouter_connection,
    "grok": test_grok_connection,
}

ALLOWED_PROVIDERS = frozenset({"openai", "ollama", "google", "openrouter", "anthropic", "grok", "vertexai"})


@router.get("/{provider}/status")
async def get_provider_status(
    provider: str = Path(
        ...,
        description="Provider name to test connectivity for",
        regex="^[a-z0-9_]+$",
        max_length=20
    )
):
    """Test provider connectivity using server-side API key (secure)"""
    try:
        if provider not in ALLOWED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider '{provider}'. Allowed providers: {sorted(ALLOWED_PROVIDERS)}"
            )

        safe_provider = provider[:20]
        logfire.info(f"Testing {safe_provider} connectivity server-side")

        if provider == "vertexai":
            result = await check_vertex_ai_connection()
            logfire.info(f"{safe_provider} connectivity test result: {result.get('ok')}")
            return result

        if provider not in PROVIDER_TESTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Provider '{provider}' not supported for connectivity testing"
            )

        # Get API key server-side (never expose to client)
        key_name = f"{provider.upper()}_API_KEY"
        api_key = await credential_service.get_credential(key_name, decrypt=True)

        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            logfire.info(f"No API key configured for {safe_provider}")
            return {"ok": False, "reason": "no_key"}

        tester = PROVIDER_TESTERS[provider]
        is_connected = await tester(api_key)

        logfire.info(f"{safe_provider} connectivity test result: {is_connected}")
        return {
            "ok": is_connected,
            "reason": "connected" if is_connected else "connection_failed",
            "provider": provider
        }

    except HTTPException:
        raise
    except Exception as e:
        safe_error = str(e)[:100]
        logfire.error(f"Error testing {provider[:20]} connectivity: {safe_error}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error during connectivity test"})
