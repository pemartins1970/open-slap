import os
from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..auth import get_current_user
from ..deps import (
    SECURITY_SETTINGS_DEFAULT,
    _dpapi_protect_text,
    _get_effective_security_settings,
    _get_env_api_key_for_provider,
    _infer_env_provider,
    _sanitize_api_key,
    security,
)
from ..db import (
    add_user_llm_provider_key_ciphertext,
    delete_user_auth_settings,
    delete_user_api_key,
    delete_user_llm_provider_key,
    get_active_user_llm_provider_key_ciphertext,
    get_user_api_key_ciphertext,
    get_user_auth_settings,
    get_user_llm_settings,
    get_user_system_profile,
    list_user_llm_provider_keys,
    set_active_user_llm_provider_key,
    upsert_user_api_key_ciphertext,
    upsert_user_auth_settings,
    upsert_user_llm_settings,
    upsert_user_security_settings,
    update_user_system_profile_data,
)

router = APIRouter()


class LlmSettingsInput(BaseModel):
    mode: str
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class LlmProviderKeyCreateInput(BaseModel):
    provider: str
    api_key: str


class LlmProviderKeySelectInput(BaseModel):
    key_id: int


class LanguageSettingsInput(BaseModel):
    lang: str


class SecuritySettingsInput(BaseModel):
    sandbox: Optional[bool] = None
    allow_os_commands: Optional[bool] = None
    allow_file_write: Optional[bool] = None
    allow_web_retrieval: Optional[bool] = None
    allow_connectors: Optional[bool] = None
    allow_system_profile: Optional[bool] = None


class AuthSettingsInput(BaseModel):
    jwt_expire_minutes: Optional[int] = None
    use_default: Optional[bool] = False


def _safe_llm_settings(inp: Dict[str, Any]) -> Dict[str, Any]:
    raw_provider = (inp or {}).get("provider")
    provider = (str(raw_provider).strip().lower() if raw_provider is not None else None) or None
    base_url = (inp or {}).get("base_url")
    if isinstance(base_url, str):
        base_url = base_url.strip().strip("`\"' ,").rstrip("/")

    if provider == "gemini":
        bu = str(base_url or "").strip()
        if not bu:
            bu = "https://generativelanguage.googleapis.com/v1"
        if bu.endswith("/v1beta") and "generativelanguage.googleapis.com" in bu:
            bu = bu[:-6] + "v1"
        base_url = bu
    elif provider == "groq":
        base_url = str(base_url or "https://api.groq.com/openai/v1").strip()
    elif provider == "openai":
        base_url = str(base_url or "https://api.openai.com/v1").strip()
    elif provider == "openrouter":
        base_url = str(base_url or "https://openrouter.ai/api/v1").strip()
    elif provider == "ollama":
        base_url = str(base_url or "http://localhost:11434").strip()
    return {
        "mode": str((inp or {}).get("mode") or "env"),
        "provider": provider,
        "model": (inp or {}).get("model"),
        "base_url": base_url,
    }


def _safe_security_settings(inp: Dict[str, Any]) -> Dict[str, Any]:
    raw = inp or {}
    out = dict(SECURITY_SETTINGS_DEFAULT)
    for k in SECURITY_SETTINGS_DEFAULT.keys():
        v = raw.get(k, None)
        if v is None:
            continue
        out[k] = bool(v)
    if out.get("sandbox"):
        out["allow_os_commands"] = False
        out["allow_file_write"] = False
        out["allow_web_retrieval"] = False
        out["allow_connectors"] = False
        out["allow_system_profile"] = False
    return out


def _default_jwt_expire_minutes() -> int:
    raw = (os.getenv("OPENSLAP_JWT_EXPIRE_MINUTES") or "").strip()
    try:
        v = int(raw or "120")
    except Exception:
        v = 120
    return max(15, min(v, 10080))


def _safe_auth_settings(inp: Dict[str, Any]) -> Dict[str, Any]:
    raw = inp or {}
    out: Dict[str, Any] = {}
    v = raw.get("jwt_expire_minutes", None)
    if v is not None:
        try:
            iv = int(v)
        except Exception:
            iv = None
        if iv is not None:
            out["jwt_expire_minutes"] = max(15, min(iv, 10080))
    return out


