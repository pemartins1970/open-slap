"""
🧠 Memory & Connectors Routes - Endpoints para gestão de memória e conectores API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from ..deps import security, HTTPAuthorizationCredentials, ConnectorSecretInput
from ..db import list_user_connector_keys as get_user_connectors, upsert_user_connector_secret_ciphertext as upsert_user_connector_secret
from ..main_auth import get_current_user

memory_connectors_router = APIRouter(prefix="/api", tags=["memory", "connectors"])

@memory_connectors_router.post("/memory/decay")
async def trigger_memory_decay_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Dispara processo de decaimento de memória."""
    raise HTTPException(status_code=501, detail="Memory decay não implementado")

@memory_connectors_router.get("/connectors")
async def list_connectors_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista conectores disponíveis para o usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    connectors = get_user_connectors(current_user["id"])
    return {"connectors": connectors}

@memory_connectors_router.put("/connectors/{connector_key}/secret")
async def update_connector_secret(
    connector_key: str,
    payload: ConnectorSecretInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza secret de um conector."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    upsert_user_connector_secret(
        user_id=current_user["id"],
        connector_key=connector_key,
        secret_ciphertext=payload.secret_ciphertext,
    )
    return {"ok": True}
