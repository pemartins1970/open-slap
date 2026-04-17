"""
Gerenciamento de Banco de Dados SQLite - Versão Refatorada
Persistência de conversas e mensagens
"""

import os
import re
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

# Importações dos módulos refatorados
from .database import DatabaseSchema, TASK_TODO_UPDATABLE_COLUMNS
from .database.conversations import ConversationRepository
from .database.todos import TodoRepository
from .database.users import UserRepository


# Configuração de redação de dados sensíveis
_REDACTION_RULES = [
    ("github_token", re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("google_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{30,}\b")),
    ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b", re.IGNORECASE)),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9\-_]+?\.[A-Za-z0-9\-_]+?(\.[A-Za-z0-9\-_]+)?\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("cpf", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("cnpj", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")),
    (
        "private_key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"
        ),
    ),
]


def _redaction_enabled() -> bool:
    """Verifica se redação está habilitada"""
    v = (os.getenv("SLAP_MEMORY_REDACTION_ENABLED") or "").strip().lower()
    return v not in {"0", "false", "no", "off"}


def _redact_text(value: Optional[str]) -> Optional[str]:
    """Remove informações sensíveis do texto"""
    if value is None or not isinstance(value, str) or value == "":
        return value
    if not _redaction_enabled():
        return value
    out = value
    for name, rx in _REDACTION_RULES:
        out = rx.sub(f"[REDACTED:{name}]", out)
    return out


