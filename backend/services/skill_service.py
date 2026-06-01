"""
🎯 Skill Service - Serviço isolado de gestão de skills e experts
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from ..db import (
    get_user_skills,
    upsert_user_skills,
    get_expert_rating_summary,
    record_expert_rating,
    get_user_llm_settings
)
from ..runtime import moe_router

logger = logging.getLogger(__name__)


class SkillService:
    """Serviço de gestão de skills com evolução adaptativa"""
    
    def __init__(self):
        self.skill_cache = {}
        self.performance_tracker = {}
        self.skill_registry = self._load_builtin_skills()
        self.mcp_registry = {}  # Registry de MCPs dinâmicos
        
    def _load_builtin_skills(self) -> Dict[str, Any]:
        """
        Carrega skills built-in do sistema
        """
        return {
            "systems-architect": {
                "id": "systems-architect",
                "name": "Systems Architect",
                "description": "Designs complex systems and architectures",
                "capabilities": ["system_design", "architecture", "technical_analysis"],
                "expertise_level": 0.9,
                "category": "technical"
            },
            "backend-dev": {
                "id": "backend-dev",
                "name": "Backend Developer",
                "description": "Develops backend systems and APIs",
                "capabilities": ["api_design", "database", "backend_logic"],
                "expertise_level": 0.8,
                "category": "technical"
            },
            "frontend-dev": {
                "id": "frontend-dev",
                "name": "Frontend Developer",
                "description": "Develops user interfaces and frontend applications",
                "capabilities": ["ui_design", "frontend_logic", "user_experience"],
                "expertise_level": 0.8,
                "category": "technical"
            },
            "data-analyst": {
                "id": "data-analyst",
                "name": "Data Analyst",
                "description": "Analyzes data and provides insights",
                "capabilities": ["data_analysis", "statistics", "visualization"],
                "expertise_level": 0.7,
                "category": "analytical"
            },
            "project-manager": {
                "id": "project-manager",
                "name": "Project Manager",
                "description": "Manages projects and coordinates teams",
                "capabilities": ["planning", "coordination", "resource_management"],
                "expertise_level": 0.7,
                "category": "management"
            },
            "creative-writer": {
                "id": "creative-writer",
                "name": "Creative Writer",
                "description": "Creates creative content and documentation",
                "capabilities": ["writing", "creativity", "documentation"],
                "expertise_level": 0.8,
                "category": "creative"
            },
            "researcher": {
                "id": "researcher",
                "name": "Researcher",
                "description": "Conducts research and gathers information",
                "capabilities": ["research", "information_gathering", "analysis"],
                "expertise_level": 0.7,
                "category": "research"
            },
            "general": {
                "id": "general",
                "name": "General Assistant",
                "description": "General purpose assistant for various tasks",
                "capabilities": ["general_knowledge", "problem_solving", "communication"],
                "expertise_level": 0.6,
                "category": "general"
            },
            "software-operator": {
                "id": "software-operator",
                "name": "Software Operator",
                "description": "Executes software commands and operations",
                "capabilities": ["command_execution", "system_operations", "automation"],
                "expertise_level": 0.9,
                "category": "technical"
            }
        }
    
    async def load_user_mcps(self, user_id: int) -> None:
        """
        Carrega MCPs ativos do usuário e os integra ao registry
        Não bloqueia se endpoints estiverem fora do ar
        """
        try:
            from .mcp_service import get_user_mcps
            import aiohttp
            import asyncio
            
            # Obter MCPs ativos do usuário
            active_mcps = await get_user_mcps(user_id, active_only=True)
            
            # Limpar registry antigo do usuário
            user_prefix = f"user_{user_id}_"
            keys_to_remove = [k for k in self.mcp_registry.keys() if k.startswith(user_prefix)]
            for key in keys_to_remove:
                del self.mcp_registry[key]
            
            # Adicionar MCPs ativos ao registry (com timeout para não bloquear)
            loaded_count = 0
            failed_count = 0
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                tasks = []
                
                for mcp in active_mcps:
                    manifest = mcp.get("manifest", {})
                    mcp_id = mcp.get("id")
                    
                    if mcp_id and manifest:
                        # Converter MCP para formato de skill
                        skill_id = f"user_{user_id}_{mcp_id}"
                        
                        skill_data = {
                            "id": skill_id,
                            "name": manifest.get("name", mcp_id),
                            "description": manifest.get("description", f"MCP: {mcp_id}"),
                            "capabilities": manifest.get("tools", []) + manifest.get("agents", []),
                            "expertise_level": 0.8,  # MCPs geralmente têm bom nível de expertise
                            "category": manifest.get("category", "custom"),
                            "mcp_id": mcp_id,
                            "mcp_manifest": manifest,
                            "mcp_endpoint": manifest.get("endpoint"),
                            "mcp_auth": manifest.get("auth"),
                            "is_mcp": True,
                            "user_id": user_id,
                            "endpoint_status": "unknown"  # Será atualizado após verificação
                        }
                        
                        # Adicionar ao registry imediatamente
                        self.mcp_registry[skill_id] = skill_data
                        
                        # Verificar endpoint em background (não bloqueia)
                        endpoint = manifest.get("endpoint")
                        if endpoint:
                            task = self._verify_mcp_endpoint(session, skill_id, endpoint)
                            tasks.append(task)
                        else:
                            skill_data["endpoint_status"] = "no_endpoint"
                        
                        loaded_count += 1
                
                # Executar verificações de endpoint em paralelo com timeout
                if tasks:
                    try:
                        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=30)
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout na verificação de endpoints para usuário {user_id}")
            
            logger.info(f"Carregados {loaded_count} MCPs para usuário {user_id} ({failed_count} com problemas)")
            
        except Exception as e:
            logger.error(f"Erro ao carregar MCPs do usuário {user_id}: {str(e)}")
    
    async def _verify_mcp_endpoint(self, session, skill_id: str, endpoint: str) -> None:
        """
        Verifica se endpoint MCP está respondendo (não bloqueante)
        """
        try:
            if skill_id not in self.mcp_registry:
                return
                
            async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    self.mcp_registry[skill_id]["endpoint_status"] = "online"
                else:
                    self.mcp_registry[skill_id]["endpoint_status"] = f"error_{response.status}"
                    
        except asyncio.TimeoutError:
            if skill_id in self.mcp_registry:
                self.mcp_registry[skill_id]["endpoint_status"] = "timeout"
        except Exception as e:
            if skill_id in self.mcp_registry:
                self.mcp_registry[skill_id]["endpoint_status"] = "offline"
            logger.debug(f"Endpoint {endpoint} offline para MCP {skill_id}: {str(e)}")
    
    async def get_user_skills(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtém skills do usuário com cache e metadados (incluindo MCPs dinâmicos)
        """
        try:
            # Verificar cache
            if user_id in self.skill_cache:
                cache_entry = self.skill_cache[user_id]
                if (datetime.utcnow() - cache_entry["cached_at"]).seconds < 300:  # 5 min
                    return cache_entry["skills"]
            
            # Garantir que MCPs do usuário estão carregados
            await self.load_user_mcps(user_id)
            
            # Obter skills do banco
            user_skills = get_user_skills(user_id) or []
            
            # Enriquecer com metadados do registry (built-in + MCPs)
            enriched_skills = []
            all_registry = {**self.skill_registry, **self.mcp_registry}
            
            for skill in user_skills:
                skill_id = skill.get("id")
                if skill_id in all_registry:
                    registry_skill = all_registry[skill_id].copy()
                    registry_skill.update(skill)  # Override com dados do usuário
                    enriched_skills.append(registry_skill)
                else:
                    # Skill customizado do usuário
                    enriched_skills.append({
                        "id": skill_id,
                        "name": skill.get("name", skill_id),
                        "description": skill.get("description", ""),
                        "capabilities": skill.get("capabilities", []),
                        "expertise_level": skill.get("expertise_level", 0.5),
                        "category": skill.get("category", "custom"),
                        "custom": True
                    })
            
            # Adicionar MCPs ativos que não estão no skills do usuário (auto-instalação)
            user_prefix = f"user_{user_id}_"
            for skill_id, mcp_skill in self.mcp_registry.items():
                if skill_id.startswith(user_prefix) and not any(s.get("id") == skill_id for s in enriched_skills):
                    # MCP não está no skills do usuário, adicionar como disponível
                    enriched_skills.append({
                        **mcp_skill,
                        "auto_installed": True,
                        "enabled": True  # MCPs ativos são enabled por padrão
                    })
            
            # Cache para próximas consultas
            self.skill_cache[user_id] = {
                "skills": enriched_skills,
                "cached_at": datetime.utcnow()
            }
            
            return enriched_skills
            
        except Exception as e:
            logger.error(f"Error getting user skills: {str(e)}")
            return []
    
    async def update_user_skills(
        self,
        user_id: int,
        skills: List[Union[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Atualiza skills do usuário com validação
        """
        try:
            # Validar e normalizar skills
            normalized_skills = []
            
            for skill in skills:
                if isinstance(skill, str):
                    # Referência por ID
                    if skill in self.skill_registry:
                        normalized_skills.append(self.skill_registry[skill])
                    else:
                        # Criar skill básico
                        normalized_skills.append({
                            "id": skill,
                            "name": skill,
                            "description": f"Skill: {skill}",
                            "capabilities": [],
                            "expertise_level": 0.5,
                            "category": "custom"
                        })
                elif isinstance(skill, dict):
                    # Skill completo
                    skill_id = skill.get("id")
                    if skill_id in self.skill_registry:
                        # Complementar com dados do built-in
                        builtin = self.skill_registry[skill_id].copy()
                        builtin.update(skill)
                        normalized_skills.append(builtin)
                    else:
                        # Skill customizado
                        normalized_skills.append(skill)
            
            # Salvar no banco
            upsert_user_skills(user_id, normalized_skills)
            
            # Invalidar cache
            if user_id in self.skill_cache:
                del self.skill_cache[user_id]
            
            logger.info(f"Updated {len(normalized_skills)} skills for user {user_id}")
            
            return {
                "success": True,
                "updated": len(normalized_skills),
                "skills": normalized_skills
            }
            
        except Exception as e:
            logger.error(f"Error updating user skills: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "updated": 0
            }
    
    async def get_skill_recommendations(
        self,
        user_id: int,
        context: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recomenda skills baseado em contexto e histórico
        """
        try:
            # Obter skills atuais do usuário
            current_skills = await self.get_user_skills(user_id)
            current_skill_ids = {skill.get("id") for skill in current_skills}
            
            # Obter ratings de experts
            expert_ratings = get_expert_rating_summary(user_id) or {}
            
            # Analisar contexto para identificar necessidades
            context_lower = (context or "").lower()
            recommendations = []
            
            # Mapeamento de palavras-chave para skills
            keyword_to_skills = {
                # Technical
                "arquitetura": ["systems-architect"],
                "sistema": ["systems-architect", "backend-dev"],
                "api": ["backend-dev", "frontend-dev"],
                "banco de dados": ["backend-dev"],
                "interface": ["frontend-dev"],
                
                # Analytical
                "análise": ["data-analyst"],
                "dados": ["data-analyst"],
                "estatística": ["data-analyst"],
                
                # Management
                "projeto": ["project-manager"],
                "gerenciar": ["project-manager"],
                "equipe": ["project-manager"],
                
                # Creative
                "criar": ["creative-writer"],
                "escrever": ["creative-writer"],
                "conteúdo": ["creative-writer"],
                
                # Research
                "pesquisar": ["researcher"],
                "informação": ["researcher"],
                "estudar": ["researcher"]
            }
            
            # Encontrar skills relevantes para o contexto
            for keyword, skill_ids in keyword_to_skills.items():
                if keyword in context_lower:
                    for skill_id in skill_ids:
                        if skill_id not in current_skill_ids:
                            skill_data = self.skill_registry.get(skill_id)
                            if skill_data:
                                # Calcular score de recomendação
                                score = self._calculate_recommendation_score(
                                    skill_data, expert_ratings, context
                                )
                                recommendations.append({
                                    **skill_data,
                                    "recommendation_score": score,
                                    "reason": f"Contexto menciona '{keyword}'"
                                })
            
            # Adicionar skills populares se não houver recomendações específicas
            if not recommendations:
                popular_skills = ["systems-architect", "backend-dev", "data-analyst"]
                for skill_id in popular_skills:
                    if skill_id not in current_skill_ids:
                        skill_data = self.skill_registry.get(skill_id)
                        if skill_data:
                            score = self._calculate_recommendation_score(
                                skill_data, expert_ratings, context
                            )
                            recommendations.append({
                                **skill_data,
                                "recommendation_score": score,
                                "reason": "Skill popular e versátil"
                            })
            
            # Ordenar por score e limitar
            recommendations.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting skill recommendations: {str(e)}")
            return []
    
    async def rate_expert_performance(
        self,
        user_id: int,
        expert_id: str,
        task_id: Optional[str],
        rating: float,  # 0.0 a 1.0
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Regra performance de expert e atualiza modelo
        """
        try:
            # Validar rating
            if not 0.0 <= rating <= 1.0:
                return {
                    "success": False,
                    "error": "Rating must be between 0.0 and 1.0"
                }
            
            # Registrar no banco
            record_expert_rating(user_id, expert_id, rating)
            
            # Atualizar performance tracker
            if expert_id not in self.performance_tracker:
                self.performance_tracker[expert_id] = {
                    "ratings": [],
                    "average_rating": 0.0,
                    "task_count": 0,
                    "last_updated": datetime.utcnow()
                }
            
            tracker = self.performance_tracker[expert_id]
            tracker["ratings"].append({
                "rating": rating,
                "task_id": task_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow()
            })
            
            # Manter apenas últimas 50 avaliações
            if len(tracker["ratings"]) > 50:
                tracker["ratings"] = tracker["ratings"][-50:]
            
            # Recalcular média
            tracker["average_rating"] = sum(r["rating"] for r in tracker["ratings"]) / len(tracker["ratings"])
            tracker["task_count"] += 1
            tracker["last_updated"] = datetime.utcnow()
            
            # Ajustar expertise level baseado em performance
            await self._adjust_expertise_level(expert_id, tracker["average_rating"])
            
            logger.info(f"Rated expert {expert_id}: {rating} (avg: {tracker['average_rating']:.2f})")
            
            return {
                "success": True,
                "expert_id": expert_id,
                "rating": rating,
                "average_rating": tracker["average_rating"],
                "total_ratings": len(tracker["ratings"])
            }
            
        except Exception as e:
            logger.error(f"Error rating expert: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_recommendation_score(
        self,
        skill: Dict[str, Any],
        expert_ratings: Dict[str, Dict[str, Any]],
        context: str
    ) -> float:
        """
        Calcula score de recomendação para uma skill
        """
        try:
            score = 0.0
            skill_id = skill.get("id")
            
            # Fator 1: Performance histórica (40%)
            if skill_id in expert_ratings:
                avg_rating = expert_ratings[skill_id].get("average_rating", 0.5)
                score += avg_rating * 0.4
            
            # Fator 2: Expertise level da skill (30%)
            expertise = skill.get("expertise_level", 0.5)
            score += expertise * 0.3
            
            # Fator 3: Versatilidade (número de capabilities) (20%)
            capabilities = skill.get("capabilities", [])
            versatility_score = min(len(capabilities) / 5.0, 1.0)  # Normalizado para 0-1
            score += versatility_score * 0.2
            
            # Fator 4: Relevância de categoria (10%)
            category = skill.get("category", "general")
            context_lower = context.lower()
            
            category_relevance = {
                "technical": 0.9,
                "analytical": 0.8,
                "management": 0.7,
                "creative": 0.7,
                "research": 0.6,
                "general": 0.5
            }
            
            # Boost se palavras-chave da categoria aparecem no contexto
            category_keywords = {
                "technical": ["técnico", "sistema", "api", "código"],
                "analytical": ["análise", "dados", "estatística"],
                "management": ["projeto", "gerenciar", "equipe"],
                "creative": ["criar", "conteúdo", "escrever"],
                "research": ["pesquisar", "informação", "estudo"]
            }
            
            if category in category_keywords:
                keywords = category_keywords[category]
                if any(keyword in context_lower for keyword in keywords):
                    score += 0.1
                else:
                    score += category_relevance.get(category, 0.5) * 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5
    
    async def _adjust_expertise_level(
        self,
        expert_id: str,
        average_rating: float
    ) -> None:
        """
        Ajusta expertise level baseado em performance contínua
        """
        try:
            if expert_id not in self.skill_registry:
                return
            
            current_level = self.skill_registry[expert_id].get("expertise_level", 0.5)
            
            # Ajuste baseado em rating
            if average_rating > 0.8:
                # Performance excelente - aumentar expertise
                new_level = min(current_level + 0.05, 1.0)
            elif average_rating < 0.3:
                # Performance ruim - diminuir expertise
                new_level = max(current_level - 0.05, 0.1)
            else:
                # Performance razoável - ajuste menor
                new_level = current_level + (average_rating - 0.5) * 0.1
            
            # Atualizar no registry
            self.skill_registry[expert_id]["expertise_level"] = max(0.1, min(1.0, new_level))
            
            logger.info(f"Adjusted expertise level for {expert_id}: {current_level:.2f} → {new_level:.2f}")
            
        except Exception as e:
            logger.error(f"Error adjusting expertise level: {str(e)}")
    
    async def get_skill_analytics(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Retorna analytics detalhadas dos skills do usuário
        """
        try:
            user_skills = await self.get_user_skills(user_id)
            
            # Estatísticas básicas
            total_skills = len(user_skills)
            custom_skills = len([s for s in user_skills if s.get("custom", False)])
            builtin_skills = total_skills - custom_skills
            
            # Análise por categoria
            categories = {}
            for skill in user_skills:
                category = skill.get("category", "unknown")
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            # Expertise levels
            expertise_levels = [s.get("expertise_level", 0.5) for s in user_skills]
            avg_expertise = sum(expertise_levels) / len(expertise_levels) if expertise_levels else 0
            
            # Performance por expert
            expert_performance = {}
            for skill in user_skills:
                skill_id = skill.get("id")
                if skill_id in self.performance_tracker:
                    tracker = self.performance_tracker[skill_id]
                    expert_performance[skill_id] = {
                        "average_rating": tracker.get("average_rating", 0.5),
                        "total_ratings": len(tracker.get("ratings", [])),
                        "task_count": tracker.get("task_count", 0)
                    }
            
            return {
                "total_skills": total_skills,
                "custom_skills": custom_skills,
                "builtin_skills": builtin_skills,
                "categories": categories,
                "average_expertise": avg_expertise,
                "expert_performance": expert_performance,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting skill analytics: {str(e)}")
            return {"error": str(e)}


# Instância global do serviço
skill_service = SkillService()


# Funções de compatibilidade com código existente
async def get_user_skills_service(user_id: int) -> List[Dict[str, Any]]:
    """Função wrapper para compatibilidade"""
    return await skill_service.get_user_skills(user_id)


async def update_user_skills_service(
    user_id: int,
    skills: List[Union[str, Dict[str, Any]]]
) -> Dict[str, Any]:
    """Função wrapper para compatibilidade"""
    return await skill_service.update_user_skills(user_id, skills)


async def get_skill_recommendations_service(
    user_id: int,
    context: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Função wrapper para compatibilidade"""
    return await skill_service.get_skill_recommendations(user_id, context, limit)