@router.get("/api/settings/llm")
async def get_llm_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    stored = get_user_llm_settings(current_user["id"])
    raw_settings = (stored or {}).get("settings") or {}
    settings = _safe_llm_settings(raw_settings)
    llm_mode = str(settings.get("mode") or "env").strip().lower()
    provider = str(settings.get("provider") or "").strip().lower()
    effective_provider = provider or None
    if llm_mode == "api" and not effective_provider:
        effective_provider = "openai"
    has_stored_key = bool(get_user_api_key_ciphertext(current_user["id"]))
    has_provider_key = bool(
        effective_provider
        and get_active_user_llm_provider_key_ciphertext(current_user["id"], effective_provider)
    )
    provider_key_count = (
        len(list_user_llm_provider_keys(current_user["id"], provider=effective_provider))
        if effective_provider
        else 0
    )
    env_provider = _infer_env_provider()
    has_env_key = bool(_get_env_api_key_for_provider(effective_provider or env_provider))
    has_key = bool(has_stored_key or has_provider_key or has_env_key)
    key_source = "stored" if (has_stored_key or has_provider_key) else ("env" if has_env_key else "none")
    if not raw_settings or not provider:
        if env_provider:
            settings = _safe_llm_settings(
                {
                    "mode": "api",
                    "provider": env_provider,
                    "model": raw_settings.get("model"),
                    "base_url": raw_settings.get("base_url"),
                }
            )
    return {
        "settings": settings,
        "has_api_key": has_key,
        "api_key_source": key_source,
        "has_stored_api_key": bool(has_stored_key or has_provider_key),
        "has_env_api_key": bool(has_env_key),
        "provider_key_count": int(provider_key_count),
        "provider_has_active_key": bool(has_provider_key),
        "updated_at": (stored or {}).get("updated_at"),
    }


