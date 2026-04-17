"""
🔍 Search & Skills Routes - Endpoints para busca de mensagens e gestão de skills
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional

from ..deps import SkillsUpdate, security
from ..main_auth import (
    search_user_messages,
    get_user_skills,
    upsert_user_skills,
    HTTPAuthorizationCredentials,
    get_current_user,
)

search_skills_router = APIRouter(prefix="/api", tags=["search", "skills"])

@search_skills_router.get("/search/messages")
async def search_messages_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    q: str = Query(""),
    kind: Optional[str] = Query(None),
    limit: int = Query(50),
):
    """Busca mensagens do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    results = search_user_messages(current_user["id"], q, limit=int(limit), kind=kind)
    return {"results": results}

@search_skills_router.get("/skills")
async def list_skills_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista skills do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    skills = get_user_skills(current_user["id"]) or []
    return {"skills": skills}

@search_skills_router.put("/skills")
async def put_skills_endpoint(
    payload: SkillsUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza skills do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    skills = payload.skills if isinstance(payload.skills, list) else []
    upsert_user_skills(current_user["id"], skills)
    return {"ok": True, "count": len(skills)}
