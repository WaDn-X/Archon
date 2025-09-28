"""
AI Module for VoidSpec Integration

This module provides multi-provider AI capabilities for the VoidSpec integration,
supporting Grok, OpenAI, and Zippy AI with fallback and comparison features.
"""

from .multi_provider_ai import (
    MultiProviderAISystem,
    AIProviderClient,
    GrokClient,
    OpenAIClient,
    ZippyAIClient,
    GenerationResult,
    ProviderComparison,
    create_multi_provider_system,
    create_grok_provider,
    create_openai_provider,
    create_zippy_provider
)

__all__ = [
    'MultiProviderAISystem',
    'AIProviderClient',
    'GrokClient',
    'OpenAIClient',
    'ZippyAIClient',
    'GenerationResult',
    'ProviderComparison',
    'create_multi_provider_system',
    'create_grok_provider',
    'create_openai_provider',
    'create_zippy_provider'
]

