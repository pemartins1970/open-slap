"""
LLM Manager Refatorado - Versão Modular
Gerenciamento de providers LLM (Gemini, Groq, Ollama, OpenAI, OpenRouter)
"""

import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from .llm.providers import ProviderManager, ProviderConfig
from .llm.clients import create_client, LLMClient
from .config.settings import settings

BASE_DIR = Path(__file__).resolve().parents[1]

# Timeout HTTP global
HTTP_TIMEOUT_S = float(str(os.getenv("OPENSLAP_HTTP_TIMEOUT_S") or "6").strip() or "6")


class LLMManager:
    """Gerenciador de LLMs - Versão Refatorada e Modular"""
    
    def __init__(self):
        self.provider_manager = ProviderManager()
        self._clients_cache: Dict[str, LLMClient] = {}
    
    def _get_client(self, provider_id: str) -> Optional[LLMClient]:
        """Obtém cliente LLM com cache"""
        if provider_id not in self._clients_cache:
            provider = self.provider_manager.get_provider(provider_id)
            if not provider:
                return None
            self._clients_cache[provider_id] = create_client(provider)
        
        return self._clients_cache[provider_id]
    
    def _summarize_sqlite_schema(self) -> str:
        """Resume schema do banco de dados SQLite"""
        try:
            from .db import get_db_path
        except Exception:
            return ""
        
        try:
            import sqlite3
            db_path = get_db_path()
            if not db_path or not os.path.exists(db_path):
                return ""
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                schema_parts = ["### Schema do Banco de Dados SQLite\n"]
                for (table_name,) in tables:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    schema_parts.append(f"**{table_name}**:")
                    for col in columns:
                        schema_parts.append(f"  - {col[1]} ({col[2]})")
                    schema_parts.append("")
                
                return "\n".join(schema_parts)
        except Exception:
            return ""
    
    def _summarize_project_tree(self) -> str:
        """Resume estrutura do projeto"""
        root = BASE_DIR
        max_dirs = 6
        max_files_per_dir = 6
        
        try:
            tree_parts = ["### Estrutura do Projeto\n"]
            
            for i, (dirpath, dirnames, filenames) in enumerate(os.walk(root)):
                if i >= max_dirs:
                    break
                
                rel_path = os.path.relpath(dirpath, root)
                if rel_path == ".":
                    tree_parts.append("**raiz**:")
                else:
                    tree_parts.append(f"**{rel_path}**:")
                
                # Limita diretórios
                dirnames[:] = dirnames[:max_dirs]
                for dirname in dirnames:
                    tree_parts.append(f"  📁 {dirname}/")
                
                # Limita arquivos
                for filename in filenames[:max_files_per_dir]:
                    tree_parts.append(f"  📄 {filename}")
                
                tree_parts.append("")
            
            return "\n".join(tree_parts)
        except Exception:
            return ""
    
    def _build_full_prompt(
        self, prompt: str, expert: Dict[str, Any], user_context: Optional[str]
    ) -> str:
        """Constrói prompt completo com contexto do expert e sistema"""
        expert_prompt = (expert or {}).get("prompt") or ""
        
        # Adiciona contexto do expert se existir
        if expert_prompt:
            base = expert_prompt
        else:
            base = "Você é um assistente de IA útil e preciso."
        
        # Adiciona contexto do sistema se habilitado
        if settings.enable_system_profile and settings.attach_system_profile:
            ctx = ""
            
            # Adiciona schema do BD se habilitado
            if settings.enable_rag_sqlite:
                schema = self._summarize_sqlite_schema()
                if schema:
                    ctx += f"\n{schema}"
            
            # Adiciona estrutura do projeto
            proj_tree = self._summarize_project_tree()
            if proj_tree:
                ctx += f"\n{proj_tree}"
            
            # Limita tamanho do contexto
            if len(ctx) > settings.system_profile_max_chars:
                ctx = ctx[: settings.system_profile_max_chars] + "..."
            
            if ctx.strip():
                base = f"{base}\n\nContexto do sistema (SOUL, uso interno):\n{ctx}".strip()
        
        return f"{base}\n\nPergunta: {prompt}\n\nResposta:".strip()
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Obtém status de todos os providers"""
        status = {}
        
        for provider_id in self.provider_manager.get_enabled_providers():
            client = self._get_client(provider_id)
            if client:
                try:
                    is_online = await client.test_connection()
                    provider = self.provider_manager.get_provider(provider_id)
                    
                    status[provider_id] = {
                        "name": provider.name if provider else provider_id,
                        "enabled": provider.is_enabled() if provider else False,
                        "online": is_online,
                        "model": provider.model if provider else "",
                        "keys_count": len(provider.keys) if provider else 0,
                    }
                except Exception as e:
                    status[provider_id] = {
                        "name": provider_id,
                        "enabled": False,
                        "online": False,
                        "error": str(e),
                    }
            else:
                status[provider_id] = {
                    "name": provider_id,
                    "enabled": False,
                    "online": False,
                    "error": "Cliente não disponível",
                }
        
        return status
    
    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        preferred_provider: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming com fallback automático"""
        
        # Determina ordem de providers a tentar
        if preferred_provider:
            providers_to_try = [preferred_provider] + [
                p for p in self.provider_manager.get_available_providers()
                if p != preferred_provider
            ]
        else:
            providers_to_try = self.provider_manager.get_available_providers()
        
        last_error = None
        
        for provider_id in providers_to_try:
            try:
                client = self._get_client(provider_id)
                if not client:
                    continue
                
                provider = self.provider_manager.get_provider(provider_id)
                if not provider or not provider.is_enabled():
                    continue
                
                # Tenta gerar resposta
                async for chunk in client.stream_generate(
                    prompt, expert, user_context, messages
                ):
                    yield chunk
                
                return  # Sucesso, não precisa tentar outros providers
            
            except Exception as e:
                last_error = e
                # Continua para o próximo provider
                continue
        
        # Se chegou aqui, todos os providers falharam
        if last_error:
            yield f"❌ Erro em todos os providers: {str(last_error)}"
        else:
            yield "❌ Todos os providers estão indisponíveis. Verifique suas configurações de API."
    
    async def test_provider(self, provider_id: str) -> bool:
        """Testa se um provider específico está funcionando"""
        client = self._get_client(provider_id)
        if not client:
            return False
        
        try:
            return await client.test_connection()
        except Exception:
            return False
    
    def get_available_providers(self) -> List[str]:
        """Obtém lista de providers disponíveis"""
        return self.provider_manager.get_available_providers()
    
    def get_provider_info(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações detalhadas de um provider"""
        provider = self.provider_manager.get_provider(provider_id)
        if not provider:
            return None
        
        return {
            "id": provider.provider_id,
            "name": provider.name,
            "enabled": provider.enabled,
            "model": provider.model,
            "base_url": provider.base_url,
            "url": provider.url,
            "timeout": provider.timeout,
            "keys_count": len(provider.keys),
        }
    
    def update_provider_config(self, provider_id: str, **kwargs) -> bool:
        """Atualiza configuração de um provider"""
        success = self.provider_manager.update_provider_config(provider_id, **kwargs)
        
        # Limpa cache do cliente se atualizado com sucesso
        if success and provider_id in self._clients_cache:
            del self._clients_cache[provider_id]
        
        return success


# Instância global para compatibilidade
llm_manager = LLMManager()

# Funções de conveniência para compatibilidade com código existente
async def get_provider_status() -> Dict[str, Any]:
    """Obtém status dos providers (função de conveniência)"""
    return await llm_manager.get_provider_status()

async def stream_generate(
    prompt: str,
    expert: Dict[str, Any],
    user_context: Optional[str] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    preferred_provider: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Gera resposta em streaming (função de conveniência)"""
    async for chunk in llm_manager.stream_generate(
        prompt, expert, user_context, messages, preferred_provider
    ):
        yield chunk

async def test_provider(provider_id: str) -> bool:
    """Testa provider (função de conveniência)"""
    return await llm_manager.test_provider(provider_id)

def get_available_providers() -> List[str]:
    """Obtém providers disponíveis (função de conveniência)"""
    return llm_manager.get_available_providers()

def get_provider_info(provider_id: str) -> Optional[Dict[str, Any]]:
    """Obtém informações do provider (função de conveniência)"""
    return llm_manager.get_provider_info(provider_id)
