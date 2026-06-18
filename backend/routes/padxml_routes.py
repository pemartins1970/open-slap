"""
📄 PadXML Routes - Endpoints para gerenciamento de PadXML
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse
from typing import List, Optional, Dict, Any

from ..deps import security, HTTPAuthorizationCredentials

REDIRECT_URL = "/api/soul/extract_and_save"

padxml_router = APIRouter(prefix="/api/padxml", tags=["padxml"])


@padxml_router.get("/software")
async def list_software_endpoint(
    limit: int = Query(20, ge=1, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista software disponível no formato PadXML."""
    raise HTTPException(status_code=501, detail="PadXML não implementado")


@padxml_router.post("/save_message", status_code=308)
async def save_message_redirect(request: Request):
    """Rota legada — redireciona para /api/soul/extract_and_save."""
    return RedirectResponse(url=REDIRECT_URL, status_code=308)
