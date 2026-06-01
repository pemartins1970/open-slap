"""
🚀 Onboarding Routes - Endpoints para gerenciamento de onboarding de usuários
"""

from fastapi import APIRouter, HTTPException, Depends

from ..deps import security, HTTPAuthorizationCredentials
from ..db import (
    get_user_onboarding_completed,
    set_user_onboarding_completed,
)
from ..main_auth import get_current_user

onboarding_router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@onboarding_router.get("/status")
async def get_onboarding_status_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verifica status do onboarding do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    completed = get_user_onboarding_completed(current_user["id"])

    return {
        "completed": completed if completed is not None else False,
        "user_id": current_user["id"]
    }


@onboarding_router.post("/complete")
async def complete_onboarding_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Marca o onboarding do usuário como concluído."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    set_user_onboarding_completed(current_user["id"], True)

    return {
        "ok": True,
        "completed": True,
        "message": "Onboarding concluído com sucesso"
    }


@onboarding_router.post("/reset")
async def reset_onboarding_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Reseta o status do onboarding do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    set_user_onboarding_completed(current_user["id"], False)

    return {
        "ok": True,
        "completed": False,
        "message": "Onboarding resetado com sucesso"
    }
