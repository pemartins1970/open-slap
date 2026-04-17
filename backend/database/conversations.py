"""
Operações de Banco de Dados para Conversas
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path


class ConversationRepository:
    """Repositório para operações com conversas"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
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
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_conversation(
        self,
        user_id: int,
        session_id: str,
        title: str,
        kind: str = "conversation",
        source: str = "user"
    ) -> int:
        """Cria uma nova conversa"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversations (user_id, session_id, title, kind, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, session_id, title, kind, source)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_conversations(
        self, 
        user_id: int, 
        kind: Optional[str] = None, 
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtém conversas do usuário"""
        with self._connect() as conn:
            query = "SELECT * FROM conversations WHERE user_id = ?"
            params = [user_id]
            
            if kind:
                query += " AND kind = ?"
                params.append(kind)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY updated_at DESC"
            
            conversations = conn.execute(query, params).fetchall()
            return [dict(conv) for conv in conversations]
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Obtém mensagens de uma conversa"""
        with self._connect() as conn:
            messages = conn.execute(
                """
                SELECT * FROM messages 
                WHERE conversation_id = ? 
                ORDER BY created_at ASC
                """,
                (conversation_id,)
            ).fetchall()
            return [dict(msg) for msg in messages]
    
    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Obtém uma mensagem específica"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM messages WHERE id = ?",
                (message_id,)
            ).fetchone()
            return dict(row) if row else None
    
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
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages 
                (conversation_id, role, content, expert_id, provider, model, tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (conversation_id, role, content, expert_id, provider, model, tokens)
            )
            
            # Atualiza timestamp da conversa
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            
            conn.commit()
            return cursor.lastrowid
    
    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Deleta conversa e suas mensagens"""
        with self._connect() as conn:
            # Verifica se a conversa pertence ao usuário
            conv = conn.execute(
                "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id)
            ).fetchone()
            
            if not conv:
                return False
            
            # Deleta mensagens
            conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            
            # Deleta TODOs relacionados
            conn.execute(
                "DELETE FROM task_todos WHERE conversation_id = ?",
                (conversation_id,)
            )
            
            # Deleta conversa
            conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            
            conn.commit()
            return True
    
    def update_conversation_title(
        self, conversation_id: int, user_id: int, title: str
    ) -> bool:
        """Atualiza título da conversa"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE conversations 
                SET title = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
                """,
                (title, conversation_id, user_id)
            )
            conn.commit()
            return bool(cursor.rowcount)
    
    def search_user_messages(
        self,
        user_id: int,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Busca mensagens do usuário"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT m.*, c.title, c.session_id
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = ? AND m.content LIKE ?
                ORDER BY m.created_at DESC
                LIMIT ?
                """,
                (user_id, f"%{query}%", limit)
            ).fetchall()
            return [dict(r) for r in rows]
    
    def get_conversation_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém conversa ativa por session_id"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_conversation_by_session_for_user(
        self, user_id: int, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém conversa por session_id para um usuário específico"""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM conversations 
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id)
            ).fetchone()
            if row:
                return dict(row)
            return None
