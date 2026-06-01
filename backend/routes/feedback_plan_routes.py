"""
📊 Feedback & Plan Routes - Endpoints para feedback e planejamento de tarefas
"""

import logging
import uuid
from datetime import datetime, timezone
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
    save_message,
)
from ..main_auth import get_current_user
from ..runtime import llm_manager, moe_router
from ..agents.base import agent_registry

logger = logging.getLogger(__name__)

feedback_plan_router = APIRouter(prefix="/api", tags=["feedback", "plan"])

# In-memory orchestration run storage
_orchestration_runs: Dict[str, Dict[str, Any]] = {}


async def _run_orchestration(run_id: str, conversation_id: int, user_id: int, auto_approve: bool):
    """Execute plan tasks sequentially in background."""
    run = _orchestration_runs.get(run_id)
    if not run:
        return

    tasks = get_plan_tasks(conversation_id)
    if not tasks:
        run["status"] = "completed"
        run["log"].append({"task_id": None, "status": "done", "msg": "No tasks to execute."})
        return

    tasks_done = 0
    tasks_failed = 0

    for task in tasks:
        task_id = task.get("id")
        title = task.get("title", "")
        skill_id = task.get("skill_id")

        run["log"].append({"task_id": task_id, "status": "active", "msg": f"Executing: {title}"})

        try:
            update_plan_task_status(task_id, "active", conversation_id)

            agent = agent_registry.get(skill_id) if skill_id else None
            if agent:
                result = await agent.execute(title, context={})
                if result.status == "success":
                    output = result.data.get("response", "")
                    if output:
                        save_message(conversation_id, "assistant", output, expert_id=skill_id)
                    tasks_done += 1
                    run["log"].append({"task_id": task_id, "status": "done", "msg": f"Completed: {title}"})
                    update_plan_task_status(task_id, "done", conversation_id)
                else:
                    tasks_failed += 1
                    error_msg = result.error or "Unknown error"
                    run["log"].append({"task_id": task_id, "status": "failed", "msg": f"Agent failed: {error_msg}"})
                    update_plan_task_status(task_id, "failed", conversation_id)
            else:
                expert = moe_router.select_expert(title) if moe_router else {"id": "general"}
                collected = []
                async for chunk in llm_manager.stream_generate(
                    prompt=title,
                    expert=expert,
                    user_context="",
                ):
                    if isinstance(chunk, str):
                        collected.append(chunk)
                output = "".join(collected)
                if output:
                    save_message(conversation_id, "assistant", output, expert_id=expert.get("id"))
                tasks_done += 1
                run["log"].append({"task_id": task_id, "status": "done", "msg": f"Completed: {title}"})
                update_plan_task_status(task_id, "done", conversation_id)

        except Exception as e:
            tasks_failed += 1
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            run["log"].append({"task_id": task_id, "status": "failed", "msg": f"Error: {str(e)}"})
            try:
                update_plan_task_status(task_id, "failed", conversation_id)
            except Exception:
                pass

    summary = f"Orquestração concluída: {tasks_done} tarefa(s) executada(s), {tasks_failed} falha(s)."
    save_message(conversation_id, "assistant", summary)
    run["status"] = "completed"
    run["tasks_done"] = tasks_done
    run["tasks_failed"] = tasks_failed
    run["log"].append({
        "task_id": None, "status": "done",
        "msg": f"Orchestration finished. {tasks_done} done, {tasks_failed} failed."
    })

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
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    _orchestration_runs[run_id] = {
        "status": "running",
        "conversation_id": conversation_id,
        "user_id": current_user["id"],
        "started_at": now,
        "tasks_done": 0,
        "tasks_failed": 0,
        "log": [{"task_id": None, "status": "running", "msg": "Orchestration started."}],
    }

    background_tasks.add_task(
        _run_orchestration, run_id, conversation_id, current_user["id"], payload.auto_approve
    )

    return {"run_id": run_id}

@feedback_plan_router.get("/plan/orchestrate/{run_id}/status")
async def get_orchestration_status(
    run_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Obtém status da orquestração."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    run = _orchestration_runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "status": run["status"],
        "tasks_done": run["tasks_done"],
        "tasks_failed": run["tasks_failed"],
        "log": run["log"],
    }
