"""
🗄️ DB - Gerenciamento de Banco de Dados SQLite
Persistência de conversas e mensagens
Segundo WINDSURF_AGENT.md - SESS-01
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Garante que as tabelas existem"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Tabela de conversas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Tabela de mensagens
            conn.execute("""
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
            """)
            
            # Índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS friction_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meta_version TEXT NOT NULL,
                    meta_product TEXT NOT NULL,
                    meta_tier TEXT NOT NULL,
                    meta_timestamp TEXT NOT NULL,
                    meta_session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_code TEXT NOT NULL,
                    event_layer TEXT NOT NULL,
                    action_attempted TEXT NOT NULL,
                    blocked_by TEXT NOT NULL,
                    user_message TEXT,
                    context_os TEXT NOT NULL,
                    context_runtime TEXT NOT NULL,
                    context_skill_active TEXT,
                    context_connector_active TEXT,
                    payload_json TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    sent INTEGER NOT NULL DEFAULT 0,
                    github_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_friction_events_sent ON friction_events(sent)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_friction_events_code ON friction_events(event_code)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_friction_events_layer ON friction_events(event_layer)")
            
            conn.commit()
    
    def create_conversation(self, user_id: int, session_id: str, title: str) -> int:
        """Cria nova conversa"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (user_id, session_id, title) VALUES (?, ?, ?)",
                (user_id, session_id, title)
            )
            conversation_id = cursor.lastrowid
            conn.commit()
        
        return conversation_id
    
    def get_user_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtém conversas do usuário"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conversations = conn.execute("""
                SELECT id, title, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
                FROM conversations 
                WHERE user_id = ? 
                ORDER BY updated_at DESC
            """, (user_id,)).fetchall()
            
            return [dict(conv) for conv in conversations]
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Obtém mensagens de uma conversa"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            messages = conn.execute("""
                SELECT id, role, content, expert_id, provider, model, tokens, created_at
                FROM messages 
                WHERE conversation_id = ? 
                ORDER BY created_at ASC
            """, (conversation_id,)).fetchall()
            
            return [dict(msg) for msg in messages]
    
    def save_message(self, conversation_id: int, role: str, content: str, 
                   expert_id: Optional[str] = None, provider: Optional[str] = None, 
                   model: Optional[str] = None, tokens: Optional[int] = None) -> int:
        """Salva mensagem"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO messages 
                (conversation_id, role, content, expert_id, provider, model, tokens) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (conversation_id, role, content, expert_id, provider, model, tokens))
            
            message_id = cursor.lastrowid
            
            # Atualizar timestamp da conversa
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            
            conn.commit()
        
        return message_id
    
    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Deleta conversa e suas mensagens"""
        with sqlite3.connect(self.db_path) as conn:
            # Verificar se a conversa pertence ao usuário
            conv = conn.execute(
                "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id)
            ).fetchone()
            
            if not conv:
                return False
            
            # Deletar mensagens primeiro (foreign key)
            conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            
            # Deletar conversa
            conn.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id)
            )
            
            conn.commit()
        
        return True
    
    def get_conversation_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém conversa ativa por session_id"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conversation = conn.execute("""
                SELECT id, user_id, title, created_at
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (session_id,)).fetchone()
            
            if conversation:
                return dict(conversation)
        
        return None

    def create_friction_event(self, payload: Dict[str, Any], mode: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO friction_events (
                    meta_version, meta_product, meta_tier, meta_timestamp, meta_session_id,
                    event_type, event_code, event_layer, action_attempted, blocked_by, user_message,
                    context_os, context_runtime, context_skill_active, context_connector_active,
                    payload_json, mode, sent, github_url, sent_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL)
                """,
                (
                    str(payload.get("meta", {}).get("version", "")),
                    str(payload.get("meta", {}).get("product", "")),
                    str(payload.get("meta", {}).get("tier", "")),
                    str(payload.get("meta", {}).get("timestamp", "")),
                    str(payload.get("meta", {}).get("session_id", "")),
                    str(payload.get("event", {}).get("type", "")),
                    str(payload.get("event", {}).get("code", "")),
                    str(payload.get("event", {}).get("layer", "")),
                    str(payload.get("event", {}).get("action_attempted", "")),
                    str(payload.get("event", {}).get("blocked_by", "")),
                    payload.get("event", {}).get("user_message"),
                    str(payload.get("context", {}).get("os", "")),
                    str(payload.get("context", {}).get("runtime", "")),
                    payload.get("context", {}).get("skill_active"),
                    payload.get("context", {}).get("connector_active"),
                    json.dumps(payload, ensure_ascii=False),
                    mode,
                ),
            )
            event_id = cursor.lastrowid
            conn.commit()
        return int(event_id)

    def list_friction_events(self, sent: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        query = "SELECT * FROM friction_events"
        params: List[Any] = []
        if sent is not None:
            query += " WHERE sent = ?"
            params.append(int(sent))
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(r) for r in rows]

    def count_pending_friction_events(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM friction_events WHERE sent = 0").fetchone()
            return int(row[0]) if row else 0

    def mark_friction_event_sent(self, event_id: int, github_url: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE friction_events SET sent = 1, github_url = ?, sent_at = CURRENT_TIMESTAMP WHERE id = ?",
                (github_url, int(event_id)),
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_friction_event(self, event_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM friction_events WHERE id = ?", (int(event_id),))
            conn.commit()
            return cur.rowcount > 0
    
    def update_conversation_title(self, conversation_id: int, title: str) -> bool:
        """Atualiza título da conversa"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (title, conversation_id)
            )
            conn.commit()
        
        return True
    
    def get_conversation_stats(self, conversation_id: int) -> Dict[str, Any]:
        """Obtém estatísticas da conversa"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Estatísticas gerais
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
                    SUM(tokens) as total_tokens,
                    MIN(created_at) as started_at,
                    MAX(created_at) as last_activity
                FROM messages 
                WHERE conversation_id = ?
            """, (conversation_id,)).fetchone()
            
            # Providers usados
            providers = conn.execute("""
                SELECT DISTINCT provider, COUNT(*) as usage_count
                FROM messages 
                WHERE conversation_id = ? AND provider IS NOT NULL
                GROUP BY provider
            """, (conversation_id,)).fetchall()
            
            # Experts usados
            experts = conn.execute("""
                SELECT DISTINCT expert_id, COUNT(*) as usage_count
                FROM messages 
                WHERE conversation_id = ? AND expert_id IS NOT NULL
                GROUP BY expert_id
            """, (conversation_id,)).fetchall()
            
            return {
                **dict(stats),
                "providers": [dict(p) for p in providers],
                "experts": [dict(e) for e in experts]
            }

