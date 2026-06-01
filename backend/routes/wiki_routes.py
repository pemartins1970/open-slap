"""Wiki Routes — Endpoints para a base de conhecimento de projetos."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel

from ..deps import security, HTTPAuthorizationCredentials
from ..auth import get_current_user
from ..db import (
    get_project, get_wiki_section, get_wiki_full,
    append_wiki_entry, log_agent_action
)

wiki_router = APIRouter(prefix="/api/projects", tags=["wiki"])


class WikiEntryInput(BaseModel):
    section: str
    title: Optional[str] = ''
    content_md: str
    author: Optional[str] = 'user'


@wiki_router.post("/{project_id}/wiki")
async def add_wiki_entry_endpoint(
    project_id: int,
    payload: WikiEntryInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Adiciona uma entrada na wiki do projeto."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    entry_id = append_wiki_entry(
        project_id, user["id"],
        section=payload.section,
        content_md=payload.content_md,
        author=payload.author or 'user',
        title=payload.title or ''
    )
    return {"ok": True, "entry_id": entry_id}
