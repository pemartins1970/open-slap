"""
🔐 AUTH - Sistema de Autenticação Básico
Implementação de login/senha local com JWT

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
from pathlib import Path

from jose import JWTError, jwt
from fastapi import HTTPException, status

# Configurações


def _load_or_create_jwt_secret() -> str:
    env_secret = str(os.getenv("JWT_SECRET") or "").strip()
    if env_secret:
        return env_secret
    secret_file = Path(os.path.expanduser("~")).resolve() / "OpenSlap" / ".jwt_secret"
    try:
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        if secret_file.exists():
            existing = secret_file.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        created = secrets.token_hex(32)
        secret_file.write_text(created, encoding="utf-8")
        return created
    except Exception:
        return secrets.token_hex(32)


SECRET_KEY = _load_or_create_jwt_secret()
ALGORITHM = "HS256"
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("OPENSLAP_JWT_EXPIRE_MINUTES") or "120")
except Exception:
    ACCESS_TOKEN_EXPIRE_MINUTES = 120


class AuthManager:
    """Gerenciador de autenticação"""

    def __init__(self, db_path: Optional[str] = None):
        env_db = (os.getenv("SLAP_DB_PATH") or os.getenv("OPENSLAP_DB_PATH") or "").strip()
        default_db = str((Path(__file__).resolve().parents[1] / "data" / "auth.db").resolve())
        self.db_path = str(db_path or env_db or default_db)
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_password_resets_email
                ON password_resets(email)
            """)
            conn.commit()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica senha usando bcrypt direto — trunca em 72 bytes"""
        truncated = plain_password.encode("utf-8")[:72]
        return _bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))

    def get_password_hash(self, password: str) -> str:
        """Gera hash usando bcrypt direto — trunca em 72 bytes"""
        truncated = password.encode("utf-8")[:72]
        return _bcrypt.hashpw(truncated, _bcrypt.gensalt()).decode("utf-8")

    def create_user(self, email: str, password: str) -> Dict[str, Any]:
        """Cria novo usuário"""
        try:
            email = (email or "").strip().lower()
            hashed_password = self.get_password_hash(password)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                    (email, hashed_password),
                )
                user_id = cursor.lastrowid
                conn.commit()

            return {
                "id": user_id,
                "email": email,
                "created_at": datetime.now().isoformat(),
            }
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado"
            )

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário"""
        email = (email or "").strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id, email, hashed_password FROM users WHERE email = ?", (email,)
            ).fetchone()

            if user and self.verify_password(password, user["hashed_password"]):
                return {"id": user["id"], "email": user["email"]}

        return None

    def create_password_reset(
        self, email: str, expires_minutes: int = 15
    ) -> Optional[str]:
        email = (email or "").strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,),
            ).fetchone()
            if not user:
                return None

            code = secrets.token_urlsafe(16)
            code_hash = self.get_password_hash(code)
            expires_at = int(
                (datetime.utcnow() + timedelta(minutes=expires_minutes)).timestamp()
            )
            conn.execute(
                "INSERT INTO password_resets (email, code_hash, expires_at) VALUES (?, ?, ?)",
                (email, code_hash, expires_at),
            )
            conn.commit()
            return code

    def consume_password_reset(self, email: str, code: str) -> bool:
        email = (email or "").strip().lower()
        code = (code or "").strip()
        now_ts = int(datetime.utcnow().timestamp())
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, code_hash, expires_at
                FROM password_resets
                WHERE email = ? AND used_at IS NULL AND expires_at > ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (email, now_ts),
            ).fetchone()
            if not row:
                return False

            expires_at = int(row["expires_at"] or 0)
            if expires_at <= now_ts:
                return False

            if not self.verify_password(code, row["code_hash"]):
                return False

            conn.execute(
                "UPDATE password_resets SET used_at = ? WHERE id = ?",
                (now_ts, row["id"]),
            )
            conn.commit()
            return True

    def set_password_by_email(self, email: str, new_password: str) -> bool:
        email = (email or "").strip().lower()
        hashed_password = self.get_password_hash(new_password)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE users SET hashed_password = ? WHERE email = ?",
                (hashed_password, email),
            )
            conn.commit()
            return cursor.rowcount > 0

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
        expires_minutes: Optional[int] = None,
    ) -> str:
        """Cria token JWT"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        elif expires_minutes is not None:
            try:
                m = int(expires_minutes)
            except Exception:
                m = ACCESS_TOKEN_EXPIRE_MINUTES
            m = max(1, m)
            expire = datetime.utcnow() + timedelta(minutes=m)
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
                "SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)
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


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    return auth_manager.create_access_token(data, expires_minutes=expires_minutes)


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


def create_password_reset(email: str) -> Optional[str]:
    return auth_manager.create_password_reset(email)


def confirm_password_reset(email: str, code: str, new_password: str) -> bool:
    if not auth_manager.consume_password_reset(email, code):
        return False
    return auth_manager.set_password_by_email(email, new_password)
