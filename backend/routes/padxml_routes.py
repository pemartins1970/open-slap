"""
📄 PadXML Routes - Endpoints para gerenciamento de PadXML
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any

from ..deps import security, HTTPAuthorizationCredentials
from ..main_auth import get_current_user

padxml_router = APIRouter(prefix="/api/padxml", tags=["padxml"])


@padxml_router.get("/software")
async def list_software_endpoint(
    limit: int = Query(20, ge=1, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista software disponível no formato PadXML."""
    raise HTTPException(status_code=501, detail="PadXML não implementado")


@padxml_router.post("/save_message")
async def save_message_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Salva uma mensagem no formato PadXML."""
    raise HTTPException(status_code=501, detail="PadXML não implementado")
