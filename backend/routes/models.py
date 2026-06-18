import asyncio
import time
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import get_current_user
from ..db import get_active_user_llm_provider_key_ciphertext, get_user_llm_settings
from ..deps import _dpapi_unprotect_text, _sanitize_api_key, security
from ..llm_manager_simple import llm_manager

router = APIRouter()

OLLAMA_URL_DEFAULT = "http://localhost:11434"

# Cache para modelos Ollama — preenchido em background, nunca bloqueia o endpoint
_ollama_cache: List[Dict[str, str]] = []
_ollama_cache_ts: float = 0
_OLLAMA_CACHE_TTL = 30.0
_ollama_task: Optional[asyncio.Task] = None

PROVIDER_MODEL_LISTS: Dict[str, List[Dict[str, str]]] = {
    "gemini": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
        {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
    ],
    "groq": [
        {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B"},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B"},
        {"id": "llama3-8b-8192", "name": "Llama 3 8B"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
        {"id": "gemma2-9b-it", "name": "Gemma 2 9B"},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
    ],
    "openrouter": [
        {"id": "nvidia/nemotron-3-nano-30b-a3b:free", "name": "Nemotron 3 Nano (free)"},
        {"id": "qwen/qwen3-coder:free", "name": "Qwen3 Coder (free)"},
        {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Llama 3.2 3B (free)"},
        {"id": "google/gemma-3-12b-it:free", "name": "Gemma 3 12B (free)"},
    ],
}


def _user_has_provider_key(user_id: int, provider_id: str) -> bool:
    try:
        ct = get_active_user_llm_provider_key_ciphertext(user_id, provider_id)
        if ct:
            raw = _dpapi_unprotect_text(ct) or ""
            if raw.strip():
                return True
    except Exception:
        pass
    return False


def _provider_has_env_key(provider_id: str) -> bool:
    prov = llm_manager.providers.get(provider_id)
    if not prov:
        return False
    if provider_id == "ollama":
        url = str(prov.get("url") or "").strip()
        return bool(url)
    if "keys" in prov:
        keys = prov.get("keys", [])
        return bool([k for k in keys if _sanitize_api_key(k)])
    key = prov.get("key")
    return bool(_sanitize_api_key(key))


async def _fetch_ollama_models(base_url: str) -> List[Dict[str, str]]:
    url = f"{base_url}/api/tags"
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                payload = await resp.json()
    except Exception:
        return []
    models = payload.get("models") if isinstance(payload, dict) else []
    if not isinstance(models, list):
        return []
    result: List[Dict[str, str]] = []
    for m in models:
        name = str(m.get("name") or "").strip() if isinstance(m, dict) else ""
        if name:
            result.append({"id": name, "name": name})
    return result


async def _warm_ollama_cache_loop() -> None:
    """Background task: atualiza o cache do Ollama a cada TTL segundos."""
    global _ollama_cache, _ollama_cache_ts
    base_url = str(
        llm_manager.providers.get("ollama", {}).get("url") or OLLAMA_URL_DEFAULT
    )
    models = await _fetch_ollama_models(base_url)
    _ollama_cache = models
    _ollama_cache_ts = time.time()


def _start_ollama_background_task() -> None:
    global _ollama_task
    if _ollama_task is None or _ollama_task.done():
        _ollama_task = asyncio.create_task(_warm_ollama_cache_loop())


@router.get("/api/models/available")
async def get_available_models(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = int(current_user["id"])

    stored = get_user_llm_settings(user_id)
    settings = (stored or {}).get("settings") or {}
    current_provider = str(settings.get("provider") or "").strip().lower() or None
    current_model = (settings.get("model") or "").strip() or None

    providers: List[Dict[str, Any]] = []

    all_providers = ["gemini", "groq", "openai", "openrouter", "ollama"]

    for pid in all_providers:
        has_env = _provider_has_env_key(pid)
        has_user = _user_has_provider_key(user_id, pid)
        available = has_env or has_user

        if pid == "ollama":
            base_url = str(
                llm_manager.providers.get("ollama", {}).get("url") or OLLAMA_URL_DEFAULT
            )
            if not available:
                available = bool(base_url)
            if available and not _ollama_cache_ts:
                _start_ollama_background_task()
            models = list(_ollama_cache) if available else []
        else:
            models = PROVIDER_MODEL_LISTS.get(pid, [])

        name_map = {
            "gemini": "Gemini",
            "groq": "Groq",
            "openai": "OpenAI",
            "openrouter": "OpenRouter",
            "ollama": "Ollama (Local)",
        }

        providers.append({
            "id": pid,
            "name": name_map.get(pid, pid),
            "available": available,
            "models": models,
        })

    active = await llm_manager.get_active_provider(current_provider)

    return {
        "current": {
            "provider": active.get("provider") or current_provider or "gemini",
            "model": current_model or active.get("model") or "gemini-2.5-flash",
        },
        "providers": providers,
    }
