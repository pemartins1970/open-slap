"""
📝 Notes Routes - Endpoints para gerenciamento de anotações
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel

from ..deps import security, HTTPAuthorizationCredentials
from ..db import (
    create_note,
    update_note,
    delete_note,
    get_note,
    list_notes,
    search_notes,
    list_notes_by_category,
)
from ..main_auth import get_current_user

notes_router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteCreateInput(BaseModel):
    title: str
    content_md: str
    tags: Optional[str] = None
    project_id: Optional[int] = None
    category: Optional[Literal['nota', 'ideia_solta', 'ideacao', 'projeto_futuro']] = 'nota'
    source: Optional[Literal['user', 'agent']] = 'user'


class NoteUpdateInput(BaseModel):
    title: str
    content_md: str
    tags: Optional[str] = None
    project_id: Optional[int] = None
    category: Optional[Literal['nota', 'ideia_solta', 'ideacao', 'projeto_futuro']] = None
    source: Optional[Literal['user', 'agent']] = None


@notes_router.get("")
async def get_notes_endpoint(
    project_id: Optional[int] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista todas as notas do usuário."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    return list_notes(current_user["id"], project_id=project_id)


@notes_router.post("")
async def create_note_endpoint(
    payload: NoteCreateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Cria uma nova nota."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    note_id = create_note(
        user_id=current_user["id"],
        title=payload.title,
        content_md=payload.content_md,
        tags=payload.tags,
        project_id=payload.project_id,
        category=payload.category or 'nota',
        source=payload.source or 'user',
    )
    
    return {"id": note_id, "message": "Nota criada com sucesso"}


@notes_router.get("/{note_id}")
async def get_note_endpoint(
    note_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém uma nota específica."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    note = get_note(note_id, current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    
    return note


@notes_router.put("/{note_id}")
async def update_note_endpoint(
    note_id: int,
    payload: NoteUpdateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza uma nota existente."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    success = update_note(
        note_id=note_id,
        user_id=current_user["id"],
        title=payload.title,
        content_md=payload.content_md,
        tags=payload.tags,
        project_id=payload.project_id,
        category=payload.category,
        source=payload.source,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não atualizada")
    
    return {"success": True, "message": "Nota atualizada com sucesso"}


@notes_router.delete("/{note_id}")
async def delete_note_endpoint(
    note_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Deleta uma nota."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    success = delete_note(note_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    
    return {"success": True, "message": "Nota removida com sucesso"}


@notes_router.get("/search/{query}")
async def search_notes_endpoint(
    query: str,
    limit: Optional[int] = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Busca notas baseadas em texto usando FTS5."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    return search_notes(current_user["id"], query, limit=limit)


@notes_router.get("/by-category/{category}")
async def get_notes_by_category_endpoint(
    category: str,
    project_id: Optional[int] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista notas por categoria (ideia_solta, ideacao, projeto_futuro, nota)."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return list_notes_by_category(current_user["id"], category, project_id=project_id)
