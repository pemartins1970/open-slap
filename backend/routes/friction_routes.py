"""
Rotas de friction — config, pending, report, send, discard, session delete.
Extraídas de main_auth.py.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..deps import security, active_connections
from ..main_auth import get_current_user

friction_router = APIRouter(tags=["friction"])


class FrictionReportInput(BaseModel):
    code: str
    layer: str
    action_attempted: str
    blocked_by: str
    session_id: str
    user_message: Optional[str] = None
    os: Optional[str] = None
    runtime: Optional[str] = None
    skill_active: Optional[str] = None
    connector_active: Optional[str] = None
    product: str = "open-slap"
    tier: str = "free"


@friction_router.get("/api/friction/config")
async def get_friction_config(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna configuração atual de friction."""
    # Lazy imports para evitar circular
    from ..main_auth import (
        _friction_mode,
        _friction_payload,
        _friction_frontend_payload,
    )
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {
        "mode": _friction_mode(),
        "payload_keys": list(_friction_payload.keys()) if _friction_payload else [],
        "frontend_keys": list(_friction_frontend_payload.keys()) if _friction_frontend_payload else [],
        "github_issue_creation": _friction_mode() in ("debug", "verbose"),
        "frontend_notifications": True,
    }


@friction_router.get("/api/friction/pending_count")
async def get_friction_pending_count(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna contagem de eventos de friction pendentes."""
    # Lazy import para evitar circular
    from ..main_auth import count_pending_friction_events
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    count = count_pending_friction_events(int(current_user["id"]))
    return {"count": count}


@friction_router.get("/api/friction/pending")
async def get_friction_pending(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna lista de eventos de friction pendentes."""
    # Lazy import para evitar circular
    from ..main_auth import list_friction_events
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    events = list_friction_events(int(current_user["id"]), status="pending", limit=50)
    return {"events": events, "count": len(events)}


@friction_router.post("/api/friction/report")
async def report_friction(
    payload: FrictionReportInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Reporta um evento de friction."""
    # Lazy imports para evitar circular
    from ..main_auth import (
        create_friction_event,
        _friction_mode,
        _create_github_issue,
    )
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    # Criar evento de friction
    event_id = create_friction_event(
        user_id=int(current_user["id"]),
        code=payload.code,
        layer=payload.layer,
        action_attempted=payload.action_attempted,
        blocked_by=payload.blocked_by,
        session_id=payload.session_id,
        user_message=payload.user_message,
        os=payload.os,
        runtime=payload.runtime,
        skill_active=payload.skill_active,
        connector_active=payload.connector_active,
        product=payload.product,
        tier=payload.tier,
    )

    # Criar issue no GitHub se modo debug/verbose
    github_url = None
    mode = _friction_mode()
    if mode in ("debug", "verbose"):
        try:
            issue_payload = {
                "event": payload.dict(),
                "meta": {
                    "reported_at": datetime.utcnow().isoformat(),
                    "reported_by": "friction_api",
                },
            }
            github_url = await _create_github_issue(issue_payload, submission_mode="api")
        except Exception:
            pass

    return {
        "ok": True,
        "event_id": event_id,
        "github_issue_url": github_url,
    }


@friction_router.post("/api/friction/pending/send")
async def send_pending_friction(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Envia eventos de friction pendentes (ex: para analytics)."""
    # Lazy imports para evitar circular
    from ..main_auth import list_friction_events, mark_friction_event_sent
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    events = list_friction_events(int(current_user["id"]), status="pending", limit=100)
    sent_count = 0

    for event in events:
        try:
            mark_friction_event_sent(int(current_user["id"]), event["id"])
            sent_count += 1
        except Exception:
            pass

    return {"ok": True, "sent_count": sent_count}


@friction_router.post("/api/friction/pending/{event_id}/discard")
async def discard_friction_event(
    event_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Descarta um evento de friction pendente."""
    # Lazy import para evitar circular
    from ..main_auth import delete_friction_event
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    try:
        delete_friction_event(int(current_user["id"]), event_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@friction_router.delete("/api/session/{session_id}")
async def delete_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Remove uma sessão WebSocket ativa."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    # Verificar se a sessão pertence ao usuário
    ws = active_connections.get(session_id)
    if ws:
        # Fechar conexão
        try:
            await ws.close(code=1000, reason="Sessão encerrada pelo usuário")
        except Exception:
            pass
        active_connections.pop(session_id, None)

    return {"ok": True, "session_id": session_id}
