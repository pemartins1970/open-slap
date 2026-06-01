"""
🔌 Connectors Routes - Endpoints para gestão de conectores externos
"""

from fastapi import APIRouter, Request, Depends, Query
from typing import Optional

from ..deps import (
    _require_mcp_secret,
    security,
    TelegramLinkConsumeInput,
    TelegramUnlinkInput,
    TelegramInboundInput,
    HTTPAuthorizationCredentials,
)
from ..main_auth import (
    consume_telegram_link_code,
    revoke_telegram_link,
    get_telegram_user_by_link_code,
)

connectors_router = APIRouter(prefix="/connectors", tags=["connectors"])

@connectors_router.post("/telegram/link")
async def mcp_telegram_link_endpoint(
    payload: TelegramLinkConsumeInput, request: Request
):
    """Consume código de link do Telegram via MCP."""
    _require_mcp_secret(request)
    user_id = consume_telegram_link_code(payload.code)
    if not user_id:
        raise ValueError("Código inválido ou expirado")
    return {"ok": True, "user_id": int(user_id)}

@connectors_router.post("/telegram/unlink")
async def mcp_telegram_unlink_endpoint(payload: TelegramUnlinkInput, request: Request):
    """Revoga link do Telegram via MCP."""
    _require_mcp_secret(request)
    ok = revoke_telegram_link(
        telegram_user_id=payload.telegram_user_id, chat_id=payload.chat_id
    )
    return {"ok": bool(ok)}

@connectors_router.get("/telegram/status")
async def mcp_telegram_status_endpoint(
    request: Request,
    telegram_user_id: str = Query(...),
    chat_id: str = Query(...),
):
    """Verifica status de link do Telegram via MCP."""
    _require_mcp_secret(request)
    user_id = get_telegram_user_by_link_code(telegram_user_id, chat_id)
    return {"linked": bool(user_id), "user_id": int(user_id) if user_id else None}

@connectors_router.post("/telegram/inbound")
async def mcp_telegram_inbound_endpoint(
    payload: TelegramInboundInput, request: Request
):
    """Recebe mensagens inbound do Telegram via MCP."""
    _require_mcp_secret(request)
    from ..main_auth import _handle_telegram_message
    await _handle_telegram_message(
        telegram_user_id=payload.telegram_user_id,
        chat_id=payload.chat_id,
        message_text=payload.message_text,
    )
    return {"ok": True}
