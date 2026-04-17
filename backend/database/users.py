"""
Operações de Banco de Dados para Usuários
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional


class UserRepository:
    """Repositório para operações com usuários"""
    
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
    
    def create_user(self, email: str, password_hash: str) -> int:
        """Cria um novo usuário"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
                """,
                (email, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtém usuário por email"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtém usuário por ID"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def update_user_password(self, user_id: int, password_hash: str) -> bool:
        """Atualiza senha do usuário"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE users 
                SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (password_hash, user_id)
            )
            conn.commit()
            return bool(cursor.rowcount)
    
    def get_user_skills(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Obtém habilidades do usuário"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT skills_json FROM user_skills WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            if not row or not row[0]:
                return None
            
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return None
    
    def upsert_user_skills(self, user_id: int, skills: List[Dict[str, Any]]) -> None:
        """Atualiza habilidades do usuário"""
        payload = json.dumps(skills or [])
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_skills (user_id, skills_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, payload)
            )
            conn.commit()
    
    def get_user_onboarding_completed(self, user_id: int) -> Optional[bool]:
        """Verifica se onboarding do usuário foi concluído"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT completed FROM user_onboarding WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            if not row:
                return None
            return bool(row[0])
    
    def set_user_onboarding_completed(self, user_id: int, completed: bool) -> None:
        """Define status de onboarding do usuário"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_onboarding (user_id, completed, completed_at)
                VALUES (?, ?, ?)
                """,
                (user_id, completed, sqlite3.Timestamp("now") if completed else None)
            )
            conn.commit()
    
    def upsert_user_api_key_ciphertext(self, user_id: int, api_key_ciphertext: str) -> None:
        """Atualiza chave API do usuário (legado)"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_connector_secrets (user_id, connector_key, secret_ciphertext, updated_at)
                VALUES (?, 'legacy_api_key', ?, CURRENT_TIMESTAMP)
                """,
                (user_id, api_key_ciphertext)
            )
            conn.commit()
    
    def add_user_llm_provider_key_ciphertext(
        self, user_id: int, provider: str, api_key_ciphertext: str, set_active: bool = True
    ) -> int:
        """Adiciona chave de provedor LLM para o usuário"""
        prov = str(provider or "").strip().lower()
        if not prov:
            raise ValueError("Provider não pode ser vazio")
        
        with self._connect() as conn:
            # Se set_active, desativa outras chaves do mesmo provider
            if set_active:
                conn.execute(
                    "UPDATE user_llm_provider_keys SET is_active = 0 WHERE user_id = ? AND provider = ?",
                    (user_id, prov)
                )
            
            cursor = conn.execute(
                """
                INSERT INTO user_llm_provider_keys 
                (user_id, provider, key_name, api_key_ciphertext, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, prov, f"{prov}_default", api_key_ciphertext, 1 if set_active else 0)
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
    
    def list_user_llm_provider_keys(
        self, user_id: int, provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista chaves LLM do usuário"""
        prov = str(provider or "").strip().lower()
        
        with self._connect() as conn:
            if prov:
                rows = conn.execute(
                    """
                    SELECT * FROM user_llm_provider_keys 
                    WHERE user_id = ? AND provider = ?
                    ORDER BY created_at DESC
                    """,
                    (user_id, prov)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM user_llm_provider_keys 
                    WHERE user_id = ?
                    ORDER BY provider, created_at DESC
                    """,
                    (user_id,)
                ).fetchall()
            
            out = []
            for row in rows:
                d = dict(row)
                d["is_active"] = bool(d["is_active"])
                out.append(d)
            return out
    
    def get_active_user_llm_provider_key_ciphertext(
        self, user_id: int, provider: str
    ) -> Optional[str]:
        """Obtém chave ativa do provedor LLM"""
        prov = str(provider or "").strip().lower()
        if not prov:
            return None
        
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT api_key_ciphertext FROM user_llm_provider_keys 
                WHERE user_id = ? AND provider = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, prov)
            ).fetchone()
            
            if not row:
                return None
            return str(row[0] or "")
    
    def set_active_user_llm_provider_key(
        self, user_id: int, provider: str, key_id: int
    ) -> bool:
        """Define chave ativa do provedor LLM"""
        prov = str(provider or "").strip().lower()
        if not prov:
            return False
        
        with self._connect() as conn:
            # Desativa todas as chaves do provider
            conn.execute(
                "UPDATE user_llm_provider_keys SET is_active = 0 WHERE user_id = ? AND provider = ?",
                (user_id, prov)
            )
            
            # Ativa a chave específica
            cursor = conn.execute(
                """
                UPDATE user_llm_provider_keys 
                SET is_active = 1 
                WHERE user_id = ? AND provider = ? AND id = ?
                """,
                (user_id, prov, key_id)
            )
            conn.commit()
            return True
    
    def delete_user_llm_provider_key(self, user_id: int, provider: str, key_id: int) -> bool:
        """Deleta chave LLM do usuário"""
        prov = str(provider or "").strip().lower()
        if not prov:
            return False
        
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM user_llm_provider_keys 
                WHERE user_id = ? AND provider = ? AND id = ?
                """,
                (user_id, prov, key_id)
            )
            conn.commit()
            return int(cursor.rowcount or 0) > 0
    
    def upsert_user_connector_secret_ciphertext(
        self, user_id: int, connector_key: str, secret_ciphertext: str
    ) -> None:
        """Atualiza segredo de conector do usuário"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_connector_secrets 
                (user_id, connector_key, secret_ciphertext, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, connector_key, secret_ciphertext)
            )
            conn.commit()
    
    def get_user_connector_secret_ciphertext(
        self, user_id: int, connector_key: str
    ) -> Optional[str]:
        """Obtém segredo de conector do usuário"""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT secret_ciphertext FROM user_connector_secrets 
                WHERE user_id = ? AND connector_key = ?
                """,
                (user_id, connector_key)
            ).fetchone()
            
            if not row:
                return None
            return str(row[0] or "")
