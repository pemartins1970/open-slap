"""
🔐 AUTH - Sistema de Autenticação Básico
Implementação de login/senha local com JWT
Segundo WINDSURF_AGENT.md - AUTH-01

CORREÇÃO: auth.py gerencia APENAS a tabela users.
Conversations e messages pertencem ao db.py — ter
schemas duplicados causava crash (coluna updated_at ausente).
"""

import os
import sqlite3
import secrets
import bcrypt as _bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException, status

# Configurações
SECRET_KEY = os.getenv("JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias


class AuthManager:
    """Gerenciador de autenticação"""

    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Garante que o banco de dados e tabela users existem"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Apenas a tabela de usuários — conversations/messages ficam com db.py
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica senha usando bcrypt direto — trunca em 72 bytes"""
        truncated = plain_password.encode('utf-8')[:72]
        return _bcrypt.checkpw(truncated, hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Gera hash usando bcrypt direto — trunca em 72 bytes"""
        truncated = password.encode('utf-8')[:72]
        return _bcrypt.hashpw(truncated, _bcrypt.gensalt()).decode('utf-8')

    def create_user(self, email: str, password: str) -> Dict[str, Any]:
        """Cria novo usuário"""
        try:
            hashed_password = self.get_password_hash(password)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                    (email, hashed_password)
                )
                user_id = cursor.lastrowid
                conn.commit()

            return {
                "id": user_id,
                "email": email,
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id, email, hashed_password FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if user and self.verify_password(password, user["hashed_password"]):
                return {
                    "id": user["id"],
                    "email": user["email"]
                }

        return None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Cria token JWT"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtém usuário por ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id, email, created_at FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            if user:
                return dict(user)

        return None


# Instância global
auth_manager = AuthManager()


# Funções auxiliares para FastAPI
def create_user(email: str, password: str) -> Dict[str, Any]:
    return auth_manager.create_user(email, password)

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    return auth_manager.authenticate_user(email, password)

def create_access_token(data: dict) -> str:
    return auth_manager.create_access_token(data)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    return auth_manager.verify_token(token)

def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    payload = verify_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    return auth_manager.get_user_by_id(int(user_id))
