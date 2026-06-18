"""
📊 Feedback & Plan Routes - Endpoints para feedback e planejamento de tarefas
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, Query
from typing import List, Dict, Any, Optional

from ..deps import (
    security,
    HTTPAuthorizationCredentials,
    FeedbackInput,
    PlanApproveInput,
    PlanTaskStatusInput,
    OrchestrationStartInput,
    _get_effective_security_settings,
)
from ..db import (
    upsert_message_feedback,
    get_message_feedback,
    create_plan_tasks,
    get_plan_tasks,
    update_plan_task_status,
    save_message,
    get_user_llm_settings,
    get_user_soul,
    list_soul_events,
)
from ..main_auth import (
    get_current_user,
)
from ..runtime import llm_manager, moe_router
from ..agents.base import agent_registry

logger = logging.getLogger(__name__)

feedback_plan_router = APIRouter(prefix="/api", tags=["feedback", "plan"])

_orchestration_runs: Dict[str, Dict[str, Any]] = {}


async def _ws_send(websocket: Optional[WebSocket], payload: dict) -> None:
    """Envia mensagem ao WebSocket se disponível."""
    _logfile = r"C:\Users\pemar\AppData\Local\Temp\opencode\orchestrate_debug.log"
    if websocket is None:
        with open(_logfile, "a", encoding="utf-8") as f:
            f.write(f"[_ws_send] websocket is None — type={payload.get('type')} não enviado\n")
        return
    try:
        await websocket.send_json(payload)
        with open(_logfile, "a", encoding="utf-8") as f:
            f.write(f"[_ws_send] enviado type={payload.get('type')} len={len(str(payload))}\n")
    except Exception as e:
        with open(_logfile, "a", encoding="utf-8") as f:
            f.write(f"[_ws_send] falha ao enviar {payload.get('type')}: {e}\n")


def _build_orchestration_context(user_id: int, conversation_id: int) -> Dict[str, Any]:
    """
    Constrói o mesmo combined_context que o WebSocketOrchestrator usa.
    Retorna dict com: combined_context, user_llm_override, api_key_override
    """
    from ..main_auth import (
        _safe_llm_settings,
        _build_soul_markdown,
        _build_runtime_context_block,
        _get_user_api_key,
    )

    # LLM settings
    stored_llm = get_user_llm_settings(user_id)
    user_llm_override = _safe_llm_settings((stored_llm or {}).get("settings") or {})

    api_key_override = _get_user_api_key(user_id, user_llm_override.get("provider"))
    if api_key_override:
        user_llm_override["api_key"] = api_key_override

    # Soul / user context
    user_context = ""
    stored_soul = get_user_soul(user_id)
    soul_events = list_soul_events(user_id, limit=20)
    if stored_soul:
        user_context = (stored_soul.get("markdown") or "").strip()
        if not user_context:
            user_context = _build_soul_markdown(
                stored_soul.get("data") or {}, soul_events
            ).strip()
    elif soul_events:
        user_context = _build_soul_markdown({}, soul_events).strip()

    # Runtime context block
    sec = _get_effective_security_settings(user_id)
    sys_ctx = _build_runtime_context_block(
        user_id=user_id,
        conversation_id=conversation_id,
        sec=sec,
        llm_override=user_llm_override,
    )

    combined_context = f"{user_context}\n\n{sys_ctx}" if user_context else sys_ctx

    return {
        "combined_context": combined_context,
        "user_llm_override": user_llm_override,
        "sec": sec,
    }


async def _run_orchestration(
    run_id: str,
    conversation_id: int,
    user_id: int,
    auto_approve: bool,
    websocket: Optional[WebSocket] = None,
    current_user: Optional[Dict[str, Any]] = None,
):
    """Execute plan tasks sequentially in background."""
    run = _orchestration_runs.get(run_id)
    if not run:
        return

    tasks = get_plan_tasks(conversation_id)
    if not tasks:
        run["status"] = "completed"
        run["log"].append({"task_id": None, "status": "done", "msg": "No tasks to execute."})
        return

    # Construir contexto completo (soul + runtime + llm settings)
    ctx = {}
    try:
        ctx = _build_orchestration_context(user_id, conversation_id)
    except Exception as e:
        logger.warning(f"Falha ao construir contexto de orquestração: {e}")

    combined_context = ctx.get("combined_context", "")
    user_llm_override = ctx.get("user_llm_override", {})

    tasks_done = 0
    tasks_failed = 0

    def _is_cancelled(run_id: str) -> bool:
        from ..ws.orchestrator import ws_orchestrator
        event = ws_orchestrator.cancel_events.get(run_id)
        return event is not None and event.is_set()

    async def _cancel_exit(msg: str, partial_output: str = "") -> None:
        run["status"] = "cancelled"
        run["log"].append({"task_id": task_id, "status": "cancelled", "msg": msg})
        await _ws_send(websocket, {"type": "status", "content": "⏹️ Orquestração cancelada."})
        await _ws_send(websocket, {"type": "cancelled", "conversation_id": conversation_id})
        partial = partial_output.strip()
        if partial:
            save_message(conversation_id, "assistant", partial + "\n\n*[Orquestração cancelada pelo usuário]*", expert_id=skill_id)
        else:
            save_message(conversation_id, "assistant", "*[Orquestração cancelada pelo usuário]*")

    try:
        for task in tasks:
            task_id = task.get("id")
            title = task.get("title", "")
            skill_id = task.get("skill_id")

            if _is_cancelled(run_id):
                await _cancel_exit("Orquestração cancelada pelo usuário.")
                return

            run["log"].append({"task_id": task_id, "status": "active", "msg": f"Executing: {title}"})
            await _ws_send(websocket, {"type": "status", "content": f"Executando tarefa: {title}"})

            try:
                update_plan_task_status(task_id, "active", conversation_id)

                agent = agent_registry.get(skill_id) if skill_id else None
                if agent:
                    agent_expert = moe_router.select_expert(title, force_expert_id=skill_id) if moe_router else {"id": skill_id}
                    collected = []
                    async for chunk in agent.stream_execute(
                        title,
                        context={
                            "expert": agent_expert,
                            "combined_context": combined_context,
                        },
                    ):
                        if _is_cancelled(run_id):
                            break
                        if isinstance(chunk, str):
                            collected.append(chunk)
                            await _ws_send(websocket, {"type": "chunk", "content": chunk})
                    if _is_cancelled(run_id):
                        await _cancel_exit("Orquestração cancelada durante execução do agente.", partial_output="".join(collected))
                        return
                    output = "".join(collected)
                    if output:
                        save_message(conversation_id, "assistant", output, expert_id=skill_id)
                    tasks_done += 1
                    run["log"].append({"task_id": task_id, "status": "done", "msg": f"Completed: {title}"})
                    update_plan_task_status(task_id, "done", conversation_id)
                else:
                    expert = moe_router.select_expert(title) if moe_router else {"id": "general"}
                    collected = []
                    async for chunk in llm_manager.stream_generate(
                        prompt=title,
                        expert=expert,
                        user_context=combined_context,
                        llm_override=user_llm_override,
                    ):
                        if _is_cancelled(run_id):
                            break
                        if isinstance(chunk, str):
                            collected.append(chunk)
                            await _ws_send(websocket, {"type": "chunk", "content": chunk})
                    if _is_cancelled(run_id):
                        await _cancel_exit("Orquestração cancelada durante geração LLM.", partial_output="".join(collected))
                        return
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
                await _ws_send(websocket, {"type": "status", "content": f"Erro na tarefa: {title}"})
                try:
                    update_plan_task_status(task_id, "failed", conversation_id)
                except Exception:
                    pass

        summary = f"Orquestração concluída: {tasks_done} tarefa(s) executada(s), {tasks_failed} falha(s)."
        save_message(conversation_id, "assistant", summary)
        await _ws_send(websocket, {"type": "chunk", "content": summary})
        await _ws_send(websocket, {"type": "done", "provider": None, "model": None})

        run["status"] = "completed"
        run["tasks_done"] = tasks_done
        run["tasks_failed"] = tasks_failed
        run["log"].append({
            "task_id": None, "status": "done",
            "msg": f"Orchestration finished. {tasks_done} done, {tasks_failed} failed."
        })
    finally:
        from ..ws.orchestrator import ws_orchestrator
        ws_orchestrator.cancel_events.pop(run_id, None)


@feedback_plan_router.post("/feedback")
async def post_feedback(
    payload: FeedbackInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
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
    dbg_session_id: Optional[str] = Query(None),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    _logfile = r"C:\Users\pemar\AppData\Local\Temp\opencode\orchestrate_debug.log"
    with open(_logfile, "a", encoding="utf-8") as f:
        f.write(f"[orchestrate] conv={conversation_id} session_id={payload.session_id!r} auto_approve={payload.auto_approve} dbg_qs={dbg_session_id!r}\n")

    # Recuperar WebSocket ativo da sessão, se houver
    websocket = None
    try:
        from ..ws.orchestrator import ws_orchestrator
        # 1. Tentar por session_id (enviado pelo frontend)
        if payload.session_id:
            websocket = ws_orchestrator.active_connections.get(payload.session_id)
            with open(_logfile, "a", encoding="utf-8") as f:
                f.write(f"[orchestrate] session_id={payload.session_id!r} websocket={'found' if websocket else 'NOT FOUND'}\n")
        # 2. Fallback: buscar por user_id (robusto contra perda de session_id)
        if websocket is None:
            user_id = str(current_user.get("id", ""))
            websocket = ws_orchestrator.active_user_connections.get(user_id)
            with open(_logfile, "a", encoding="utf-8") as f:
                f.write(f"[orchestrate] fallback user_id={user_id} websocket={'found' if websocket else 'NOT FOUND'}\n")
        if websocket is None:
            active = list(ws_orchestrator.active_connections.keys())
            with open(_logfile, "a", encoding="utf-8") as f:
                f.write(f"[orchestrate] NENHUM websocket encontrado. session_ids ativos: {active}\n")
    except Exception as e:
        with open(_logfile, "a", encoding="utf-8") as f:
            f.write(f"[orchestrate] erro: {e}\n")

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
        _run_orchestration,
        run_id,
        conversation_id,
        current_user["id"],
        payload.auto_approve,
        websocket,
        current_user,
    )

    return {"run_id": run_id}


@feedback_plan_router.get("/plan/orchestrate/{run_id}/status")
async def get_orchestration_status(
    run_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
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


@feedback_plan_router.post("/plan/orchestrate/{run_id}/cancel")
async def cancel_orchestration(
    run_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    from ..ws.orchestrator import ws_orchestrator
    await ws_orchestrator.cancel_orchestration(run_id)

    run = _orchestration_runs.get(run_id)
    if run and run.get("status") == "running":
        run["status"] = "cancelled"
        run["log"].append({"task_id": None, "status": "cancelled", "msg": "Cancelamento solicitado via API."})

    return {"ok": True, "run_id": run_id, "status": "cancelled"}
