"""
📊 Feedback & Plan Routes - Endpoints para feedback e planejamento de tarefas
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional

from ..deps import (
    security,
    HTTPAuthorizationCredentials,
    FeedbackInput,
    PlanApproveInput,
    PlanTaskStatusInput,
    OrchestrationStartInput,
)
from ..db import (
    upsert_message_feedback,
    get_message_feedback,
    create_plan_tasks,
    get_plan_tasks,
    update_plan_task_status,
)
from ..main_auth import get_current_user

feedback_plan_router = APIRouter(prefix="/api", tags=["feedback", "plan"])

@feedback_plan_router.post("/feedback")
async def post_feedback(
    payload: FeedbackInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Registra feedback (thumbs up/down) para uma mensagem."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    upsert_message_feedback(
        user_id=current_user["id"],
        message_id=payload.message_id,
        rating=payload.rating,
    )
    return {"ok": True}

@feedback_plan_router.get("/feedback/{message_id}")
async def get_feedback(
    message_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém feedback de uma mensagem específica."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    rating = get_message_feedback(
        user_id=current_user["id"],
        message_id=message_id,
    )
    return {"rating": rating}

@feedback_plan_router.post("/plan/approve")
async def approve_plan(
    payload: PlanApproveInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Aprova um plano e cria as tarefas associadas."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    ids = create_plan_tasks(
        user_id=current_user["id"],
        parent_conversation_id=payload.conversation_id,
        tasks=payload.tasks,
    )
    return {"ok": True, "task_ids": ids, "count": len(ids)}

@feedback_plan_router.get("/plan/tasks/{conversation_id}")
async def get_plan_tasks_endpoint(
    conversation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém tarefas de planejamento de uma conversa."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    tasks = get_plan_tasks(conversation_id)
    return {"tasks": tasks}

@feedback_plan_router.put("/plan/tasks/{task_id}/status")
async def update_plan_task(
    task_id: int,
    payload: PlanTaskStatusInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza status de uma tarefa de planejamento."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    update_plan_task_status(
        task_id=task_id,
        status=payload.status,
        conversation_id=payload.conversation_id,
    )
    return {"ok": True}

@feedback_plan_router.post("/plan/orchestrate/{conversation_id}")
async def start_orchestration(
    conversation_id: int,
    background_tasks: BackgroundTasks,
    payload: OrchestrationStartInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Inicia orquestração de tarefas em background."""
    raise HTTPException(status_code=501, detail="Orquestração não implementada")

@feedback_plan_router.get("/plan/orchestrate/{run_id}/status")
async def get_orchestration_status(
    run_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém status da orquestração."""
    raise HTTPException(status_code=501, detail="Orquestração não implementada")
