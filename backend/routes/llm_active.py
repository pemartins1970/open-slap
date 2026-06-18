from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import get_current_user
from ..db import get_user_llm_settings
from ..deps import security
from ..runtime import llm_manager

router = APIRouter()


@router.get("/api/llm/active")
async def get_active_provider(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    preferred_provider: Optional[str] = None
    stored = get_user_llm_settings(current_user["id"])
    if stored:
        settings = stored.get("settings") or {}
        mode = str(settings.get("mode") or "").strip().lower()
        provider = str(settings.get("provider") or "").strip().lower()
        if provider and mode not in ("", "env"):
            preferred_provider = provider

    result = await llm_manager.get_active_provider(preferred_provider)
    return result
