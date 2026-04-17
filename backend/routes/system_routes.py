"""
Rotas de sistema — system_profile, system_map, doctor.
Extraídas de main_auth.py.
"""
import sys
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..deps import (
    security,
    _get_effective_security_settings,
    _sanitize_api_key,
    _system_map_cache,
)
from ..db import (
    upsert_user_system_profile,
    get_user_system_profile,
    get_user_llm_settings,
)
from ..main_auth import get_current_user
from ..utils.system import generate_system_map_ascii as _generate_system_map_ascii

# Importar main_auth como módulo para acessar variáveis globais (lazy import)
_main = None

def _get_main():
    global _main
    if _main is None:
        import src.backend.main_auth as _main_module
        _main = _main_module
    return _main

system_router = APIRouter(prefix="/api", tags=["system"])


def _sanitize_base_url(url: str) -> str:
    """Sanitiza URL base da API."""
    u = str(url or "").strip()
    if not u:
        return ""
    # Remover trailing slash
    return u.rstrip("/")


async def _test_api_provider(
    session: aiohttp.ClientSession,
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Testa conectividade com um provedor LLM."""
    result = {
        "provider": provider,
        "ok": False,
        "latency_ms": None,
        "error": None,
    }
    try:
        start = asyncio.get_event_loop().time()
        # Implementação simplificada - teste dummy
        if provider == "openai":
            headers = {"Authorization": f"Bearer {api_key}"}
            url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/models"
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                _ = await resp.text()
                result["ok"] = resp.status == 200
        elif provider == "anthropic":
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
            url = (base_url or "https://api.anthropic.com").rstrip("/") + "/v1/models"
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                _ = await resp.text()
                result["ok"] = resp.status == 200
        else:
            # Provedor genérico - apenas verificar se temos config
            result["ok"] = bool(api_key)
        result["latency_ms"] = round((asyncio.get_event_loop().time() - start) * 1000, 2)
    except Exception as e:
        result["error"] = str(e)
    return result


@system_router.get("/system_profile/installed_software")
async def get_installed_sw(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna software instalado no sistema."""
    # Lazy imports para evitar import circular
    from ..main_auth import get_installed_software, _top20_productivity
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    items = get_installed_software(max_age_s=21600)
    top20 = _top20_productivity(items)
    return {
        "items": items,
        "top20_productivity": top20,
        "count": len(items),
    }


@system_router.post("/system_profile/refresh_inventory")
async def refresh_inventory(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Força atualização do inventário de software."""
    # Lazy imports para evitar import circular
    from ..main_auth import get_installed_software, _top20_productivity
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    # Force refresh by invalidating cache and re-scan
    _main = _get_main()
    _main._installed_cache_ts = None
    items = get_installed_software(max_age_s=0)
    top20 = _top20_productivity(items)
    try:
        from ..db import upsert_system_kv_cache
        upsert_system_kv_cache(
            "installed_sw_snapshot",
            {
                "items": items,
                "removed": _main._installed_removed if _main else [],
                "top20": top20,
            },
        )
    except Exception:
        pass
    return {"ok": True, "count": len(items), "top20_count": len(top20)}


@system_router.get("/system_map")
async def get_system_map(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna mapa ASCII do sistema."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    import time
    cache = _system_map_cache
    if cache.get("ascii") and cache.get("generated_at"):
        return {
            "ascii": cache["ascii"],
            "generated_at": cache["generated_at"],
            "cached": True,
        }
    ascii_map = _generate_system_map_ascii()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _system_map_cache["ascii"] = ascii_map
    _system_map_cache["generated_at"] = now
    return {"ascii": ascii_map, "generated_at": now, "cached": False}


@system_router.post("/system_map/refresh")
async def refresh_system_map(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Força regeneração do mapa do sistema."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    import time
    ascii_map = _generate_system_map_ascii()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _system_map_cache["ascii"] = ascii_map
    _system_map_cache["generated_at"] = now
    return {"ascii": ascii_map, "generated_at": now, "cached": False}


@system_router.get("/doctor")
async def doctor_check(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Diagnóstico completo do sistema."""
    # Lazy imports para evitar import circular
    from ..main_auth import (
        _build_system_profile,
        _format_system_profile_summary,
        _safe_llm_settings,
        _get_user_api_key,
        _get_env_api_key_for_provider,
    )
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user_id = int(current_user["id"])

    # Coletar informações do sistema
    profile = _build_system_profile(user_id)
    summary = _format_system_profile_summary(profile)

    # Verificar configurações LLM
    llm_cfg = get_user_llm_settings(user_id)
    safe_settings = _safe_llm_settings(llm_cfg or {})

    # Testar conectividade com provedores
    connectivity_results = []
    async with aiohttp.ClientSession() as session:
        # Testar provedor ativo
        provider = safe_settings.get("provider", "openai")
        api_key = _get_user_api_key(user_id, provider) or _get_env_api_key_for_provider(provider)
        if api_key:
            result = await _test_api_provider(session, provider, api_key)
            connectivity_results.append(result)

    # Compilar relatório
    report = {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "system_profile_summary": summary,
        "llm_settings": {
            "provider": safe_settings.get("provider"),
            "model": safe_settings.get("model"),
        },
        "connectivity": connectivity_results,
        "checks": {
            "system_profile": bool(profile),
            "llm_configured": bool(api_key),
            "api_reachable": any(r["ok"] for r in connectivity_results),
        },
    }
    return report
