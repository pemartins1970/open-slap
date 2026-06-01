"""
Schema do Banco de Dados SQLite
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path


# Colunas que podem ser modificadas pelo update_task_todo
TASK_TODO_UPDATABLE_COLUMNS: frozenset = frozenset({
    "text", "status", "kind", "actor", "origin", "scope", "priority",
    "due_at", "parent_todo_id", "delivery_path", "artifact_meta",
    "source_conversation_id", "source_message_id",
})


class DatabaseSchema:
    """Gerencia schema e migrações do banco de dados"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def ensure_database(self, connection) -> None:
        """Garante que todas as tabelas existam"""
        self._create_users_table(connection)
        self._create_conversations_table(connection)
        self._create_messages_table(connection)
        self._create_task_todos_table(connection)
        self._create_user_skills_table(connection)
        self._create_user_llm_keys_table(connection)
        self._create_user_connectors_table(connection)
        self._create_user_onboarding_table(connection)
        self._create_indexes(connection)
    
    def _create_users_table(self, connection) -> None:
        """Cria tabela de usuários"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    
    def _create_conversations_table(self, connection) -> None:
        """Cria tabela de conversas"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                kind TEXT DEFAULT 'conversation',
                source TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        
        # Migrações para colunas novas
        try:
            cols = [
                (r[1] if isinstance(r, (list, tuple)) else None)
                for r in connection.execute("PRAGMA table_info(conversations)").fetchall()
            ]
            if "kind" not in cols:
                connection.execute(
                    "ALTER TABLE conversations ADD COLUMN kind TEXT DEFAULT 'conversation'"
                )
            if "source" not in cols:
                connection.execute(
                    "ALTER TABLE conversations ADD COLUMN source TEXT DEFAULT 'user'"
                )
                try:
                    connection.execute(
                        "UPDATE conversations SET source='user' WHERE source IS NULL OR TRIM(source)=''"
                    )
                except Exception:
                    pass
        except Exception:
            pass
    
    def _create_messages_table(self, connection) -> None:
        """Cria tabela de mensagens"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                expert_id TEXT,
                provider TEXT,
                model TEXT,
                tokens INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            """
        )
    
    def _create_task_todos_table(self, connection) -> None:
        """Cria tabela de tarefas TODO"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done')),
                kind TEXT DEFAULT 'step',
                actor TEXT DEFAULT 'human',
                origin TEXT DEFAULT 'user',
                scope TEXT DEFAULT 'project',
                priority TEXT DEFAULT 'medium',
                due_at TEXT,
                parent_todo_id INTEGER,
                delivery_path TEXT,
                artifact_meta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_conversation_id INTEGER,
                source_message_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            """
        )
        
        # Migrações para colunas novas
        try:
            cols = [
                (r[1] if isinstance(r, (list, tuple)) else None)
                for r in connection.execute("PRAGMA table_info(task_todos)").fetchall()
            ]
            if "kind" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN kind TEXT DEFAULT 'step'")
            if "actor" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN actor TEXT DEFAULT 'human'")
            if "origin" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN origin TEXT DEFAULT 'user'")
            if "scope" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN scope TEXT DEFAULT 'project'")
            if "priority" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN priority TEXT DEFAULT 'medium'")
            if "parent_todo_id" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN parent_todo_id INTEGER")
            if "delivery_path" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN delivery_path TEXT")
            if "artifact_meta" not in cols:
                connection.execute("ALTER TABLE task_todos ADD COLUMN artifact_meta TEXT")
        except Exception:
            pass
    
    def _create_user_skills_table(self, connection) -> None:
        """Cria tabela de habilidades do usuário"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_skills (
                user_id INTEGER PRIMARY KEY,
                skills_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
    
    def _create_user_llm_keys_table(self, connection) -> None:
        """Cria tabela de chaves LLM do usuário"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_llm_provider_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                key_name TEXT NOT NULL,
                api_key_ciphertext TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
    
    def _create_user_connectors_table(self, connection) -> None:
        """Cria tabela de conectores do usuário"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_connector_secrets (
                user_id INTEGER NOT NULL,
                connector_key TEXT NOT NULL,
                secret_ciphertext TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, connector_key),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
    
    def _create_user_onboarding_table(self, connection) -> None:
        """Cria tabela de onboarding do usuário"""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_onboarding (
                user_id INTEGER PRIMARY KEY,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
    
    def _create_indexes(self, connection) -> None:
        """Cria índices para performance"""
        # Conversations
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_kind ON conversations(user_id, kind)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_source ON conversations(user_id, source)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)"
        )
        
        # Messages
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)"
        )
        
        # Task Todos
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_task_todos_user_id ON task_todos(user_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_task_todos_conversation_id ON task_todos(conversation_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_task_todos_status ON task_todos(status)"
        )
        
        # LLM Keys
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_keys_user_provider ON user_llm_provider_keys(user_id, provider)"
        )
