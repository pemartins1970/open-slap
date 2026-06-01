"""
🔧 Forge Routes - Endpoints para integração com Forge IDE
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, Any

from ..deps import (
    FORGE_IDE_MODE,
    FORGE_IDE_TOKEN_TTL_MINUTES,
    _is_local_client,
    _ensure_forge_user,
    security,
)

forge_router = APIRouter(prefix="/forge", tags=["forge"])

# Imports movidos para evitar circular import
from ..main_auth import (
    verify_token,
    get_current_user,
    discover_harnesses,
    HTTPAuthorizationCredentials,
)

@forge_router.post("/token")
async def forge_token(request: Request):
    """Gera token de acesso para Forge IDE."""
    if not FORGE_IDE_MODE:
        raise HTTPException(status_code=404, detail="Forge IDE Mode desativado")
    if not _is_local_client(request):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas via localhost")

    user = _ensure_forge_user()
    from datetime import timedelta
    from ..auth import auth_manager

    token = auth_manager.create_access_token(
        data={"sub": str(user["id"]), "forge": True},
        expires_delta=timedelta(minutes=int(FORGE_IDE_TOKEN_TTL_MINUTES)),
    )
    return {"access_token": token, "token_type": "bearer", "user": user}

@forge_router.get("/status")
async def forge_status(request: Request):
    """Verifica status do Forge IDE Mode."""
    if not FORGE_IDE_MODE:
        return {"forge_mode": False}
    if not _is_local_client(request):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas via localhost")
    user = _ensure_forge_user()
    return {"forge_mode": True, "user": {"id": user.get("id"), "email": user.get("email")}}

@forge_router.get("/harnesses")
async def forge_harnesses(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Lista harnesses disponíveis no Forge IDE."""
    if not FORGE_IDE_MODE:
        raise HTTPException(status_code=404, detail="Forge IDE Mode desativado")
    token = credentials.credentials
    payload = verify_token(token) or {}
    if not payload.get("forge"):
        raise HTTPException(status_code=403, detail="Token Forge requerido")
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"harnesses": discover_harnesses()}
