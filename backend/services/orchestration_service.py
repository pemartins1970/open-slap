"""
🎯 Orchestration Service - Serviço isolado de orquestração de tarefas
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from ..db import (
    get_plan_tasks,
    update_plan_task_status,
    update_orchestration_run,
    create_conversation,
    save_message,
    get_user_llm_settings,
    get_user_soul,
    list_soul_events,
    _build_soul_markdown,
    upsert_user_soul
)
from ..runtime import moe_router, llm_manager
from ..main_auth import (
    _safe_llm_settings,
    _get_effective_security_settings,
    _run_external_software_skill
)

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Serviço de orquestração isolado e resiliente"""
    
    def __init__(self):
        self.failure_patterns = {}
        self.recovery_strategies = {}
        self.circuit_breakers = {}
    
    async def execute_orchestration(
        self,
        run_id: int,
        user_id: int,
        parent_conversation_id: int,
        user_llm_override: Dict[str, Any],
        websocket: Optional[Callable] = None,
    ) -> None:
        """
        Executa orquestração completa com self-healing
        """
        log: List[Dict[str, Any]] = []
        
        def _log(task_id, status, msg):
            log.append({"task_id": task_id, "status": status, "msg": msg})
            try:
                update_orchestration_run(run_id, "running", log)
            except Exception:
                pass
        
        async def _send_status(text: str) -> None:
            if not websocket:
                return
            try:
                await websocket({"type": "status", "content": str(text or "")})
            except Exception:
                return
        
        try:
            # Obter tarefas pendentes
            tasks = get_plan_tasks(parent_conversation_id)
            pending = [t for t in tasks if t.get("status") in ("pending", "active")]
            
            # Ordenar prioridades (software_operator primeiro)
            try:
                pending.sort(
                    key=lambda x: 0
                    if str(x.get("skill_id") or "").strip().lower() == "software_operator"
                    else 1
                )
            except Exception:
                pass
            
            _log(0, "started", f"Orquestração iniciada com {len(pending)} tarefas")
            await _send_status(f"🚀 Iniciando orquestração com {len(pending)} tarefas")
            
            # Processar cada tarefa
            for i, task in enumerate(pending):
                task_id = task.get("id")
                title = task.get("title", f"Tarefa {i+1}")
                skill_id = task.get("skill_id")
                
                try:
                    _log(task_id, "active", f"Executando: {title}")
                    await _send_status(f"📋 {i+1}/{len(pending)} - {title}")
                    
                    # Executar tarefa com self-healing
                    result = await self._execute_task_with_healing(
                        task, user_id, parent_conversation_id, 
                        user_llm_override, websocket, _send_status
                    )
                    
                    if result["success"]:
                        _log(task_id, "done", f"Concluída: {title}")
                        await _send_status(f"✅ {title} concluída")
                    else:
                        _log(task_id, "failed", f"Falha: {title} - {result['error']}")
                        await _send_status(f"❌ Falha em {title}: {result['error']}")
                        
                except Exception as e:
                    _log(task_id, "error", f"Erro crítico: {title} - {str(e)}")
                    await _send_status(f"🔥 Erro crítico em {title}")
                    logger.error(f"Task execution failed: {title}", exc_info=True)
            
            # Marcar orquestração como concluída
            update_orchestration_run(run_id, "completed", log)
            await _send_status("🎉 Orquestração concluída com sucesso!")
            
        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
            update_orchestration_run(run_id, "failed", log)
            await _send_status("💥 Orquestração falhou!")
    
    async def _execute_task_with_healing(
        self,
        task: Dict[str, Any],
        user_id: int,
        parent_conversation_id: int,
        user_llm_override: Dict[str, Any],
        websocket: Optional[Callable],
        _send_status: Callable
    ) -> Dict[str, Any]:
        """
        Executa tarefa individual com estratégias de recuperação
        """
        task_id = task.get("id")
        title = task.get("title", "Tarefa sem título")
        skill_id = task.get("skill_id")
        
        try:
            # Estratégia 1: Execução normal
            result = await self._execute_task_normal(
                task, user_id, parent_conversation_id, user_llm_override
            )
            if result["success"]:
                return result
            
            # Estratégia 2: Retry com backoff
            await _send_status(f"🔄 Tentando novamente: {title}")
            await asyncio.sleep(2)  # Backoff inicial
            
            result = await self._execute_task_normal(
                task, user_id, parent_conversation_id, user_llm_override
            )
            if result["success"]:
                return result
            
            # Estratégia 3: Fallback para general skill
            if skill_id and skill_id != "general":
                await _send_status(f"🔧 Usando skill general: {title}")
                task["skill_id"] = "general"
                result = await self._execute_task_normal(
                    task, user_id, parent_conversation_id, user_llm_override
                )
                if result["success"]:
                    return result
            
            # Estratégia 4: Marcar como failed com contexto
            return {
                "success": False,
                "error": "Todas as estratégias de recuperação falharam",
                "task_id": task_id,
                "title": title
            }
            
        except Exception as e:
            logger.error(f"Task execution error: {title}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "title": title
            }
    
    async def _execute_task_normal(
        self,
        task: Dict[str, Any],
        user_id: int,
        parent_conversation_id: int,
        user_llm_override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execução normal da tarefa (extraída do main_auth.py)
        """
        task_id = task.get("id")
        title = task.get("title", "Tarefa sem título")
        skill_id = task.get("skill_id")
        
        try:
            # Criar sub-conversação para a tarefa
            sub_conv_id = create_conversation(
                user_id,
                f"task_{task_id}",
                f"📋 {title}",
                kind="task",
            )
            
            # Obter contexto do usuário
            user_context = await self._build_user_context(user_id)
            
            # Obter LLM settings
            stored_llm = get_user_llm_settings(user_id)
            llm_override = _safe_llm_settings(
                (stored_llm or {}).get("settings") or {}
            )
            
            # Selecionar expert
            expert = await moe_router.select_expert_llm_first(
                title, force_expert_id=skill_id, llm_override=llm_override
            )
            
            # Compor prompt da tarefa
            prompt = self._compose_task_prompt(title, task, user_context)
            
            # Executar LLM (non-streaming para orquestração)
            full_response = ""
            expert_info = None
            async for chunk in llm_manager.stream_generate(
                prompt,
                expert,
                user_context=user_context,
                llm_override=llm_override,
            ):
                if isinstance(chunk, str):
                    full_response += chunk
                else:
                    expert_info = chunk
            
            # Salvar resposta
            persisted_response = full_response.strip()
            if persisted_response:
                save_message(
                    sub_conv_id,
                    "assistant",
                    persisted_response,
                    expert_id=(expert_info or {}).get("id")
                    if isinstance(expert_info, dict)
                    else None,
                    provider=(expert_info or {}).get("provider")
                    if isinstance(expert_info, dict)
                    else None,
                    model=(expert_info or {}).get("model")
                    if isinstance(expert_info, dict)
                    else None,
                    tokens=(expert_info or {}).get("tokens")
                    if isinstance(expert_info, dict)
                    else None,
                )
            
            # Marcar tarefa como concluída
            update_plan_task_status(task_id, "done")
            
            # Handle software_operator se aplicável
            if (
                persisted_response.strip()
                and expert
                and str(expert.get("id") or "").strip().lower() == "software_operator"
            ):
                await self._handle_software_operator(
                    persisted_response, user_id, sub_conv_id, expert, 
                    user_llm_override, user_context
                )
            
            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "response": persisted_response,
                "conversation_id": sub_conv_id
            }
            
        except Exception as e:
            update_plan_task_status(task_id, "failed")
            raise e
    
    async def _build_user_context(self, user_id: int) -> str:
        """Constrói contexto do usuário (soul + system profile)"""
        try:
            user_context = ""
            
            # Obter soul
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
            
            return user_context
            
        except Exception as e:
            logger.error(f"Error building user context: {str(e)}")
            return ""
    
    def _compose_task_prompt(
        self, 
        title: str, 
        task: Dict[str, Any], 
        user_context: str
    ) -> str:
        """Compõe o prompt para execução da tarefa"""
        
        prompt = (
            f"You are executing task: {title}\n\n"
            f"This task is part of a larger project plan. "
            f"Focus on delivering high-quality work for this specific task.\n\n"
        )
        
        # Adicionar contexto do usuário se disponível
        if user_context.strip():
            prompt += f"User Context:\n{user_context}\n\n"
        
        # Adicionar descrição da tarefa se disponível
        description = task.get("description", "")
        if description.strip():
            prompt += f"Task Description:\n{description}\n\n"
        
        # Adicionar instruções específicas
        prompt += (
            "Please execute this task efficiently and provide a complete, "
            "working solution. Focus on quality and correctness."
        )
        
        return prompt
    
    async def _handle_software_operator(
        self,
        full_response: str,
        user_id: int,
        conversation_id: int,
        expert: Dict[str, Any],
        llm_override: Dict[str, Any],
        user_context: str
    ) -> None:
        """Handle especial para software_operator"""
        try:
            sec = _get_effective_security_settings(user_id)
            
            # Executar comando externo
            result = await _run_external_software_skill(
                command_text=full_response,
                user_id=user_id,
                conversation_id=conversation_id,
                sec=sec,
                expert=expert,
                llm_override=llm_override,
                user_context=user_context,
                websocket=None,  # Não temos websocket no service
            )
            
            # Salvar resultado da execução
            if result.get("output"):
                save_message(
                    conversation_id,
                    "assistant",
                    f"Executado:\n{result['output']}",
                    expert_id=expert.get("id")
                )
                
        except Exception as e:
            logger.error(f"Software operator error: {str(e)}")
            save_message(
                conversation_id,
                "assistant",
                f"Erro na execução: {str(e)}",
                expert_id=expert.get("id")
            )


# Instância global do serviço
orchestration_service = OrchestrationService()


# Funções de compatibilidade com código existente
async def run_orchestration(
    run_id: int,
    user_id: int,
    parent_conversation_id: int,
    user_llm_override: Dict[str, Any],
    websocket: Optional[Any] = None,
) -> None:
    """Função wrapper para compatibilidade"""
    await orchestration_service.execute_orchestration(
        run_id, user_id, parent_conversation_id, user_llm_override, websocket
    )
