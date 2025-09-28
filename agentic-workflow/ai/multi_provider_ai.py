"""
Multi-Provider AI System for VoidSpec Integration

This module implements a comprehensive AI system that supports multiple providers
(Grok, OpenAI, and others) with fallback capabilities and ZippyTrust integration.
"""

import asyncio
import json
import logging
import time
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class AIProvider:
    """Configuration for an AI provider."""
    name: str
    client: Any
    cost_per_token: float
    max_tokens: int
    supported_models: List[str]
    api_key_env_var: str
    base_url: Optional[str] = None


@dataclass
class GenerationResult:
    """Result from AI generation."""
    success: bool
    content: str
    provider: str
    model: str
    tokens_used: int
    cost: float
    generation_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderComparison:
    """Comparison of results from different providers."""
    prompt: str
    results: Dict[str, GenerationResult]
    winner: str
    comparison_metrics: Dict[str, Any]
    created_at: str


class AIProviderClient(ABC):
    """Abstract base class for AI provider clients."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate content using this provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available."""
        pass


class GrokClient(AIProviderClient):
    """Client for Grok AI (xAI)."""

    def __init__(self, api_key: str, model: str = "grok-1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.x.ai/v1"

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate content using Grok."""
        try:
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.3),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data["usage"]["total_tokens"]
                        cost = tokens_used * 0.0001  # Grok pricing (adjust as needed)
                        
                        generation_time = time.time() - start_time
                        
                        return GenerationResult(
                            success=True,
                            content=content,
                            provider="grok",
                            model=self.model,
                            tokens_used=tokens_used,
                            cost=cost,
                            generation_time=generation_time,
                            metadata={"temperature": kwargs.get("temperature", 0.3)}
                        )
                    else:
                        error_text = await response.text()
                        return GenerationResult(
                            success=False,
                            content="",
                            provider="grok",
                            model=self.model,
                            tokens_used=0,
                            cost=0.0,
                            generation_time=time.time() - start_time,
                            error=f"HTTP {response.status}: {error_text}"
                        )

        except Exception as e:
            return GenerationResult(
                success=False,
                content="",
                provider="grok",
                model=self.model,
                tokens_used=0,
                cost=0.0,
                generation_time=0.0,
                error=str(e)
            )

    def is_available(self) -> bool:
        """Check if Grok is available."""
        return bool(self.api_key)


class OpenAIClient(AIProviderClient):
    """Client for OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate content using OpenAI."""
        try:
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data["usage"]["total_tokens"]
                        
                        # Calculate cost based on model
                        if "gpt-4" in self.model:
                            cost = tokens_used * 0.00003  # GPT-4 pricing
                        else:
                            cost = tokens_used * 0.0000015  # GPT-3.5 pricing
                        
                        generation_time = time.time() - start_time
                        
                        return GenerationResult(
                            success=True,
                            content=content,
                            provider="openai",
                            model=self.model,
                            tokens_used=tokens_used,
                            cost=cost,
                            generation_time=generation_time,
                            metadata={"temperature": kwargs.get("temperature", 0.7)}
                        )
                    else:
                        error_text = await response.text()
                        return GenerationResult(
                            success=False,
                            content="",
                            provider="openai",
                            model=self.model,
                            tokens_used=0,
                            cost=0.0,
                            generation_time=time.time() - start_time,
                            error=f"HTTP {response.status}: {error_text}"
                        )

        except Exception as e:
            return GenerationResult(
                success=False,
                content="",
                provider="openai",
                model=self.model,
                tokens_used=0,
                cost=0.0,
                generation_time=0.0,
                error=str(e)
            )

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return bool(self.api_key)


class AnthropicClient(AIProviderClient):
    """Client for Anthropic Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate content using Anthropic Claude."""
        try:
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                        
                        # Claude pricing (adjust as needed)
                        cost = tokens_used * 0.000015
                        
                        generation_time = time.time() - start_time
                        
                        return GenerationResult(
                            success=True,
                            content=content,
                            provider="anthropic",
                            model=self.model,
                            tokens_used=tokens_used,
                            cost=cost,
                            generation_time=generation_time,
                            metadata={"temperature": kwargs.get("temperature", 0.7)}
                        )
                    else:
                        error_text = await response.text()
                        return GenerationResult(
                            success=False,
                            content="",
                            provider="anthropic",
                            model=self.model,
                            tokens_used=0,
                            cost=0.0,
                            generation_time=time.time() - start_time,
                            error=f"HTTP {response.status}: {error_text}"
                        )

        except Exception as e:
            return GenerationResult(
                success=False,
                content="",
                provider="anthropic",
                model=self.model,
                tokens_used=0,
                cost=0.0,
                generation_time=0.0,
                error=str(e)
            )

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return bool(self.api_key)


class ZippyAIClient(AIProviderClient):
    """Client for Zippy's custom AI models."""

    def __init__(self, api_key: str, model: str = "zippy-spec-v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.zippy.ai/v1"

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate content using Zippy AI."""
        try:
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", 0.5),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "trust_validation": True
                }
                
                async with session.post(
                    f"{self.base_url}/generate",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"]
                        tokens_used = data.get("tokens_used", len(prompt.split()) * 1.8)
                        cost = tokens_used * 0.00008  # Zippy AI pricing
                        
                        generation_time = time.time() - start_time
                        
                        return GenerationResult(
                            success=True,
                            content=content,
                            provider="zippy",
                            model=self.model,
                            tokens_used=tokens_used,
                            cost=cost,
                            generation_time=generation_time,
                            metadata={
                                "trust_score": data.get("trust_score", 0.9),
                                "validation_level": data.get("validation_level", "high")
                            }
                        )
                    else:
                        error_text = await response.text()
                        return GenerationResult(
                            success=False,
                            content="",
                            provider="zippy",
                            model=self.model,
                            tokens_used=0,
                            cost=0.0,
                            generation_time=time.time() - start_time,
                            error=f"HTTP {response.status}: {error_text}"
                        )

        except Exception as e:
            return GenerationResult(
                success=False,
                content="",
                provider="zippy",
                model=self.model,
                tokens_used=0,
                cost=0.0,
                generation_time=0.0,
                error=str(e)
            )

    def is_available(self) -> bool:
        """Check if Zippy AI is available."""
        return bool(self.api_key)


class MultiProviderAISystem:
    """
    Multi-provider AI system supporting Grok, OpenAI, and other providers
    with fallback capabilities and ZippyTrust integration.
    """

    def __init__(self):
        self.providers: Dict[str, AIProviderClient] = {}
        self.default_provider = "grok"
        self.fallback_order = ["grok", "openai", "anthropic", "zippy"]
        self.generation_history: List[GenerationResult] = []

    def register_provider(self, name: str, provider: AIProviderClient):
        """Register a new AI provider."""
        self.providers[name] = provider
        logger.info(f"Registered AI provider: {name}")

    def unregister_provider(self, name: str):
        """Unregister an AI provider."""
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Unregistered AI provider: {name}")

    def list_providers(self) -> List[str]:
        """List all registered providers."""
        return list(self.providers.keys())

    def get_available_providers(self) -> List[str]:
        """List providers that are currently available."""
        return [name for name, provider in self.providers.items() if provider.is_available()]

    async def generate_specs(self, prompt: str, provider: str = None,
                           version: str = 'v1', reviewer_pass: bool = True) -> Dict[str, Any]:
        """
        Generate specs using specified provider with fallback.

        Args:
            prompt: User's feature description
            provider: Preferred provider (optional)
            version: Prompt version (v1, v1b, enhanced)
            reviewer_pass: Whether to use reviewer pass

        Returns:
            Dictionary containing generated specs and metadata
        """
        provider_name = provider or self.default_provider
        provider_order = [provider_name] + [p for p in self.fallback_order if p != provider_name]

        for current_provider in provider_order:
            if current_provider not in self.providers:
                continue

            provider_client = self.providers[current_provider]
            if not provider_client.is_available():
                continue

            try:
                logger.info(f"Attempting generation with provider: {current_provider}")

                # Generate requirements
                requirements_result = await provider_client.generate(
                    self._build_requirements_prompt(prompt, version)
                )

                if not requirements_result.success:
                    continue

                # Generate design
                design_result = await provider_client.generate(
                    self._build_design_prompt(prompt, version)
                )

                if not design_result.success:
                    continue

                # Generate tasks
                tasks_result = await provider_client.generate(
                    self._build_tasks_prompt(prompt, version)
                )

                if not tasks_result.success:
                    continue

                # Store in history
                self.generation_history.extend([requirements_result, design_result, tasks_result])

                # Calculate total cost
                total_cost = requirements_result.cost + design_result.cost + tasks_result.cost
                total_tokens = requirements_result.tokens_used + design_result.tokens_used + tasks_result.tokens_used

                return {
                    'success': True,
                    'provider': current_provider,
                    'version': version,
                    'requirements': {
                        'content': requirements_result.content,
                        'tokens': requirements_result.tokens_used,
                        'cost': requirements_result.cost
                    },
                    'design': {
                        'content': design_result.content,
                        'tokens': design_result.tokens_used,
                        'cost': design_result.cost
                    },
                    'tasks': {
                        'content': tasks_result.content,
                        'tokens': tasks_result.tokens_used,
                        'cost': tasks_result.cost
                    },
                    'metadata': {
                        'total_cost': total_cost,
                        'total_tokens': total_tokens,
                        'generation_time': max(r.generation_time for r in [requirements_result, design_result, tasks_result]),
                        'created_at': datetime.now().isoformat()
                    }
                }

            except Exception as e:
                logger.warning(f"Generation failed with provider {current_provider}: {e}")
                continue

        return {
            'success': False,
            'error': f"All providers failed. Available providers: {self.get_available_providers()}",
            'provider': None,
            'version': version
        }

    async def compare_providers(self, prompt: str, providers: List[str] = None) -> Dict[str, Any]:
        """
        Compare results across different AI providers.

        Args:
            prompt: Prompt to test
            providers: List of providers to compare (optional)

        Returns:
            Comparison results and analysis
        """
        providers_to_test = providers or self.get_available_providers()
        results = {}

        for provider_name in providers_to_test:
            if provider_name not in self.providers:
                continue

            try:
                result = await self.generate_specs(prompt, provider_name)
                results[provider_name] = result
            except Exception as e:
                results[provider_name] = {
                    'success': False,
                    'error': str(e)
                }

        # Analyze comparison
        comparison = self._analyze_comparison(results, prompt)

        return {
            'prompt': prompt,
            'results': results,
            'comparison': comparison,
            'created_at': datetime.now().isoformat()
        }

    def _build_requirements_prompt(self, prompt: str, version: str) -> str:
        """Build requirements generation prompt."""
        base_prompt = f"""Generate requirements for the following feature using EARS notation:

Feature: {prompt}

Requirements should follow this format:
WHEN [condition]
THE SYSTEM SHALL [action]

Include acceptance criteria and dependencies."""

        if version == 'v1b':
            return base_prompt + "\n\nFocus on functional requirements and user acceptance criteria."
        elif version == 'enhanced':
            return base_prompt + "\n\nInclude non-functional requirements, performance criteria, and security considerations."

        return base_prompt

    def _build_design_prompt(self, prompt: str, version: str) -> str:
        """Build design generation prompt."""
        return f"""Generate technical design for the following feature:

Feature: {prompt}

Include:
- Technical Architecture
- Component Diagram
- Data Flow
- Security Considerations
- Performance Requirements"""

    def _build_tasks_prompt(self, prompt: str, version: str) -> str:
        """Build tasks generation prompt."""
        return f"""Generate implementation tasks for the following feature:

Feature: {prompt}

Format as numbered list with:
1. Task description
   - Outcome: Expected result
   - Dependencies: Prerequisites
   - Estimate: Time estimate"""

    def _analyze_comparison(self, results: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Analyze comparison results."""
        successful_results = {k: v for k, v in results.items() if v.get('success', False)}

        if not successful_results:
            return {
                'success': False,
                'error': 'No successful generations to compare'
            }

        # Simple winner determination based on cost-effectiveness
        winner = min(successful_results.keys(),
                    key=lambda x: successful_results[x]['metadata']['total_cost'])

        return {
            'success': True,
            'winner': winner,
            'total_providers_tested': len(results),
            'successful_providers': len(successful_results),
            'cost_comparison': {
                provider: result['metadata']['total_cost']
                for provider, result in successful_results.items()
            },
            'performance_comparison': {
                provider: result['metadata']['generation_time']
                for provider, result in successful_results.items()
            }
        }

    def get_generation_history(self, limit: int = 10) -> List[GenerationResult]:
        """Get recent generation history."""
        return self.generation_history[-limit:]

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        if not self.generation_history:
            return {'total_generations': 0, 'total_cost': 0, 'total_tokens': 0}

        total_cost = sum(result.cost for result in self.generation_history)
        total_tokens = sum(result.tokens_used for result in self.generation_history)

        provider_stats = {}
        for result in self.generation_history:
            if result.provider not in provider_stats:
                provider_stats[result.provider] = {'count': 0, 'cost': 0, 'tokens': 0}
            provider_stats[result.provider]['count'] += 1
            provider_stats[result.provider]['cost'] += result.cost
            provider_stats[result.provider]['tokens'] += result.tokens_used

        return {
            'total_generations': len(self.generation_history),
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'provider_stats': provider_stats
        }


# Factory functions for easy provider registration
def create_grok_provider(api_key: Optional[str] = None) -> GrokClient:
    """Create Grok provider with API key from environment if not provided."""
    api_key = api_key or os.getenv('XAI_API_KEY')
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable not set")
    return GrokClient(api_key)


def create_openai_provider(api_key: Optional[str] = None) -> OpenAIClient:
    """Create OpenAI provider with API key from environment if not provided."""
    api_key = api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAIClient(api_key)


def create_anthropic_provider(api_key: Optional[str] = None) -> AnthropicClient:
    """Create Anthropic provider with API key from environment if not provided."""
    api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return AnthropicClient(api_key)


def create_zippy_provider(api_key: Optional[str] = None) -> ZippyAIClient:
    """Create Zippy AI provider with API key from environment if not provided."""
    api_key = api_key or os.getenv('ZIPPY_API_KEY')
    if not api_key:
        raise ValueError("ZIPPY_API_KEY environment variable not set")
    return ZippyAIClient(api_key)


# Convenience function to create a fully configured system
def create_multi_provider_system() -> MultiProviderAISystem:
    """Create a multi-provider AI system with all available providers."""
    system = MultiProviderAISystem()

    # Try to register each provider if API keys are available
    try:
        system.register_provider('grok', create_grok_provider())
        logger.info("Registered Grok provider")
    except ValueError:
        logger.warning("Grok API key not available, skipping registration")

    try:
        system.register_provider('openai', create_openai_provider())
        logger.info("Registered OpenAI provider")
    except ValueError:
        logger.warning("OpenAI API key not available, skipping registration")

    try:
        system.register_provider('anthropic', create_anthropic_provider())
        logger.info("Registered Anthropic provider")
    except ValueError:
        logger.warning("Anthropic API key not available, skipping registration")

    try:
        system.register_provider('zippy', create_zippy_provider())
        logger.info("Registered Zippy AI provider")
    except ValueError:
        logger.warning("Zippy API key not available, skipping registration")

    return system

