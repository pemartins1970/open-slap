import json
from typing import Any, Dict, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import (
    create_telegram_link_code,
    delete_user_connector_secret,
    list_telegram_links,
    upsert_user_connector_secret_ciphertext,
)
from ..deps import (
    _dpapi_protect_text,
    _ensure_connectors_allowed,
    _get_user_connector_secret,
    _get_user_connector_secret_raw,
    _sanitize_api_key,
    security,
)

router = APIRouter()


class GitHubConnectInput(BaseModel):
    token: str


class TokenConnectInput(BaseModel):
    token: str


class AutomationClientSettingsInput(BaseModel):
    base_url: str
    api_key: Optional[str] = None


def _google_bearer_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


async def _google_test_get(url: str, access_token: str) -> Dict[str, Any]:
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=_google_bearer_headers(access_token)) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao validar credencial (HTTP {resp.status}).",
                )
            return data or {}

@router.put("/api/connectors/github")
async def put_github_connector_endpoint(
    payload: GitHubConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "github", ciphertext)
    return {"ok": True}

@router.delete("/api/connectors/github")
async def delete_github_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "github")
    return {"ok": bool(ok)}

@router.post("/api/connectors/github/test")
async def test_github_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    gh_token = _get_user_connector_secret(current_user["id"], "github")
    if not gh_token:
        raise HTTPException(status_code=400, detail="Conector GitHub não configurado.")

    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get("https://api.github.com/user", headers=headers) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao validar token do GitHub (HTTP {resp.status}).",
                )
            login = (data or {}).get("login")
            return {
                "ok": True,
                "user": {"login": login, "id": (data or {}).get("id")},
            }

@router.put("/api/connectors/google_drive")
async def put_google_drive_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(
        current_user["id"], "google_drive", ciphertext
    )
    return {"ok": True}

@router.delete("/api/connectors/google_drive")
async def delete_google_drive_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "google_drive")
    return {"ok": bool(ok)}

@router.post("/api/connectors/google_drive/test")
async def test_google_drive_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    access_token = _get_user_connector_secret(current_user["id"], "google_drive")
    if not access_token:
        raise HTTPException(
            status_code=400, detail="Conector Google Drive não configurado."
        )
    data = await _google_test_get(
        "https://www.googleapis.com/drive/v3/about?fields=user",
        access_token,
    )
    return {"ok": True, "drive": {"user": (data or {}).get("user")}}

@router.put("/api/connectors/google_calendar")
async def put_google_calendar_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(
        current_user["id"], "google_calendar", ciphertext
    )
    return {"ok": True}

@router.delete("/api/connectors/google_calendar")
async def delete_google_calendar_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "google_calendar")
    return {"ok": bool(ok)}

@router.post("/api/connectors/google_calendar/test")
async def test_google_calendar_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    access_token = _get_user_connector_secret(current_user["id"], "google_calendar")
    if not access_token:
        raise HTTPException(
            status_code=400, detail="Conector Google Calendar não configurado."
        )
    data = await _google_test_get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1",
        access_token,
    )
    items = (data or {}).get("items") if isinstance(data, dict) else None
    first = items[0] if isinstance(items, list) and items else None
    return {"ok": True, "calendar": {"sample": first}}

@router.put("/api/connectors/gmail")
async def put_gmail_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "gmail", ciphertext)
    return {"ok": True}

@router.delete("/api/connectors/gmail")
async def delete_gmail_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "gmail")
    return {"ok": bool(ok)}

@router.post("/api/connectors/gmail/test")
async def test_gmail_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    access_token = _get_user_connector_secret(current_user["id"], "gmail")
    if not access_token:
        raise HTTPException(status_code=400, detail="Conector Gmail não configurado.")
    data = await _google_test_get(
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        access_token,
    )
    email = (data or {}).get("emailAddress")
    return {"ok": True, "gmail": {"email": email}}

@router.put("/api/connectors/tera")
async def put_tera_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "tera", ciphertext)
    return {"ok": True}

