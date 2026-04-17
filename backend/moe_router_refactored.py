"""
MoE Router Refatorado - Versão Modular
Roteamento baseado em keywords e LLM para seleção de especialistas
"""

import os
from typing import Dict, Any, List, Optional, AsyncGenerator

from .moe.experts import Expert, ExpertRegistry
from .moe.router import RoutingAlgorithm


class MoERouter:
    """Router de Mistura de Especialistas - Versão Refatorada e Modular"""

    def __init__(self, llm_manager=None):
        self.experts = ExpertRegistry.create_canonical_experts()
        self.routing_algorithm = RoutingAlgorithm(self.experts)
        self.llm_manager = llm_manager
        self.use_llm_routing = os.getenv("MOE_USE_LLM_ROUTING", "false").lower() == "true"

    async def select_expert(
        self,
        text: str,
        force_expert_id: Optional[str] = None,
        user_context: Optional[str] = None,
        use_llm: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Seleciona o especialista mais adequado para o texto.
        
        Args:
            text: Texto de entrada para análise
            force_expert_id: ID do especialista para forçar seleção
            user_context: Contexto adicional do usuário
            use_llm: Força uso ou não de LLM para seleção
        
        Returns:
            Dicionário com especialista selecionado e metadados
        """
        # Determina se deve usar LLM para seleção
        should_use_llm = use_llm if use_llm is not None else self.use_llm_routing
        
        if should_use_llm and self.llm_manager:
            return await self.routing_algorithm.select_expert_with_llm(
                text, force_expert_id, user_context, self.llm_manager
            )
        else:
            return self.routing_algorithm.select_expert_by_keywords(text, force_expert_id)

    def get_experts(self) -> List[Dict[str, Any]]:
        """Retorna todos os especialistas como dicionários"""
        return self.routing_algorithm.get_all_experts()

    def get_expert_by_id(self, expert_id: str) -> Optional[Dict[str, Any]]:
        """Retorna especialista por ID"""
        return self.routing_algorithm.get_expert_by_id(expert_id)

    def analyze_expert_selection(self, text: str) -> Dict[str, Any]:
        """Análise detalhada da seleção de especialista"""
        return self.routing_algorithm.analyze_expert_selection(text)

    def get_capabilities_catalog(self) -> str:
        """Retorna catálogo de capacidades dos especialistas"""
        return ExpertRegistry.get_capabilities_catalog(self.experts)

    def update_llm_manager(self, llm_manager) -> None:
        """Atualiza o gerenciador LLM usado para roteamento"""
        self.llm_manager = llm_manager

    def set_llm_routing_enabled(self, enabled: bool) -> None:
        """Habilita/desabilita roteamento via LLM"""
        self.use_llm_routing = enabled


# Instância global para compatibilidade
moe_router = MoERouter()

# Funções de conveniência para compatibilidade com código existente
def select_expert(text: str, force_expert_id: Optional[str] = None) -> Dict[str, Any]:
    """Seleciona especialista para texto (função síncrona de conveniência)"""
    return moe_router.routing_algorithm.select_expert_by_keywords(text, force_expert_id)

async def async_select_expert(
    text: str,
    force_expert_id: Optional[str] = None,
    *,
    user_context: Optional[str] = None,
    use_llm: Optional[bool] = None
) -> Dict[str, Any]:
    """Seleciona especialista de forma assíncrona (função de conveniência)"""
    return await moe_router.select_expert(
        text, force_expert_id, user_context, use_llm
    )

def get_experts() -> List[Dict[str, Any]]:
    """Retorna todos os especialistas (função de conveniência)"""
    return moe_router.get_experts()

def get_expert_by_id(expert_id: str) -> Optional[Dict[str, Any]]:
    """Retorna especialista por ID (função de conveniência)"""
    return moe_router.get_expert_by_id(expert_id)

def analyze_expert_selection(text: str) -> Dict[str, Any]:
    """Análise detalhada da seleção (função de conveniência)"""
    return moe_router.analyze_expert_selection(text)

def get_capabilities_catalog() -> str:
    """Retorna catálogo de capacidades (função de conveniência)"""
    return moe_router.get_capabilities_catalog()

# Funções de configuração
def set_llm_manager(llm_manager) -> None:
    """Define o gerenciador LLM para roteamento"""
    moe_router.update_llm_manager(llm_manager)

def enable_llm_routing(enabled: bool = True) -> None:
    """Habilita roteamento via LLM"""
    moe_router.set_llm_routing_enabled(enabled)
