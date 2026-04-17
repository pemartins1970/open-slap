"""
WebSocket Orchestrator — lógica central de mensagens e streaming.
Extraído de main_auth.py.
"""
import asyncio
import json
import logging
import os
import random
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

# Logger
logger = logging.getLogger(__name__)

# Imports do projeto (serão ajustados conforme necessário)
from ..db import get_db_path
from ..moe_router_simple import moe_router
from ..runtime import llm_manager
from ..services.wizard_service import handle_wizard_message


class WebSocketOrchestrator:
    """Orquestrador WebSocket — gerencia conexões e processamento de mensagens."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.delivery_registry: Dict[str, Dict[str, Any]] = {}

    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        current_user: Dict[str, Any],
    ) -> None:
        """Processa uma conexão WebSocket completa."""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        try:
            # Obter ou criar conversa
            from ..db import get_conversation_by_session_for_user, get_conversation_messages

            conversation = get_conversation_by_session_for_user(
                current_user["id"], session_id
            )
            conversation_id = conversation["id"] if conversation else None
            conversation_kind = (
                conversation.get("kind") if conversation else "conversation"
            ) or "conversation"

            # Enviar histórico se existir
            if conversation_id:
                from src.backend.db import get_conversation_messages

                messages = get_conversation_messages(conversation_id)
                for message in messages:
                    await websocket.send_json({"type": "history", "message": message})

            # Loop de mensagens
            await self._message_loop(
                websocket, session_id, current_user, conversation_id, conversation_kind
            )

        except WebSocketDisconnect:
            logger.info("ws_disconnect user_id=%s session_id=%s", current_user.get("id"), session_id)
        except Exception as e:
            logger.exception("ws_error user_id=%s session_id=%s", current_user.get("id"), session_id)
            try:
                await websocket.send_json({"type": "error", "content": f"Erro: {str(e)}"})
            except Exception:
                pass
        finally:
            # Limpar conexão
            if session_id in self.active_connections:
                del self.active_connections[session_id]

    async def _message_loop(
        self,
        websocket: WebSocket,
        session_id: str,
        current_user: Dict[str, Any],
        conversation_id: Optional[int],
        conversation_kind: str,
    ) -> None:
        """Loop principal de mensagens WebSocket."""
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "chat":
                    await self._handle_chat_message(
                        websocket,
                        session_id,
                        current_user,
                        conversation_id,
                        conversation_kind,
                        data,
                    )

            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.exception("ws_message_error")
                await websocket.send_json({"type": "error", "content": f"Erro: {str(e)}"})
                break

    async def _handle_chat_message(
        self,
        websocket: WebSocket,
        session_id: str,
        current_user: Dict[str, Any],
        conversation_id: Optional[int],
        conversation_kind: str,
        data: Dict[str, Any],
    ) -> None:
        """Processa uma mensagem de chat."""
        user_message = data.get("content", "")
        if not (user_message or "").strip():
            return

        # Inicializar variáveis de controle
        _done_evt = asyncio.Event()
        _last_emit = [time.time()]

        async def _ws_send(payload: Dict[str, Any]) -> None:
            await websocket.send_json(payload)
            _last_emit[0] = time.time()

        # Configurar keepalive
        _ka_task = asyncio.create_task(
            self._ws_idle_keepalive(websocket, _done_evt, _last_emit)
        )

        try:
            # Processar mensagem (simplificado — lógica completa seria movida aqui)
            await _ws_send({"type": "status", "content": "Processando mensagem..."})

            # TODO: Mover toda a lógica de processamento do main_auth.py para cá
            # incluindo: wizard, LLM streaming, connectors, file generation, etc.

            await _ws_send({"type": "done", "content": "Mensagem processada"})

        finally:
            _done_evt.set()
            if _ka_task:
                _ka_task.cancel()

    async def _ws_idle_keepalive(
        self,
        websocket: WebSocket,
        done_evt: asyncio.Event,
        last_emit_ref: List[float],
        interval_s: int = 12,
        idle_s: int = 10,
    ) -> None:
        """Mantém a conexão viva durante processamentos longos."""
        while True:
            if done_evt.is_set():
                return
            await asyncio.sleep(max(1, int(interval_s)))
            if done_evt.is_set():
                return
            try:
                if (time.time() - float(last_emit_ref[0])) >= float(idle_s):
                    await websocket.send_json(
                        {"type": "status", "content": "Ainda processando..."}
                    )
                    last_emit_ref[0] = time.time()
            except Exception:
                return


# Instância global do orquestrador
ws_orchestrator = WebSocketOrchestrator()