@router.delete("/api/connectors/tera")
async def delete_tera_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "tera")
    return {"ok": bool(ok)}

@router.post("/api/connectors/tera/test")
async def test_tera_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    value = _get_user_connector_secret(current_user["id"], "tera")
    if not value:
        raise HTTPException(status_code=400, detail="Conector Tera não configurado.")
    return {"ok": True}

@router.put("/api/connectors/telegram")
async def put_telegram_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "telegram", ciphertext)
    return {"ok": True}

@router.delete("/api/connectors/telegram")
async def delete_telegram_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "telegram")
    return {"ok": bool(ok)}

@router.post("/api/connectors/telegram/test")
async def test_telegram_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    tg_token = _get_user_connector_secret(current_user["id"], "telegram")
    if not tg_token:
        raise HTTPException(
            status_code=400, detail="Conector Telegram não configurado."
        )
    url = f"https://api.telegram.org/bot{tg_token}/getMe"
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400 or not (data or {}).get("ok"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao validar token do Telegram (HTTP {resp.status}).",
                )
            result = (data or {}).get("result") or {}
            return {
                "ok": True,
                "bot": {
                    "id": result.get("id"),
                    "username": result.get("username"),
                    "first_name": result.get("first_name"),
                },
            }

@router.post("/api/connectors/telegram/link-code")
async def create_telegram_link_code_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    created = create_telegram_link_code(int(current_user["id"]), ttl_seconds=600)
    return {"code": created.get("code"), "expires_at": created.get("expires_at")}

@router.get("/api/connectors/telegram/links")
async def list_telegram_links_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    links = list_telegram_links(int(current_user["id"]))
    return {"links": links}

@router.get("/api/automation_client")
async def get_automation_client_settings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    raw = _get_user_connector_secret_raw(int(current_user["id"]), "automation_client") or ""
    obj: Dict[str, Any] = {}
    try:
        obj = json.loads(raw) if raw else {}
    except Exception:
        obj = {}
    base_url = str(obj.get("base_url") or "").strip()
    has_key = bool(str(obj.get("api_key") or "").strip())
    return {"settings": {"base_url": base_url}, "has_api_key": has_key}

@router.put("/api/automation_client")
async def put_automation_client_settings(
    payload: AutomationClientSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    base_url = str(payload.base_url or "").strip().strip("`\"' ,").rstrip("/")
    api_key = str(payload.api_key or "").strip()
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url obrigatório.")
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="base_url inválido (http/https).")
    raw = _get_user_connector_secret_raw(int(current_user["id"]), "automation_client") or ""
    try:
        obj_prev = json.loads(raw) if raw else {}
    except Exception:
        obj_prev = {}
    existing_key = str((obj_prev or {}).get("api_key") or "").strip()
    if not api_key:
        api_key = existing_key
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key obrigatório.")
    obj = {"base_url": base_url, "api_key": api_key}
    ciphertext = _dpapi_protect_text(json.dumps(obj, ensure_ascii=False))
    upsert_user_connector_secret_ciphertext(
        int(current_user["id"]), "automation_client", ciphertext
    )
    return {"ok": True, "settings": {"base_url": base_url}, "has_api_key": True}

@router.delete("/api/automation_client")
async def delete_automation_client_settings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(int(current_user["id"]), "automation_client")
    return {"deleted": bool(ok), "has_api_key": False}

@router.post("/api/automation_client/test")
async def test_automation_client_settings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    raw = _get_user_connector_secret_raw(int(current_user["id"]), "automation_client") or ""
    try:
        obj = json.loads(raw) if raw else {}
    except Exception:
        obj = {}
    base_url = str((obj or {}).get("base_url") or "").strip().rstrip("/")
    api_key = str((obj or {}).get("api_key") or "").strip()
    if not base_url or not api_key:
        raise HTTPException(status_code=400, detail="Cliente externo não configurado.")
    timeout = aiohttp.ClientTimeout(total=4)
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{base_url}/health", headers=headers) as resp:
                return {"ok": resp.status < 500, "status": resp.status}
    except Exception:
        return {"ok": False, "status": None}
