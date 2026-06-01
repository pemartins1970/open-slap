from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import get_current_user
from ..deps import security
from ..runtime import llm_manager, moe_router

router = APIRouter()


@router.get("/api/experts")
async def get_experts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"experts": moe_router.get_experts()}


@router.get("/api/providers")
async def get_providers(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"providers": await llm_manager.get_provider_status()}

