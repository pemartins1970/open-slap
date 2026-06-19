import asyncio
import logging
import re
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
    list_soul_events,
    get_conversation_messages,
    rename_conversation_if_default,
)
from backend.runtime import moe_router, llm_manager
from backend.agents.base import agent_registry
from backend.chronicle import (
    append_chronicle_entry,
    append_chronicle_file,
    chronicle_search,
    close_any_open_session,
)
from backend.soul_extractor import extract_soul_fields, save_to_soul

logger = logging.getLogger(__name__)

class WebSocketOrchestrator:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_user_connections: Dict[str, WebSocket] = {}
        self.session_steps: Dict[str, int] = {}
        self.cancel_events: Dict[str, asyncio.Event] = {}

    async def cancel_orchestration(self, run_id: str) -> None:
        """Sinaliza cancelamento para uma orquestração em andamento."""
        event = self.cancel_events.get(run_id)
        if event:
            event.set()
            logger.info(f"Cancel signal sent for run {run_id}")

    async def handle_connection(self, websocket: WebSocket, session_id: str, current_user: Dict[str, Any]) -> None:
        """
        Aceita e gerencia o ciclo de vida de uma conexão WebSocket
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        user_id = str(current_user.get("id", ""))
        if user_id:
            self.active_user_connections[user_id] = websocket
        logger.info(f"WebSocket conectado: session_id={session_id}, user={user_id}")
        
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "chat")

                if msg_type == "cancel_orch":
                    run_id = data.get("run_id", "")
                    if run_id:
                        await self.cancel_orchestration(run_id)
                        await websocket.send_json({
                            "type": "cancel_ack",
                            "run_id": run_id,
                            "content": "Cancelamento solicitado."
                        })
                    continue

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
            if user_id and self.active_user_connections.get(user_id) is websocket:
                self.active_user_connections.pop(user_id, None)

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
            FileWriteBlockedError,
            _safe_llm_settings,
            _get_effective_security_settings,
            _build_runtime_context_block,
            _build_soul_markdown,
            _get_user_api_key,
            _extract_files_json,
            _write_files_bundle,
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
                # Chronicle: fechar sessão anterior quando cria-se nova conversa
                try:
                    close_any_open_session(exclude_conversation_id=conversation_id)
                except Exception as e:
                    logger.error("Chronicle close previous session failed: %s", e)

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

        # Chronicle: registrar entrada do usuário (infra — não propaga falha)
        try:
            append_chronicle_entry(conversation_id, "user", user_message)
        except Exception as e:
            logger.error("Chronicle user entry failed: %s", e)

        # SOUL: extrair perfil de mensagens do usuário (infra — não propaga falha)
        try:
            soul_fields = extract_soul_fields(user_message)
            if soul_fields:
                save_to_soul(user_id, soul_fields, user_message)
        except Exception as e:
            logger.error("SOUL extraction from user message failed: %s", e)

        # Enviar ACK do recebimento e status inicial
        client_message_id = data.get("client_message_id")
        if client_message_id:
            await websocket.send_json({
                "type": "user_ack",
                "client_message_id": client_message_id,
                "message": {"role": "user", "content": user_message}
            })

        await websocket.send_json({"type": "status", "content": "Sabrina está pensando..."})

        # 3. Selecionar especialista (expert)
        # Sabrina é a interface primária. MoE keyword routing só entra quando
        # force_expert_id aponta explicitamente para outro expert (plan execution,
        # seleção manual pelo usuário). 'general' e None sempre ficam com Sabrina.
        force_expert_id = data.get("force_expert_id")
        _routed_id = force_expert_id if (force_expert_id and force_expert_id != "general") else "general"
        expert = moe_router.select_expert(user_message, force_expert_id=_routed_id)
        
        # 4. Obter configurações do usuário e contexto do SOUL
        stored_llm = get_user_llm_settings(user_id)
        user_llm_override = _safe_llm_settings((stored_llm or {}).get("settings") or {})
        
        # Override session-only: provider + model do seletor do chat (maior prioridade)
        ws_provider = data.get("provider")
        ws_model = data.get("model")
        if ws_provider:
            user_llm_override["provider"] = str(ws_provider).strip().lower()
        if ws_model:
            user_llm_override["model"] = str(ws_model).strip()
        
        api_key_override = _get_user_api_key(user_id, user_llm_override.get("provider"))
        if api_key_override:
            user_llm_override["api_key"] = api_key_override
        
        # Propagar override para o done event (senão o header nunca reflete a troca)
        _active = await llm_manager.get_active_provider()
        _last_provider = user_llm_override.get("provider") or _active.get("provider")
        _last_model = user_llm_override.get("model") or _active.get("model")
        
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
        
        # Combinar contexto (internal_prompt do frontend, se houver, fica no topo)
        internal_prompt = (data.get("internal_prompt") or "").strip()
        combined_context = "\n\n".join(filter(None, [internal_prompt, user_context, sys_ctx]))

        # Chronic trigger: buscar histórico se mensagem contiver palavra-chave
        try:
            historic = _check_chronicle_trigger(user_message, conversation_id)
            if historic:
                combined_context = f"{combined_context}\n\n# Histórico de conversas anteriores\n{historic}"
        except Exception as e:
            logger.error("Chronic trigger failed: %s", e)

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
                stream = llm_manager.stream_generate(
                    prompt=user_message,
                    expert=expert,
                    user_context=combined_context,
                    llm_override=user_llm_override,
                    conversation_id=conversation_id,
                )
                async for chunk in stream:
                    if isinstance(chunk, dict):
                        _last_provider = chunk.get("provider") or _last_provider
                        _last_model = chunk.get("model") or _last_model
                    elif isinstance(chunk, str):
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

        # 5b. Interceptar <FILES_JSON> — persistir em disco se presente
        try:
            sec_write = _get_effective_security_settings(user_id)
            if bool(sec_write.get("allow_file_write")):
                bundle = _extract_files_json(full_response)
                if bundle:
                    res = _write_files_bundle(bundle)
                    created = res.get("written") or []
                    if created:
                        await websocket.send_json({
                            "type": "files_written",
                            "files": created,
                            "count": len(created)
                        })
                        logger.info(
                            f"[B-05] FILES_JSON processado via chat direto: "
                            f"{len(created)} arquivo(s) em {bundle.get('base_path')}"
                        )
                        # Chronicle: registrar arquivos escritos (infra — não propaga falha)
                        try:
                            for file_entry in created:
                                append_chronicle_file(
                                    conversation_id,
                                    file_entry if isinstance(file_entry, str) else file_entry.get("path", str(file_entry)),
                                    "write",
                                )
                        except Exception as _ce:
                            logger.error("Chronicle file write failed: %s", _ce)
        except FileWriteBlockedError as _be:
            error_msg = f"B.E.N. 2.0 bloqueou escrita: {_be}"
            logger.warning(f"[B-05/H-01] {error_msg}")
            await websocket.send_json({
                "type": "error",
                "content": error_msg
            })
        except Exception as _fe:
            logger.warning(f"[B-05] Erro ao processar FILES_JSON no chat direto: {_fe}")

        # 6. Salvar resposta final do assistente no banco
        save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
            expert_id=expert.get("id"),
            provider=_last_provider or expert.get("provider"),
            model=_last_model or expert.get("model")
        )

        # Chronicle: registrar resposta do assistant (infra — não propaga falha)
        try:
            append_chronicle_entry(conversation_id, "assistant", full_response)
        except Exception as e:
            logger.error("Chronicle assistant entry failed: %s", e)

        # SOUL: extrair perfil de respostas do assistant (infra — não propaga falha)
        try:
            soul_fields = extract_soul_fields(full_response)
            if soul_fields:
                save_to_soul(user_id, soul_fields, full_response)
        except Exception as e:
            logger.error("SOUL extraction from assistant response failed: %s", e)

        # B-07: Auto-rename na primeira resposta do assistant
        try:
            all_msgs = get_conversation_messages(conversation_id)
            assistant_msgs = [m for m in all_msgs if m.get("role") == "assistant"]
            if len(assistant_msgs) == 1:
                first_user_msg = next(
                    (m.get("content", "") for m in all_msgs if m.get("role") == "user"),
                    ""
                )
                default_title = first_user_msg[:50]
                new_title = _generate_conversation_title(first_user_msg)
                if rename_conversation_if_default(conversation_id, user_id, new_title, default_title):
                    await websocket.send_json({
                        "type": "conversation_renamed",
                        "conversation_id": conversation_id,
                        "title": new_title,
                    })
        except Exception as exc:
            logger.warning(f"[B-07] Erro ao renomear conversa: {exc}")

        # 7. Finalizar a geração e informar o cliente
        await websocket.send_json({
            "type": "done",
            "provider": _last_provider or expert.get("provider"),
            "model": _last_model or expert.get("model")
        })

        # Incrementar step counter por sessão
        _step = self.session_steps.get(session_id, 0) + 1
        self.session_steps[session_id] = _step

        trace_logger.log(
            session_id=session_id,
            step=_step,
            harness={"model": _last_model or expert.get("model", "gemini-2.5-flash")},
            input_data=user_message,
            output=full_response[:100] + "...",
            reward=0.0
        )

def _generate_conversation_title(first_user_message: str) -> str:
    clean = " ".join(first_user_message.strip().split())
    if len(clean) <= 60:
        return clean
    return clean[:60].rstrip() + "\u2026"


# --- Chronic trigger keywords (M-06) ---
_CHRONIC_TRIGGER_PATTERNS = [
    re.compile(r"\blembra\b", re.IGNORECASE),
    re.compile(r"\blembrete\b", re.IGNORECASE),
    re.compile(r"\banterior(?:mente)?\b", re.IGNORECASE),
    re.compile(r"\bsemana passada\b", re.IGNORECASE),
    re.compile(r"\bsess[ãa]o passada\b", re.IGNORECASE),
    re.compile(r"\b[uú]ltima vez\b", re.IGNORECASE),
    re.compile(r"\bcomo discutimos\b", re.IGNORECASE),
    re.compile(r"\bvoc[êe] disse\b", re.IGNORECASE),
    re.compile(r"\bremember\b", re.IGNORECASE),
    re.compile(r"\bprevious\b", re.IGNORECASE),
    re.compile(r"\byesterday\b", re.IGNORECASE),
    re.compile(r"\blast time\b", re.IGNORECASE),
    re.compile(r"\bas discussed\b", re.IGNORECASE),
    re.compile(r"\byou said\b", re.IGNORECASE),
    re.compile(r"\brecuerda\b", re.IGNORECASE),
    re.compile(r"\bayer\b", re.IGNORECASE),
    re.compile(r"\bdijiste\b", re.IGNORECASE),
    re.compile(r"\bcomo discutimos\b", re.IGNORECASE),
]

_CHRONIC_TRIGGER_SUBSTR = [
    # Árabe (MSA)
    "\u062A\u0630\u0643\u0631",       # تذكر
    "\u0633\u0627\u0628\u0642",        # سابق
    "\u0627\u0644\u0623\u0645\u0633",  # الأمس
    "\u0622\u062E\u0631 \u0645\u0631\u0629",  # آخر مرة
    "\u0643\u0645\u0627 \u0646\u0627\u0642\u0634\u0646\u0627",  # كما ناقشنا
    "\u0642\u0644\u062A",              # قلت
    # Chinês (Mandarim)
    "\u8BB0\u5F97",                    # 记得
    "\u4E4B\u524D",                    # 之前
    "\u6628\u5929",                    # 昨天
    "\u4E0A\u6B21",                    # 上次
    "\u6211\u4EEC\u8BA8\u8BBA\u8FC7", # 我们讨论过
    "\u4F60\u8BF4\u8FC7",             # 你说过
]


def _check_chronicle_trigger(user_message: str, conversation_id: int) -> str:
    """Check user message for chronicle trigger keywords and return formatted history."""
    for pat in _CHRONIC_TRIGGER_PATTERNS:
        if pat.search(user_message):
            break
    else:
        for kw in _CHRONIC_TRIGGER_SUBSTR:
            if kw in user_message:
                break
        else:
            return ""

    results = chronicle_search(user_message, limit=5)
    if not results:
        return ""

    lines: List[str] = []
    for r in results:
        rid = r.get("conversation_id", "")
        role = r.get("role", "user")
        content = r.get("content", "")[:400]
        created = r.get("created_at", "")[:16]
        lines.append(f"- [{created}] ({role}, conv#{rid}): {content}")
    return "\n".join(lines)


ws_orchestrator = WebSocketOrchestrator()
