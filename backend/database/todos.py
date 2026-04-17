"""
Operações de Banco de Dados para Tarefas TODO
"""

import sqlite3
from typing import List, Dict, Any, Optional
from .schema import TASK_TODO_UPDATABLE_COLUMNS


class TodoRepository:
    """Repositório para operações com tarefas TODO"""
    
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
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO task_todos (
                    user_id, conversation_id, text, status, kind, actor, origin,
                    scope, priority, due_at, parent_todo_id, delivery_path,
                    artifact_meta, source_conversation_id, source_message_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id, conversation_id, text, status, kind, actor, origin,
                    scope, priority, due_at, parent_todo_id, delivery_path,
                    artifact_meta, source_conversation_id, source_message_id
                )
            )
            conn.commit()
            return int(cursor.lastrowid)
    
    def list_task_todos(
        self,
        user_id: int,
        conversation_id: int,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        scope: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista tarefas TODO de uma conversa"""
        with self._connect() as conn:
            query = "SELECT * FROM task_todos WHERE user_id = ? AND conversation_id = ?"
            params = [user_id, conversation_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if kind:
                query += " AND kind = ?"
                params.append(kind)
            
            if scope:
                query += " AND scope = ?"
                params.append(scope)
            
            query += " ORDER BY created_at ASC"
            
            rows = conn.execute(query, params).fetchall()
            out = []
            for row in rows:
                d = dict(row)
                # Processa artifact_meta se for JSON
                if d.get("artifact_meta"):
                    try:
                        import json
                        d["artifact_meta"] = json.loads(d["artifact_meta"])
                    except (json.JSONDecodeError, TypeError):
                        d["artifact_meta"] = None
                out.append(d)
            return out
    
    def list_pending_todos(self, user_id: int) -> List[Dict[str, Any]]:
        """Lista todas as tarefas pendentes do usuário"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT t.*, c.title, c.session_id
                FROM task_todos t
                JOIN conversations c ON t.conversation_id = c.id
                WHERE t.user_id = ? AND t.status = 'pending'
                ORDER BY t.created_at DESC
                """,
                (user_id,)
            ).fetchall()
            
            out = []
            for row in rows:
                d = dict(row)
                if d.get("artifact_meta"):
                    try:
                        import json
                        d["artifact_meta"] = json.loads(d["artifact_meta"])
                    except (json.JSONDecodeError, TypeError):
                        d["artifact_meta"] = None
                out.append(d)
            return out
    
    def update_task_todo(
        self,
        user_id: int,
        todo_id: int,
        updates: Dict[str, Any]
    ) -> bool:
        """Atualiza uma tarefa TODO"""
        if not updates:
            return False
        
        # Filtra apenas colunas permitidas
        valid_updates = {
            k: v for k, v in updates.items() 
            if k in TASK_TODO_UPDATABLE_COLUMNS
        }
        
        if not valid_updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in valid_updates.keys()])
        values = list(valid_updates.values()) + [user_id, todo_id]
        
        with self._connect() as conn:
            cursor = conn.execute(
                f"""
                UPDATE task_todos 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? AND id = ?
                """,
                values
            )
            conn.commit()
            return bool(cursor.rowcount)
    
    def get_task_todo(self, user_id: int, todo_id: int) -> Optional[Dict[str, Any]]:
        """Obtém uma tarefa TODO específica"""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT t.*, c.title, c.session_id
                FROM task_todos t
                JOIN conversations c ON t.conversation_id = c.id
                WHERE t.user_id = ? AND t.id = ?
                """,
                (user_id, todo_id)
            ).fetchone()
            
            if not row:
                return None
            
            d = dict(row)
            if d.get("artifact_meta"):
                try:
                    import json
                    d["artifact_meta"] = json.loads(d["artifact_meta"])
                except (json.JSONDecodeError, TypeError):
                    d["artifact_meta"] = None
            return d
    
    def delete_task_todo(self, user_id: int, todo_id: int) -> bool:
        """Deleta uma tarefa TODO"""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM task_todos WHERE user_id = ? AND id = ?",
                (user_id, todo_id)
            )
            conn.commit()
            return bool(cursor.rowcount)
    
    def mark_todo_done(self, user_id: int, todo_id: int) -> bool:
        """Marca uma tarefa como concluída"""
        return self.update_task_todo(user_id, todo_id, {"status": "done"})
    
    def get_todos_by_parent(self, user_id: int, parent_todo_id: int) -> List[Dict[str, Any]]:
        """Obtém subtarefas de uma tarefa pai"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM task_todos 
                WHERE user_id = ? AND parent_todo_id = ?
                ORDER BY created_at ASC
                """,
                (user_id, parent_todo_id)
            ).fetchall()
            return [dict(row) for row in rows]
