import uuid
from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..auth import get_current_user
from ..deps import security
from ..db import (
    add_task_todo,
    create_conversation,
    delete_conversation,
    get_conversation_messages,
    get_task_todo,
    get_user_conversations,
    list_pending_todos,
    list_task_todos,
    set_conversation_project,
    update_conversation_title,
    update_task_todo,
)

router = APIRouter()


class ConversationCreate(BaseModel):
    title: str


class TitleUpdate(BaseModel):
    title: str


class TodoCreate(BaseModel):
    text: str
    kind: Optional[str] = None
    actor: Optional[str] = None
    origin: Optional[str] = None
    scope: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[str] = None
    parent_todo_id: Optional[int] = None
    delivery_path: Optional[str] = None
    artifact_meta: Optional[Dict[str, Any]] = None


class TodoUpdate(BaseModel):
    text: Optional[str] = None
    status: Optional[str] = None
    kind: Optional[str] = None
    actor: Optional[str] = None
    origin: Optional[str] = None
    scope: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[str] = None
    parent_todo_id: Optional[int] = None
    delivery_path: Optional[str] = None
    artifact_meta: Optional[Dict[str, Any]] = None


class ConversationProjectInput(BaseModel):
    project_id: Optional[int] = None


@router.get("/api/conversations")
async def list_conversations(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    kind: Optional[str] = Query("conversation"),
    source: Optional[str] = Query(None),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    kind_norm = str(kind or "").strip().lower()
    kind_filter: Optional[str] = None
    if kind_norm in ("", "all", "*", "any", "both"):
        kind_filter = None
    elif kind_norm in ("conversation", "task"):
        kind_filter = kind_norm
    else:
        kind_filter = "conversation"

    source_norm = str(source or "").strip().lower()
    source_filter: Optional[str] = None
    if source_norm and source_norm not in ("all", "*", "any"):
        source_filter = source_norm

    conversations = get_user_conversations(
        current_user["id"], kind=kind_filter, source=source_filter
    )
    return {"conversations": conversations}


@router.post("/api/conversations")
async def create_conversation_endpoint(
    conversation: ConversationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    kind: Optional[str] = Query("conversation"),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    kind_to_save = (kind or "conversation").strip().lower()
    if kind_to_save not in ("conversation", "task"):
        kind_to_save = "conversation"

    title = (conversation.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Título vazio")

    session_id = str(uuid.uuid4())
    conversation_id = create_conversation(
        current_user["id"], session_id, title, kind=kind_to_save
    )

    return {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "title": conversation.title,
    }


@router.put("/api/conversations/{conversation_id}/title")
async def rename_conversation_endpoint(
    conversation_id: int,
    payload: TitleUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    ok = update_conversation_title(conversation_id, current_user["id"], payload.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return {"ok": True}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation_endpoint(
    conversation_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    messages = get_conversation_messages(conversation_id)
    return {"messages": messages}


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    success = delete_conversation(conversation_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    return {"message": "Conversa deletada com sucesso"}


@router.put("/api/conversations/{conversation_id}/project")
async def set_conversation_project_endpoint(
    conversation_id: int,
    payload: ConversationProjectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_conversation_project(conversation_id, payload.project_id)
    return {"ok": True}


@router.get("/api/tasks")
async def list_tasks_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    tasks = get_user_conversations(current_user["id"], kind="task")
    return {"tasks": tasks}


@router.post("/api/tasks")
async def create_task_endpoint(
    task: ConversationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    title = (task.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Título vazio")
    session_id = str(uuid.uuid4())
    task_id = create_conversation(current_user["id"], session_id, title, kind="task")
    return {"task_id": task_id, "session_id": session_id, "title": title}


@router.put("/api/tasks/{task_id}/title")
async def rename_task_endpoint(
    task_id: int,
    payload: TitleUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    ok = update_conversation_title(task_id, current_user["id"], payload.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"ok": True}


@router.get("/api/tasks/{task_id}/todos")
async def list_task_todos_endpoint(
    task_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    status: Optional[str] = Query(None),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    todos = list_task_todos(current_user["id"], task_id, status=status)
    return {"todos": todos}


@router.post("/api/tasks/{task_id}/todos")
async def add_task_todo_endpoint(
    task_id: int,
    payload: TodoCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    todo_id = add_task_todo(
        current_user["id"],
        task_id,
        payload.text,
        kind=payload.kind or "step",
        actor=payload.actor or "human",
        origin=payload.origin or "user",
        scope=payload.scope or "project",
        priority=payload.priority or "medium",
        due_at=payload.due_at,
        parent_todo_id=payload.parent_todo_id,
        delivery_path=payload.delivery_path,
        artifact_meta=payload.artifact_meta,
    )
    return {"todo_id": todo_id}


@router.get("/api/tasks/todos")
async def list_global_todos_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    todos = list_pending_todos(current_user["id"])
    return {"todos": todos}


@router.put("/api/tasks/todos/{todo_id}")
async def update_task_todo_endpoint(
    todo_id: int,
    payload: TodoUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    ok = update_task_todo(
        current_user["id"],
        todo_id,
        text=payload.text,
        status=payload.status,
        kind=payload.kind,
        actor=payload.actor,
        origin=payload.origin,
        scope=payload.scope,
        priority=payload.priority,
        due_at=payload.due_at,
        parent_todo_id=payload.parent_todo_id,
        delivery_path=payload.delivery_path,
        artifact_meta=payload.artifact_meta,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="TODO não encontrado")
    return {"ok": True}


@router.get("/api/tasks/todos/{todo_id}/artifacts")
async def get_todo_artifacts_endpoint(
    todo_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    td = get_task_todo(current_user["id"], int(todo_id))
    if not td:
        raise HTTPException(status_code=404, detail="TODO não encontrado")
    meta = td.get("artifact_meta")
    if isinstance(meta, dict) and isinstance(meta.get("artifacts"), list):
        return {"artifacts": meta.get("artifacts") or []}
    if isinstance(meta, list):
        return {"artifacts": meta}
    return {"artifacts": []}

