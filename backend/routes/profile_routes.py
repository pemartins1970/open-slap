"""
👤 User Profile Routes - Endpoints para system profile e soul management
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ..deps import (
    security,
    HTTPAuthorizationCredentials,
    SoulInput,
    SoulEventInput,
    SystemProfileRefreshInput,
)
from ..db import (
    get_user_system_profile,
    update_user_system_profile_data,
    delete_user_system_profile,
    get_user_soul,
    upsert_user_soul,
    append_soul_event,
)
from ..main_auth import get_current_user

profile_router = APIRouter(prefix="/api", tags=["profile", "soul"])

@profile_router.get("/system_profile")
async def get_system_profile_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém o system profile do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    profile = get_user_system_profile(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="System profile não encontrado")
    
    return {
        "profile_markdown": profile.get("profile_md"),
        "profile_json": profile.get("profile_json"),
        "updated_at": profile.get("updated_at"),
    }

@profile_router.post("/system_profile/refresh")
async def refresh_system_profile_endpoint(
    payload: SystemProfileRefreshInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza o system profile do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    # Força refresh invalidando o cache e reconstruindo
    from ..main_auth import _build_system_profile, _format_system_profile_summary
    profile_data = _build_system_profile(current_user["id"])
    profile = get_user_system_profile(current_user["id"])
    
    return {
        "profile_markdown": profile.get("profile_md"),
        "profile_json": profile.get("profile_json"),
        "updated_at": profile.get("updated_at"),
    }

@profile_router.delete("/system_profile")
async def delete_system_profile_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Remove o system profile do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    ok = delete_user_system_profile(current_user["id"])
    return {"deleted": bool(ok)}

@profile_router.get("/soul")
async def get_soul_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém o soul (alma) do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    soul = get_user_soul(current_user["id"])
    if not soul:
        raise HTTPException(status_code=404, detail="Soul não encontrado")
    
    return {
        "soul_json": soul.get("soul_json"),
        "soul_markdown": soul.get("soul_markdown"),
        "updated_at": soul.get("updated_at"),
    }

@profile_router.put("/soul")
async def put_soul_endpoint(
    payload: SoulInput, 
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Atualiza o soul do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    soul = upsert_user_soul(
        user_id=current_user["id"],
        soul_json=payload.soul_json,
        soul_markdown=payload.soul_markdown,
    )
    
    return {
        "soul_json": soul.get("soul_json"),
        "soul_markdown": soul.get("soul_markdown"),
        "updated_at": soul.get("updated_at"),
    }

@profile_router.post("/soul/events")
async def append_soul_event_endpoint(
    payload: SoulEventInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Adiciona um evento ao soul do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    append_soul_event(
        user_id=current_user["id"],
        source=payload.source,
        event_type=payload.event_type,
        content=payload.content,
    )
    
    return {"ok": True}
