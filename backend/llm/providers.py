#!/usr/bin/env python3
"""
LLM Providers Configuration
Configuração de provedores LLM para OpenSlap
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """Tipos de provedores LLM"""
    LOCAL = "local"
    REMOTE = "remote"
    HYBRID = "hybrid"


@dataclass
class LLMProvider:
    """Configuração de provedor LLM"""
    id: str
    name: str
    type: ProviderType
    base_url: str
    api_key_env: str
    models: List[str]
    context_length: int
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7
    custom_headers: Optional[Dict[str, str]] = None
    

# Configuração de provedores
PROVIDERS: Dict[str, LLMProvider] = {
    # Ollama - Local
    "ollama": LLMProvider(
        id="ollama",
        name="Ollama",
        type=ProviderType.LOCAL,
        base_url="http://localhost:11434",
        api_key_env="",
        models=[
            "llama3.2",
            "llama3.1",
            "codellama",
            "mistral",
            "qwen2.5",
        ],
        context_length=128000,
        supports_tools=True,
        supports_streaming=True,
    ),
    
    # OpenAI
    "openai": LLMProvider(
        id="openai",
        name="OpenAI",
        type=ProviderType.REMOTE,
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        models=[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        context_length=128000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
    ),
    
    # Anthropic
    "anthropic": LLMProvider(
        id="anthropic",
        name="Anthropic",
        type=ProviderType.REMOTE,
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        models=[
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        context_length=200000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
    ),
    
    # Google AI Studio / Gemini
    "google": LLMProvider(
        id="google",
        name="Google AI Studio",
        type=ProviderType.REMOTE,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GOOGLE_API_KEY",
        models=[
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        context_length=1000000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
    ),
    
    # OpenRouter - Multi-provider gateway
    "openrouter": LLMProvider(
        id="openrouter",
        name="OpenRouter",
        type=ProviderType.REMOTE,
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        models=[
            "qwen/qwen3-coder:free",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-pro",
            "meta-llama/llama-3.2-70b",
        ],
        context_length=256000,
        supports_tools=True,
        supports_streaming=True,
        custom_headers={
            "HTTP-Referer": "https://openslap.ai",
            "X-Title": "OpenSlap",
        },
    ),
    
    # Qwen3 Coder via OpenRouter (Free Tier)
    "qwen3-coder": LLMProvider(
        id="qwen3-coder",
        name="Qwen3 Coder (OpenRouter Free)",
        type=ProviderType.REMOTE,
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        models=[
            "qwen/qwen3-coder:free",
        ],
        context_length=256000,
        supports_tools=True,
        supports_streaming=True,
        max_tokens=8192,
        custom_headers={
            "HTTP-Referer": "https://openslap.ai",
            "X-Title": "OpenSlap",
        },
    ),
    
    # Together AI
    "together": LLMProvider(
        id="together",
        name="Together AI",
        type=ProviderType.REMOTE,
        base_url="https://api.together.xyz/v1",
        api_key_env="TOGETHER_API_KEY",
        models=[
            "meta-llama/Llama-3.2-70B",
            "Qwen/Qwen3-Coder-32B",
        ],
        context_length=128000,
        supports_tools=True,
        supports_streaming=True,
    ),
    
    # Groq
    "groq": LLMProvider(
        id="groq",
        name="Groq",
        type=ProviderType.REMOTE,
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        models=[
            "qwen/qwen3-32b",
            "llama-3.2-70b-versatile",
            "mixtral-8x7b-32768",
        ],
        context_length=128000,
        supports_tools=True,
        supports_streaming=True,
    ),
}


def get_provider(provider_id: str) -> Optional[LLMProvider]:
    """Retorna configuração de provedor pelo ID"""
    return PROVIDERS.get(provider_id)


def get_available_providers() -> List[Dict[str, Any]]:
    """Retorna lista de provedores disponíveis para API"""
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type.value,
            "models": p.models,
            "context_length": p.context_length,
            "supports_tools": p.supports_tools,
            "supports_vision": p.supports_vision,
            "supports_streaming": p.supports_streaming,
        }
        for p in PROVIDERS.values()
    ]


def get_provider_for_model(model_id: str) -> Optional[str]:
    """Retorna ID do provedor que suporta o modelo especificado"""
    for provider_id, provider in PROVIDERS.items():
        if model_id in provider.models:
            return provider_id
    return None
