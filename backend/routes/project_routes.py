import logging
import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..db import (
    get_user_projects,
    get_project,
    create_project,
    update_project_name,
    update_project_context,
    delete_project,
)
from ..auth import get_current_user
from ..deps import security

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])

# --- Schemas ---

class ProjectCreateInput(BaseModel):
    name: str
    context_md: Optional[str] = ""

class ProjectUpdateInput(BaseModel):
    name: Optional[str] = None
    context_md: Optional[str] = None

# --- Routes ---

@router.get("")
async def list_projects(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista todos os projetos do usuário autenticado."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"projects": get_user_projects(user["id"])}

@router.post("")
async def create_project_endpoint(
    payload: ProjectCreateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Cria um novo projeto."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome do projeto é obrigatório")
    
    try:
        pid = create_project(user["id"], name, payload.context_md or "")
        return {"ok": True, "project_id": pid}
    except Exception as e:
        logger.exception("Falha ao criar projeto para o usuário %s", str(user.get("id")))
        
        debug = (os.getenv("OPENSLAP_DEBUG_ERRORS") or "").strip().lower() in {"1", "true", "yes", "on"}
        detail = str(e) if debug else "Erro interno ao processar a criação do projeto"
        raise HTTPException(status_code=500, detail=detail)

@router.put("/{project_id}")
async def update_project_endpoint(
    project_id: int,
    payload: ProjectUpdateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza as informações de um projeto existente."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    name = payload.name if isinstance(payload.name, str) else None
    context_md = payload.context_md if isinstance(payload.context_md, str) else None
    
    if name is None and context_md is None:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar fornecido")
        
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise HTTPException(status_code=400, detail="Nome do projeto não pode ser vazio")
        update_project_name(project_id, user["id"], clean_name)
        
    if context_md is not None:
        update_project_context(project_id, user["id"], context_md)
        
    return {"ok": True}

@router.delete("/{project_id}")
async def delete_project_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Remove um projeto permanentemente."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    ok = delete_project(project_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Projeto não encontrado ou acesso negado")
    
    return {"ok": True}
