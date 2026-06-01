import logging
from typing import Any, Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect

# Imports corrigidos usando caminhos relativos ao pacote backend
from backend.tenant_manager import tenant_manager
from backend.security_guardrail import SecurityGuardrail
from backend.trace_logger import trace_logger

from backend.db import (
    get_conversation_by_session_for_user,
    create_conversation,
    save_message,
    get_user_llm_settings,
    get_user_soul,
    list_soul_events
)
from backend.runtime import moe_router, llm_manager
from backend.agents.base import agent_registry

logger = logging.getLogger(__name__)

class WebSocketOrchestrator:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_steps: Dict[str, int] = {}

    async def handle_connection(self, websocket: WebSocket, session_id: str, current_user: Dict[str, Any]) -> None:
        """
        Aceita e gerencia o ciclo de vida de uma conexão WebSocket
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket conectado: session_id={session_id}, user={current_user.get('id')}")
        
        try:
            while True:
                data = await websocket.receive_json()
                conversation_id = data.get("conversation_id")
                conversation_kind = data.get("conversation_kind", "conversation")
                
                await self._handle_chat_message(
                    websocket=websocket,
                    session_id=session_id,
                    current_user=current_user,
                    conversation_id=conversation_id,
                    conversation_kind=conversation_kind,
                    data=data
                )
        except WebSocketDisconnect:
            logger.info(f"WebSocket desconectado (normal): session_id={session_id}")
        except Exception as e:
            logger.error(f"Erro no WebSocket: session_id={session_id}, erro={str(e)}")
        finally:
            self.active_connections.pop(session_id, None)
            self.session_steps.pop(session_id, None)

    async def _handle_chat_message(
        self, websocket: WebSocket, session_id: str, current_user: Dict[str, Any], 
        conversation_id: Optional[int], conversation_kind: str, data: Dict[str, Any]
    ) -> None:
        """
        Trata o recebimento de mensagens de chat e orquestra a geração de respostas via LLM
        """
        user_message = data.get("content", "")
        if not (user_message or "").strip():
            return

        user_id = int(current_user["id"])
        tenant_manager.set_tenant(str(user_id))
        
        # Imports locais para evitar dependência circular
        from backend.main_auth import (
            _safe_llm_settings,
            _get_effective_security_settings,
            _build_runtime_context_block,
            _build_soul_markdown,
            _get_user_api_key
        )

        
        # 1. Obter ou criar conversa vinculada ao session_id
        if not conversation_id:
            conv = get_conversation_by_session_for_user(user_id, session_id)
            if conv:
                conversation_id = conv["id"]
            else:
                conversation_id = create_conversation(
                    user_id=user_id,
                    session_id=session_id,
                    title=user_message[:50],
                    kind=conversation_kind,
                    source="web"
                )

        # 2. Avaliar segurança pelo B.E.N. 2.0
        security_eval = SecurityGuardrail.evaluate(user_message)

        if security_eval["action"] == "block":
            reason = security_eval.get("reason", "Bloqueado pelo B.E.N. 2.0.")
            # Salvar mensagem de erro no histórico
            save_message(conversation_id, "user", user_message)
            save_message(conversation_id, "assistant", f"Segurança: {reason}")
            
            await websocket.send_json({
                "type": "error",
                "content": f"Segurança: {reason}"
            })
            return

        # Salvar mensagem do usuário
        save_message(conversation_id, "user", user_message)

        # Enviar ACK do recebimento e status inicial
        client_message_id = data.get("client_message_id")
        if client_message_id:
            await websocket.send_json({
                "type": "user_ack",
                "client_message_id": client_message_id,
                "message": {"role": "user", "content": user_message}
            })

        await websocket.send_json({"type": "status", "content": "Analisando intenção..."})

        # 3. Selecionar especialista (expert)
        force_expert_id = data.get("force_expert_id")
        expert = moe_router.select_expert(user_message, force_expert_id=force_expert_id)
        
        # 4. Obter configurações do usuário e contexto do SOUL
        stored_llm = get_user_llm_settings(user_id)
        user_llm_override = _safe_llm_settings((stored_llm or {}).get("settings") or {})
        
        api_key_override = _get_user_api_key(user_id, user_llm_override.get("provider"))
        if api_key_override:
            user_llm_override["api_key"] = api_key_override
        
        user_context = ""
        stored_soul = get_user_soul(user_id)
        soul_events = list_soul_events(user_id, limit=20)
        if stored_soul:
            user_context = (stored_soul.get("markdown") or "").strip()
            if not user_context:
                user_context = _build_soul_markdown(stored_soul.get("data") or {}, soul_events).strip()
        elif soul_events:
            user_context = _build_soul_markdown({}, soul_events).strip()

        sec = _get_effective_security_settings(user_id)
        sys_ctx = _build_runtime_context_block(
            user_id=user_id,
            conversation_id=conversation_id,
            sec=sec,
            llm_override=user_llm_override
        )
        
        # Combinar contexto
        combined_context = f"{user_context}\n\n{sys_ctx}" if user_context else sys_ctx

        await websocket.send_json({"type": "status", "content": "Gerando resposta..."})

        # 5. Delegar para agent registry ou chamar LLM diretamente via WebSocket
        full_response = ""
        agent = agent_registry.get(expert.get("id"))
        if agent:
            try:
                async for chunk in agent.stream_execute(
                    intent=user_message,
                    context={"combined_context": combined_context, "expert": expert},
                ):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
            except Exception as e:
                logger.error(f"Erro no agent '{expert}': {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"Erro no agente {expert}: {str(e)}"
                })
                return
        else:
            try:
                async for chunk in llm_manager.stream_generate(
                    prompt=user_message,
                    expert=expert,
                    user_context=combined_context,
                    llm_override=user_llm_override,
                ):
                    if isinstance(chunk, str):
                        full_response += chunk
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk
                        })
            except Exception as e:
                logger.error(f"Erro na geração de LLM: {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"Erro interno do LLM: {str(e)}"
                })
                return

        # 6. Salvar resposta final do assistente no banco
        save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
            expert_id=expert.get("id"),
            provider=expert.get("provider"),
            model=expert.get("model")
        )

        # 7. Finalizar a geração e informar o cliente
        await websocket.send_json({
            "type": "done",
            "provider": expert.get("provider"),
            "model": expert.get("model")
        })

        # Incrementar step counter por sessão
        _step = self.session_steps.get(session_id, 0) + 1
        self.session_steps[session_id] = _step

        trace_logger.log(
            session_id=session_id,
            step=_step,
            harness={"model": expert.get("model", "gemini-2.5-flash")},
            input_data=user_message,
            output=full_response[:100] + "...",
            reward=0.0
        )

ws_orchestrator = WebSocketOrchestrator()