# Instância global
db_manager = DatabaseManager()

# Funções auxiliares
def create_conversation(user_id: int, session_id: str, title: str) -> int:
    """Cria nova conversa"""
    return db_manager.create_conversation(user_id, session_id, title)

def get_user_conversations(user_id: int) -> List[Dict[str, Any]]:
    """Obtém conversas do usuário"""
    return db_manager.get_user_conversations(user_id)

def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
    """Obtém mensagens de uma conversa"""
    return db_manager.get_conversation_messages(conversation_id)

def save_message(conversation_id: int, role: str, content: str, 
               expert_id: Optional[str] = None, provider: Optional[str] = None, 
               model: Optional[str] = None, tokens: Optional[int] = None) -> int:
    """Salva mensagem"""
    return db_manager.save_message(conversation_id, role, content, expert_id, provider, model, tokens)

def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """Deleta conversa"""
    return db_manager.delete_conversation(conversation_id, user_id)

def get_conversation_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtém conversa ativa por session_id"""
    return db_manager.get_conversation_by_session(session_id)

def create_friction_event(payload: Dict[str, Any], mode: str) -> int:
    return db_manager.create_friction_event(payload, mode)

def list_friction_events(sent: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
    return db_manager.list_friction_events(sent=sent, limit=limit)

def count_pending_friction_events() -> int:
    return db_manager.count_pending_friction_events()

def mark_friction_event_sent(event_id: int, github_url: str) -> bool:
    return db_manager.mark_friction_event_sent(event_id, github_url)

def delete_friction_event(event_id: int) -> bool:
    return db_manager.delete_friction_event(event_id)
