"""
🧠 Memory Service - Serviço isolado de gestão de memória
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from ..db import (
    # Memória existente
    list_soul_events,
    append_soul_event,
    get_user_soul,
    upsert_user_soul,
    _build_soul_markdown,
    
    # Memory decay e pruning
    decay_memory,
    prune_low_salience_memories,
    get_consolidated_memory_snapshot,
    
    # Memory imports
    save_external_memory_import,
    list_external_memory_imports,
    pin_external_memory_import,
    delete_external_memory_import,
    touch_external_memory_imports,
    
    # Search
    search_user_memory
)

logger = logging.getLogger(__name__)


class MemoryService:
    """Serviço de memória avançado com múltiplas estratégias"""
    
    def __init__(self):
        self.cache = {}  # Cache em memória para acesso rápido
        self.cache_ttl = 300  # 5 minutos
        
    async def store_memory(
        self,
        user_id: int,
        content: str,
        source: str = "user",
        salience: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Armazena memória com múltiplas camadas
        """
        try:
            # 1. Gerar ID único
            memory_id = f"mem_{user_id}_{datetime.utcnow().timestamp()}"
            
            # 2. Calcular salience se não fornecida
            if salience is None:
                salience = self._calculate_salience(content, source)
            
            # 3. Armazenar como soul event (camada existente)
            append_soul_event(
                user_id=user_id,
                source=source,
                content=content,
                salience=salience,
                metadata=metadata or {}
            )
            
            # 4. Cache para acesso rápido
            self.cache[memory_id] = {
                "content": content,
                "source": source,
                "salience": salience,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "accessed_at": datetime.utcnow()
            }
            
            logger.info(f"Memory stored: {memory_id} for user {user_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
    
    async def retrieve_memory(
        self,
        user_id: int,
        query: Optional[str] = None,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera memórias com busca híbrida
        """
        try:
            results = []
            
            # 1. Buscar no cache primeiro
            cached_results = self._search_cache(user_id, query, limit)
            results.extend(cached_results)
            
            # 2. Buscar no banco de dados (soul events)
            db_results = search_user_memory(
                user_id=user_id,
                q=query or "",
                limit=limit - len(results)
            )
            
            # 3. Enriquecer resultados com metadados
            for result in db_results:
                result["source"] = "database"
                result["retrieved_at"] = datetime.utcnow()
                results.append(result)
            
            # 4. Aplicar filtros se fornecidos
            if filters:
                results = self._apply_filters(results, filters)
            
            # 5. Ordenar por relevância
            results.sort(key=lambda x: (
                x.get("salience", 0),
                x.get("created_at", datetime.min)
            ), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    async def update_memory(
        self,
        user_id: int,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Atualiza memória existente
        """
        try:
            # Verificar se está no cache
            if memory_id in self.cache:
                self.cache[memory_id].update(updates)
                self.cache[memory_id]["updated_at"] = datetime.utcnow()
            
            # TODO: Implementar atualização no banco
            logger.info(f"Memory updated: {memory_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            return False
    
    async def delete_memory(
        self,
        user_id: int,
        memory_id: str
    ) -> bool:
        """
        Remove memória específica
        """
        try:
            # Remover do cache
            if memory_id in self.cache:
                del self.cache[memory_id]
            
            # TODO: Implementar remoção do banco
            logger.info(f"Memory deleted: {memory_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return False
    
    async def consolidate_memory(
        self,
        user_id: int,
        strategy: str = "salience"
    ) -> Dict[str, Any]:
        """
        Consolida memórias usando estratégia específica
        """
        try:
            if strategy == "salience":
                # Usar snapshot consolidado existente
                snapshot = get_consolidated_memory_snapshot(user_id)
                return {
                    "strategy": strategy,
                    "snapshot": snapshot,
                    "consolidated_at": datetime.utcnow(),
                    "total_memories": len(snapshot) if isinstance(snapshot, list) else 1
                }
            
            elif strategy == "temporal":
                # Consolidar por relevância temporal
                memories = await self.retrieve_memory(user_id, limit=100)
                recent_memories = [
                    m for m in memories
                    if m.get("created_at") and m["created_at"] > datetime.utcnow() - timedelta(days=7)
                ]
                
                return {
                    "strategy": strategy,
                    "snapshot": recent_memories,
                    "consolidated_at": datetime.utcnow(),
                    "total_memories": len(recent_memories)
                }
            
            elif strategy == "thematic":
                # Consolidar por temas
                memories = await self.retrieve_memory(user_id, limit=200)
                themes = self._group_by_themes(memories)
                
                return {
                    "strategy": strategy,
                    "snapshot": themes,
                    "consolidated_at": datetime.utcnow(),
                    "total_memories": len(memories)
                }
            
            else:
                raise ValueError(f"Unknown consolidation strategy: {strategy}")
                
        except Exception as e:
            logger.error(f"Error consolidating memory: {str(e)}")
            return {"strategy": strategy, "error": str(e)}
    
    async def decay_and_prune(
        self,
        user_id: int,
        force: bool = False
    ) -> Dict[str, int]:
        """
        Executa decay e pruning de memórias
        """
        try:
            # Verificar se já executou recentemente
            if not force:
                # TODO: Implementar controle de frequência
                pass
            
            # Executar decay
            decayed = decay_memory(user_id)
            
            # Executar pruning
            pruned = prune_low_salience_memories(user_id)
            
            # Limpar cache expirado
            self._cleanup_cache()
            
            logger.info(f"Memory decay/pruned for user {user_id}: decayed={decayed}, pruned={pruned}")
            
            return {
                "decayed": decayed,
                "pruned": pruned,
                "total": decayed + pruned
            }
            
        except Exception as e:
            logger.error(f"Error in decay/prune: {str(e)}")
            return {"decayed": 0, "pruned": 0, "error": str(e)}
    
    def _calculate_salience(
        self,
        content: str,
        source: str
    ) -> float:
        """
        Calcula salience baseado no conteúdo e fonte
        """
        try:
            # Salience base
            base_salience = 0.5
            
            # Ajuste por fonte
            source_multipliers = {
                "user": 1.2,
                "assistant": 0.8,
                "system": 0.6,
                "import": 1.0
            }
            base_salience *= source_multipliers.get(source, 1.0)
            
            # Ajuste por tamanho do conteúdo
            content_length = len(content)
            if content_length > 500:
                base_salience *= 1.1
            elif content_length > 1000:
                base_salience *= 1.2
            
            # Ajuste por palavras-chave importantes
            important_keywords = [
                "importante", "crucial", "essencial", "prioridade",
                "urgente", "deadline", "objetivo", "meta"
            ]
            keyword_count = sum(1 for keyword in important_keywords if keyword.lower() in content.lower())
            if keyword_count > 0:
                base_salience *= (1 + (keyword_count * 0.1))
            
            # Limitar entre 0.1 e 1.0
            return max(0.1, min(1.0, base_salience))
            
        except Exception:
            return 0.5
    
    def _search_cache(
        self,
        user_id: int,
        query: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Busca no cache local
        """
        try:
            results = []
            
            # Limpar cache expirado
            self._cleanup_cache()
            
            # Buscar por user_id
            user_memories = [
                mem for mem_id, mem in self.cache.items()
                if mem_id.startswith(f"mem_{user_id}_")
            ]
            
            # Filtrar por query se fornecida
            if query:
                query_lower = query.lower()
                user_memories = [
                    mem for mem in user_memories
                    if query_lower in mem.get("content", "").lower()
                ]
            
            # Ordenar por accessed_at (mais recente primeiro)
            user_memories.sort(
                key=lambda x: x.get("accessed_at", datetime.min),
                reverse=True
            )
            
            return user_memories[:limit]
            
        except Exception:
            return []
    
    def _cleanup_cache(self):
        """
        Remove itens expirados do cache
        """
        try:
            expired_keys = []
            cutoff = datetime.utcnow() - timedelta(seconds=self.cache_ttl)
            
            for key, value in self.cache.items():
                if value.get("created_at") and value["created_at"] < cutoff:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                
        except Exception:
            pass
    
    def _apply_filters(
        self,
        memories: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Aplica filtros na lista de memórias
        """
        try:
            filtered = memories
            
            # Filtro por fonte
            if "source" in filters:
                filtered = [
                    mem for mem in filtered
                    if mem.get("source") == filters["source"]
                ]
            
            # Filtro por salience mínima
            if "min_salience" in filters:
                min_sal = filters["min_salience"]
                filtered = [
                    mem for mem in filtered
                    if mem.get("salience", 0) >= min_sal
                ]
            
            # Filtro por período
            if "period" in filters:
                period = filters["period"]
                cutoff = datetime.utcnow() - timedelta(days=period)
                filtered = [
                    mem for mem in filtered
                    if mem.get("created_at") and mem["created_at"] >= cutoff
                ]
            
            return filtered
            
        except Exception:
            return memories
    
    def _group_by_themes(
        self,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa memórias por temas usando heurísticas simples
        """
        try:
            themes = {}
            
            for memory in memories:
                content = memory.get("content", "").lower()
                
                # Heurística simples para identificar temas
                if any(word in content for word in ["projeto", "project", "meta", "goal"]):
                    theme = "projects"
                elif any(word in content for word in ["trabalho", "work", "tarefa", "task"]):
                    theme = "work"
                elif any(word in content for word in ["pessoal", "personal", "vida", "life"]):
                    theme = "personal"
                elif any(word in content for word in ["aprendizado", "learning", "estudo", "study"]):
                    theme = "learning"
                else:
                    theme = "general"
                
                if theme not in themes:
                    themes[theme] = []
                
                themes[theme].append(memory)
            
            return themes
            
        except Exception:
            return {}


# Instância global do serviço
memory_service = MemoryService()


# Funções de compatibilidade com código existente
async def store_memory(
    user_id: int,
    content: str,
    source: str = "user",
    salience: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Função wrapper para compatibilidade"""
    return await memory_service.store_memory(user_id, content, source, salience, metadata)


async def retrieve_memory(
    user_id: int,
    query: Optional[str] = None,
    limit: int = 50,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Função wrapper para compatibilidade"""
    return await memory_service.retrieve_memory(user_id, query, limit, filters)


async def consolidate_memory(
    user_id: int,
    strategy: str = "salience"
) -> Dict[str, Any]:
    """Função wrapper para compatibilidade"""
    return await memory_service.consolidate_memory(user_id, strategy)