class DatabaseManager:
    """Gerenciador principal do banco de dados SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        env_db = (
            os.getenv("SLAP_DB_PATH") or os.getenv("OPENSLAP_DB_PATH") or ""
        ).strip()
        default_db = str(
            (Path(__file__).resolve().parents[1] / "data" / "auth.db").resolve()
        )
        self.db_path = str(db_path or env_db or default_db)
        
        # Inicializa repositórios
        self._schema = DatabaseSchema(self.db_path)
        self._conversations = ConversationRepository(self.db_path)
        self._todos = TodoRepository(self.db_path)
        self._users = UserRepository(self.db_path)
        
        self._ensure_database()
    
    def _ensure_database(self):
        """Garante que as tabelas existam"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._connect() as conn:
            self._schema.ensure_database(conn)
    
    def _connect(self) -> sqlite3.Connection:
        """Cria conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
        except Exception:
            pass
        return conn
    
    # === Operações de Conversas ===
    
    def create_conversation(
        self,
        user_id: int,
        session_id: str,
        title: str,
        kind: str = "conversation",
        source: str = "user"
    ) -> int:
        """Cria uma nova conversa"""
        return self._conversations.create_conversation(
            user_id, session_id, title, kind, source
        )
    
    def get_user_conversations(
        self, user_id: int, kind: Optional[str] = None, source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtém conversas do usuário"""
        return self._conversations.get_user_conversations(user_id, kind, source)
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Obtém mensagens de uma conversa"""
        return self._conversations.get_conversation_messages(conversation_id)
    
    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Obtém uma mensagem específica"""
        return self._conversations.get_message(message_id)
    
    def save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        expert_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tokens: Optional[int] = None
    ) -> int:
        """Salva uma mensagem na conversa"""
        # Aplica redação ao conteúdo se necessário
        if role == "assistant":
            content = _redact_text(content)
        
        return self._conversations.save_message(
            conversation_id, role, content, expert_id, provider, model, tokens
        )
    
    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Deleta conversa e suas mensagens"""
        return self._conversations.delete_conversation(conversation_id, user_id)
    
    def update_conversation_title(
        self, conversation_id: int, user_id: int, title: str
    ) -> bool:
        """Atualiza título da conversa"""
        return self._conversations.update_conversation_title(
            conversation_id, user_id, title
        )
    
    def search_user_messages(
        self, user_id: int, query: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Busca mensagens do usuário"""
        return self._conversations.search_user_messages(user_id, query, limit)
    
    def get_conversation_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém conversa ativa por session_id"""
        return self._conversations.get_conversation_by_session(session_id)
    
    def get_conversation_by_session_for_user(
        self, user_id: int, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém conversa por session_id para um usuário específico"""
        return self._conversations.get_conversation_by_session_for_user(user_id, session_id)
    
    # === Operações de Tarefas TODO ===
    
    def add_task_todo(
        self,
        user_id: int,
        conversation_id: int,
        text: str,
        status: str = "pending",
        kind: str = "step",
        actor: str = "human",
        origin: str = "user",
        scope: str = "project",
        priority: str = "medium",
        due_at: Optional[str] = None,
        parent_todo_id: Optional[int] = None,
        delivery_path: Optional[str] = None,
        artifact_meta: Optional[str] = None,
        source_conversation_id: Optional[int] = None,
        source_message_id: Optional[int] = None
    ) -> int:
        """Adiciona uma nova tarefa TODO"""
        return self._todos.add_task_todo(
            user_id, conversation_id, text, status, kind, actor, origin, scope,
            priority, due_at, parent_todo_id, delivery_path, artifact_meta,
            source_conversation_id, source_message_id
        )
    
    def list_task_todos(
        self,
        user_id: int,
        conversation_id: int,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        scope: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista tarefas TODO de uma conversa"""
        return self._todos.list_task_todos(user_id, conversation_id, status, kind, scope)
    
    def list_pending_todos(self, user_id: int) -> List[Dict[str, Any]]:
        """Lista todas as tarefas pendentes do usuário"""
        return self._todos.list_pending_todos(user_id)
    
    def update_task_todo(
        self, user_id: int, todo_id: int, updates: Dict[str, Any]
    ) -> bool:
        """Atualiza uma tarefa TODO"""
        return self._todos.update_task_todo(user_id, todo_id, updates)
    
    def get_task_todo(self, user_id: int, todo_id: int) -> Optional[Dict[str, Any]]:
        """Obtém uma tarefa TODO específica"""
        return self._todos.get_task_todo(user_id, todo_id)
    
    # === Operações de Usuários ===
    
    def get_user_skills(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Obtém habilidades do usuário"""
        return self._users.get_user_skills(user_id)
    
    def upsert_user_skills(self, user_id: int, skills: List[Dict[str, Any]]) -> None:
        """Atualiza habilidades do usuário"""
        self._users.upsert_user_skills(user_id, skills)
    
    def upsert_user_api_key_ciphertext(self, user_id: int, api_key_ciphertext: str) -> None:
        """Atualiza chave API do usuário (legado)"""
        self._users.upsert_user_api_key_ciphertext(user_id, api_key_ciphertext)
    
    def add_user_llm_provider_key_ciphertext(
        self, user_id: int, provider: str, api_key_ciphertext: str, set_active: bool = True
    ) -> int:
        """Adiciona chave de provedor LLM para o usuário"""
        return self._users.add_user_llm_provider_key_ciphertext(
            user_id, provider, api_key_ciphertext, set_active
        )
    
    def list_user_llm_provider_keys(
        self, user_id: int, provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista chaves LLM do usuário"""
        return self._users.list_user_llm_provider_keys(user_id, provider)
    
    def get_active_user_llm_provider_key_ciphertext(
        self, user_id: int, provider: str
    ) -> Optional[str]:
        """Obtém chave ativa do provedor LLM"""
        return self._users.get_active_user_llm_provider_key_ciphertext(user_id, provider)
    
    def set_active_user_llm_provider_key(
        self, user_id: int, provider: str, key_id: int
    ) -> bool:
        """Define chave ativa do provedor LLM"""
        return self._users.set_active_user_llm_provider_key(user_id, provider, key_id)
    
    def delete_user_llm_provider_key(self, user_id: int, provider: str, key_id: int) -> bool:
        """Deleta chave LLM do usuário"""
        return self._users.delete_user_llm_provider_key(user_id, provider, key_id)
    
    def get_user_onboarding_completed(self, user_id: int) -> Optional[bool]:
        """Verifica se onboarding do usuário foi concluído"""
        return self._users.get_user_onboarding_completed(user_id)
    
    def set_user_onboarding_completed(self, user_id: int, completed: bool) -> None:
        """Define status de onboarding do usuário"""
        self._users.set_user_onboarding_completed(user_id, completed)
    
    def upsert_user_connector_secret_ciphertext(
        self, user_id: int, connector_key: str, secret_ciphertext: str
    ) -> None:
        """Atualiza segredo de conector do usuário"""
        self._users.upsert_user_connector_secret_ciphertext(
            user_id, connector_key, secret_ciphertext
        )


# Instância global para compatibilidade
db_manager = DatabaseManager()

# Funções de conveniência para compatibilidade com código existente
def get_conversation_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtém conversa ativa por session_id (função de conveniência)"""
    return db_manager.get_conversation_by_session(session_id)

def get_conversation_by_session_for_user(user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
    """Obtém conversa por session_id para usuário específico (função de conveniência)"""
    return db_manager.get_conversation_by_session_for_user(user_id, session_id)

def get_user_conversations(user_id: int, kind: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtém conversas do usuário (função de conveniência)"""
    return db_manager.get_user_conversations(user_id, kind, source)

def create_conversation(user_id: int, session_id: str, title: str, kind: str = "conversation", source: str = "user") -> int:
    """Cria nova conversa (função de conveniência)"""
    return db_manager.create_conversation(user_id, session_id, title, kind, source)

def save_message(conversation_id: int, role: str, content: str, expert_id: Optional[str] = None, provider: Optional[str] = None, model: Optional[str] = None, tokens: Optional[int] = None) -> int:
    """Salva mensagem (função de conveniência)"""
    return db_manager.save_message(conversation_id, role, content, expert_id, provider, model, tokens)

def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
    """Obtém mensagens da conversa (função de conveniência)"""
    return db_manager.get_conversation_messages(conversation_id)

def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """Deleta conversa (função de conveniência)"""
    return db_manager.delete_conversation(conversation_id, user_id)

def update_conversation_title(conversation_id: int, user_id: int, title: str) -> bool:
    """Atualiza título da conversa (função de conveniência)"""
    return db_manager.update_conversation_title(conversation_id, user_id, title)

def search_user_messages(user_id: int, query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Busca mensagens do usuário (função de conveniência)"""
    return db_manager.search_user_messages(user_id, query, limit)

def add_task_todo(user_id: int, conversation_id: int, text: str, **kwargs) -> int:
    """Adiciona tarefa TODO (função de conveniência)"""
    return db_manager.add_task_todo(user_id, conversation_id, text, **kwargs)

def list_task_todos(user_id: int, conversation_id: int, **kwargs) -> List[Dict[str, Any]]:
    """Lista tarefas TODO (função de conveniência)"""
    return db_manager.list_task_todos(user_id, conversation_id, **kwargs)

def list_pending_todos(user_id: int) -> List[Dict[str, Any]]:
    """Lista tarefas pendentes (função de conveniência)"""
    return db_manager.list_pending_todos(user_id)

def update_task_todo(user_id: int, todo_id: int, updates: Dict[str, Any]) -> bool:
    """Atualiza tarefa TODO (função de conveniência)"""
    return db_manager.update_task_todo(user_id, todo_id, updates)

def get_task_todo(user_id: int, todo_id: int) -> Optional[Dict[str, Any]]:
    """Obtém tarefa TODO (função de conveniência)"""
    return db_manager.get_task_todo(user_id, todo_id)