@router.put("/api/settings/llm")
async def put_llm_settings_endpoint(
    payload: LlmSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    settings = _safe_llm_settings(payload.model_dump())
    upsert_user_llm_settings(current_user["id"], settings)
    if payload.api_key and payload.api_key.strip():
        cleaned = _sanitize_api_key(payload.api_key)
        ciphertext = _dpapi_protect_text(cleaned)
        upsert_user_api_key_ciphertext(current_user["id"], ciphertext)
    llm_mode = str(settings.get("mode") or "env").strip().lower()
    provider = str(settings.get("provider") or "").strip().lower()
    effective_provider = provider or None
    if llm_mode == "api" and not effective_provider:
        effective_provider = "openai"
    has_stored_key = bool(get_user_api_key_ciphertext(current_user["id"]))
    has_provider_key = bool(
        effective_provider
        and get_active_user_llm_provider_key_ciphertext(current_user["id"], effective_provider)
    )
    env_provider = _infer_env_provider()
    has_env_key = bool(_get_env_api_key_for_provider(effective_provider or env_provider))
    has_key = bool(has_stored_key or has_provider_key or has_env_key)
    return {"settings": settings, "has_api_key": bool(has_key)}


@router.delete("/api/settings/llm/api_key")
async def delete_llm_api_key_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    deleted = delete_user_api_key(current_user["id"])
    stored = get_user_llm_settings(current_user["id"])
    settings = _safe_llm_settings((stored or {}).get("settings") or {})
    llm_mode = str(settings.get("mode") or "env").strip().lower()
    provider = str(settings.get("provider") or "").strip().lower()
    effective_provider = provider or None
    if llm_mode == "api" and not effective_provider:
        effective_provider = "openai"
    has_stored_key = bool(get_user_api_key_ciphertext(current_user["id"]))
    has_provider_key = bool(
        effective_provider
        and get_active_user_llm_provider_key_ciphertext(current_user["id"], effective_provider)
    )
    has_env_key = bool(_get_env_api_key_for_provider(effective_provider))
    has_key = bool(has_stored_key or has_provider_key or has_env_key)
    key_source = "stored" if (has_stored_key or has_provider_key) else ("env" if has_env_key else "none")
    return {
        "deleted": bool(deleted),
        "has_api_key": has_key,
        "api_key_source": key_source,
        "has_stored_api_key": bool(has_stored_key or has_provider_key),
        "has_env_api_key": bool(has_env_key),
    }


@router.get("/api/settings/llm/keys")
async def list_llm_provider_keys_endpoint(
    provider: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    keys = list_user_llm_provider_keys(current_user["id"], provider=provider)
    return {"keys": keys}


@router.post("/api/settings/llm/keys")
async def add_llm_provider_key_endpoint(
    payload: LlmProviderKeyCreateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    prov = str(payload.provider or "").strip().lower()
    cleaned = _sanitize_api_key(payload.api_key or "")
    if not cleaned:
        raise HTTPException(status_code=400, detail="Provider e chave são obrigatórios.")
    if not prov:
        if cleaned.startswith("AIza"):
            prov = "gemini"
        elif cleaned.startswith("gsk_"):
            prov = "groq"
        elif cleaned.startswith("sk-or-"):
            prov = "openrouter"
        elif cleaned.startswith("sk-ant-"):
            prov = "anthropic"
        elif cleaned.startswith("sk-"):
            prov = "openai"
        else:
            prov = "openai"
    ciphertext = _dpapi_protect_text(cleaned)
    key_id = add_user_llm_provider_key_ciphertext(current_user["id"], prov, ciphertext, set_active=True)
    return {"ok": True, "id": int(key_id)}


@router.post("/api/settings/llm/keys/{provider}/active")
async def set_active_llm_provider_key_endpoint(
    provider: str,
    payload: LlmProviderKeySelectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    prov = str(provider or "").strip().lower()
    ok = set_active_user_llm_provider_key(current_user["id"], prov, int(payload.key_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Chave não encontrada.")
    return {"ok": True}


@router.delete("/api/settings/llm/keys/{provider}/{key_id}")
async def delete_llm_provider_key_endpoint(
    provider: str,
    key_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    prov = str(provider or "").strip().lower()
    ok = delete_user_llm_provider_key(current_user["id"], prov, int(key_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Chave não encontrada.")
    return {"ok": True}


@router.get("/api/settings/security")
async def get_security_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    effective = _get_effective_security_settings(int(current_user["id"]))
    settings = {k: effective.get(k) for k in SECURITY_SETTINGS_DEFAULT.keys()}
    return {"settings": settings, "updated_at": effective.get("updated_at")}


@router.put("/api/settings/security")
async def put_security_settings_endpoint(
    payload: SecuritySettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    prev = _get_effective_security_settings(int(current_user["id"]))
    merged = {k: prev.get(k) for k in SECURITY_SETTINGS_DEFAULT.keys()}
    for k, v in (payload.model_dump() or {}).items():
        if k in SECURITY_SETTINGS_DEFAULT and v is not None:
            merged[k] = bool(v)
    settings = _safe_security_settings(merged)
    upsert_user_security_settings(int(current_user["id"]), settings)
    return {"settings": settings}


@router.get("/api/settings/auth")
async def get_auth_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    default_minutes = _default_jwt_expire_minutes()
    stored = get_user_auth_settings(int(current_user["id"])) or {}
    raw = stored.get("settings") if isinstance(stored.get("settings"), dict) else {}
    safe = _safe_auth_settings(raw or {})
    effective_minutes = int(safe.get("jwt_expire_minutes") or default_minutes)
    has_override = "jwt_expire_minutes" in (safe or {})
    return {
        "settings": {"jwt_expire_minutes": effective_minutes},
        "defaults": {"jwt_expire_minutes": default_minutes},
        "has_override": bool(has_override),
        "updated_at": stored.get("updated_at") if has_override else None,
    }


@router.put("/api/settings/auth")
async def put_auth_settings_endpoint(
    payload: AuthSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    default_minutes = _default_jwt_expire_minutes()
    use_default = bool(payload.use_default)
    if use_default or payload.jwt_expire_minutes is None:
        delete_user_auth_settings(int(current_user["id"]))
        return {
            "settings": {"jwt_expire_minutes": default_minutes},
            "defaults": {"jwt_expire_minutes": default_minutes},
            "has_override": False,
            "updated_at": None,
        }
    safe = _safe_auth_settings({"jwt_expire_minutes": payload.jwt_expire_minutes})
    jwt_minutes = int(safe.get("jwt_expire_minutes") or default_minutes)
    upsert_user_auth_settings(int(current_user["id"]), {"jwt_expire_minutes": jwt_minutes})
    return {
        "settings": {"jwt_expire_minutes": jwt_minutes},
        "defaults": {"jwt_expire_minutes": default_minutes},
        "has_override": True,
        "updated_at": None,
    }


@router.get("/api/settings/language")
async def get_language_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    stored = get_user_system_profile(current_user["id"]) or {}
    data = stored.get("data") if isinstance(stored.get("data"), dict) else {}
    lang = str((data or {}).get("lang") or "pt").strip().lower()
    if lang not in ("pt", "en", "es", "ar", "zh"):
        lang = "pt"
    return {"lang": lang}


@router.put("/api/settings/language")
async def put_language_settings_endpoint(
    payload: LanguageSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    lang = str(payload.lang or "").strip().lower()
    if lang not in ("pt", "en", "es", "ar", "zh"):
        raise HTTPException(status_code=400, detail="Idioma inválido.")
    update_user_system_profile_data(current_user["id"], {"lang": lang})
    return {"ok": True, "lang": lang}

