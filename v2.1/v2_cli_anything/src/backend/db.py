"""
🗄️ DB - Gerenciamento de Banco de Dados SQLite
Persistência de conversas e mensagens
"""

import os
import json
import re
import sqlite3
import secrets
from typing import List, Dict, Any, Optional
from pathlib import Path

_REDACTION_RULES = [
    (
        "github_token",
        re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("google_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{30,}\b")),
    ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b", re.IGNORECASE)),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9\-_]+?\.[A-Za-z0-9\-_]+?(\.[A-Za-z0-9\-_]+)?\b"),
    ),
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
    v = (os.getenv("SLAP_MEMORY_REDACTION_ENABLED") or "").strip().lower()
    return v not in {"0", "false", "no", "off"}


def _redact_text(value: Optional[str]) -> Optional[str]:
    if value is None or not isinstance(value, str) or value == "":
        return value
    if not _redaction_enabled():
        return value
    out = value
    for name, rx in _REDACTION_RULES:
        out = rx.sub(f"[REDACTED:{name}]", out)
    return out


class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""

    def __init__(self, db_path: Optional[str] = None):
        env_db = (
            os.getenv("SLAP_DB_PATH") or os.getenv("OPENSLAP_DB_PATH") or ""
        ).strip()
        default_db = str(
            (Path(__file__).resolve().parents[1] / "data" / "auth.db").resolve()
        )
        self.db_path = str(db_path or env_db or default_db)
        self._ensure_database()

    def _ensure_database(self):
        """Garante que as tabelas existem"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self._connect() as conn:
            # Tabela de conversas
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )
            try:
                cols = [
                    (r[1] if isinstance(r, (list, tuple)) else None)
                    for r in conn.execute("PRAGMA table_info(conversations)").fetchall()
                ]
                if "kind" not in cols:
                    conn.execute(
                        "ALTER TABLE conversations ADD COLUMN kind TEXT DEFAULT 'conversation'"
                    )
                if "source" not in cols:
                    conn.execute(
                        "ALTER TABLE conversations ADD COLUMN source TEXT DEFAULT 'user'"
                    )
                    try:
                        conn.execute(
                            "UPDATE conversations SET source='user' WHERE source IS NULL OR TRIM(source)=''"
                        )
                    except Exception:
                        pass
                try:
                    conn.execute(
                        """
                        UPDATE conversations
                        SET kind = 'conversation'
                        WHERE kind = 'task'
                          AND (
                            LOWER(title) LIKE '%agente%'
                            OR LOWER(title) LIKE '%agent%'
                          )
                          AND (
                            LOWER(title) LIKE '[auto]%'
                            OR session_id LIKE 'orch-%'
                            OR EXISTS (
                              SELECT 1 FROM messages m
                              WHERE m.conversation_id = conversations.id
                                AND LOWER(m.content) LIKE '%criar um novo agente%'
                              LIMIT 1
                            )
                          )
                    """
                    )
                except Exception:
                    pass
            except Exception:
                pass

            # Tabela de mensagens
            conn.execute(
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

            # Índices para performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_kind ON conversations(user_id, kind)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_source ON conversations(user_id, source)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)"
            )

            conn.execute(
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_conversation_id INTEGER,
                    source_message_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """
            )
            try:
                cols = [
                    (r[1] if isinstance(r, (list, tuple)) else None)
                    for r in conn.execute("PRAGMA table_info(task_todos)").fetchall()
                ]
                if "kind" not in cols:
                    conn.execute("ALTER TABLE task_todos ADD COLUMN kind TEXT DEFAULT 'step'")
                if "actor" not in cols:
                    conn.execute("ALTER TABLE task_todos ADD COLUMN actor TEXT DEFAULT 'human'")
                if "origin" not in cols:
                    conn.execute("ALTER TABLE task_todos ADD COLUMN origin TEXT DEFAULT 'user'")
                if "scope" not in cols:
                    conn.execute("ALTER TABLE task_todos ADD COLUMN scope TEXT DEFAULT 'project'")
                if "priority" not in cols:
                    conn.execute("ALTER TABLE task_todos ADD COLUMN priority TEXT DEFAULT 'medium'")
                if "due_at" not in cols:
                    conn.execute("ALTER TABLE task_todos ADD COLUMN due_at TEXT")
                if "parent_todo_id" not in cols:
                    conn.execute(
                        "ALTER TABLE task_todos ADD COLUMN parent_todo_id INTEGER"
                    )
                if "delivery_path" not in cols:
                    conn.execute(
                        "ALTER TABLE task_todos ADD COLUMN delivery_path TEXT"
                    )
                if "artifact_meta" not in cols:
                    conn.execute(
                        "ALTER TABLE task_todos ADD COLUMN artifact_meta TEXT"
                    )
                if "source_conversation_id" not in cols:
                    conn.execute(
                        "ALTER TABLE task_todos ADD COLUMN source_conversation_id INTEGER"
                    )
                if "source_message_id" not in cols:
                    conn.execute(
                        "ALTER TABLE task_todos ADD COLUMN source_message_id INTEGER"
                    )
            except Exception:
                pass
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_user_status ON task_todos(user_id, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_user_scope_status ON task_todos(user_id, scope, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_user_actor_status ON task_todos(user_id, actor, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_user_kind ON task_todos(user_id, kind)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_conversation ON task_todos(conversation_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_source_conversation ON task_todos(source_conversation_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_source_message ON task_todos(source_message_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_parent ON task_todos(parent_todo_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_todos_conversation_parent ON task_todos(conversation_id, parent_todo_id)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS answer_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_hash TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_answer_cache_user_hash ON answer_cache(user_id, question_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_answer_cache_created_at ON answer_cache(created_at)"
            )

            conn.execute(
                """
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
            """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_friction_events_sent ON friction_events(sent)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_friction_events_code ON friction_events(event_code)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_friction_events_layer ON friction_events(event_layer)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_llm_settings (
                    user_id INTEGER PRIMARY KEY,
                    llm_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_security_settings (
                    user_id INTEGER PRIMARY KEY,
                    security_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_command_autoapprove (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    command_norm TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_command_autoapprove_user_cmd ON user_command_autoapprove(user_id, command_norm)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_api_secrets (
                    user_id INTEGER PRIMARY KEY,
                    api_key_ciphertext TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_llm_provider_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    api_key_ciphertext TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_llm_provider_keys_user_provider ON user_llm_provider_keys(user_id, provider)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_llm_provider_keys_user_provider_active ON user_llm_provider_keys(user_id, provider, is_active)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_system_profile (
                    user_id INTEGER PRIMARY KEY,
                    profile_md TEXT NOT NULL,
                    profile_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_onboarding (
                    user_id INTEGER PRIMARY KEY,
                    completed INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_kv_cache (
                    cache_key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_soul (
                    user_id INTEGER PRIMARY KEY,
                    soul_json TEXT NOT NULL,
                    soul_markdown TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_soul_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_soul_events_user_id ON user_soul_events(user_id)"
            )

            # ── Memory Phase 2-4: salience, decay, momentum fields ────────────
            try:
                conn.execute(
                    "ALTER TABLE user_soul_events ADD COLUMN salience REAL DEFAULT 0.5"
                )
            except Exception:
                pass
            try:
                conn.execute(
                    "ALTER TABLE user_soul_events ADD COLUMN confidence REAL DEFAULT 0.8"
                )
            except Exception:
                pass
            try:
                conn.execute(
                    "ALTER TABLE user_soul_events ADD COLUMN last_used_at TIMESTAMP"
                )
            except Exception:
                pass
            try:
                conn.execute(
                    "ALTER TABLE user_soul_events ADD COLUMN pinned INTEGER DEFAULT 0"
                )
            except Exception:
                pass
            try:
                conn.execute(
                    "ALTER TABLE user_soul_events ADD COLUMN decay_rate REAL DEFAULT 0.05"
                )
            except Exception:
                pass

            # ── Message feedback (thumbs up/down) ─────────────────────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE,
                    UNIQUE (user_id, message_id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_user ON message_feedback(user_id)"
            )

            # ── Expert ratings (aggregate, for router weighting) ──────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expert_ratings (
                    user_id INTEGER NOT NULL,
                    expert_id TEXT NOT NULL,
                    total_responses INTEGER DEFAULT 0,
                    positive INTEGER DEFAULT 0,
                    negative INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, expert_id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # ── Orchestration log ─────────────────────────────────────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestration_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    parent_conversation_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running','completed','failed')),
                    log_json TEXT DEFAULT '[]',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # ── Plan tasks (plan→build breakdown) ────────────────────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plan_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    parent_conversation_id INTEGER NOT NULL,
                    conversation_id INTEGER,
                    title TEXT NOT NULL,
                    skill_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'active', 'done', 'skipped', 'failed')),
                    position INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (parent_conversation_id) REFERENCES conversations (id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_plan_tasks_conv ON plan_tasks(parent_conversation_id)"
            )

            # ── Projects (shared context across tasks) ────────────────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    context_md TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id)"
            )
            try:
                conn.execute(
                    "ALTER TABLE conversations ADD COLUMN project_id INTEGER REFERENCES projects(id)"
                )
            except Exception:
                pass

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_skills (
                    user_id INTEGER PRIMARY KEY,
                    skills_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_connector_secrets (
                    user_id INTEGER NOT NULL,
                    connector_key TEXT NOT NULL,
                    secret_ciphertext TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, connector_key),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_link_codes (
                    code TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_user ON telegram_link_codes(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_expires ON telegram_link_codes(expires_at)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    telegram_user_id TEXT NOT NULL,
                    chat_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revoked_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telegram_links_user ON telegram_links(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telegram_links_pair ON telegram_links(telegram_user_id, chat_id)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cli_command_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_id INTEGER,
                    conversation_id INTEGER NOT NULL,
                    app_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    command_executed TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('success','error')),
                    output TEXT,
                    visual_state_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cli_logs_user ON cli_command_logs(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cli_logs_project ON cli_command_logs(project_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cli_logs_conversation ON cli_command_logs(conversation_id)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_cli_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    conversation_id INTEGER NOT NULL,
                    execution_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cli_summaries_user_exec ON conversation_cli_summaries(user_id, execution_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cli_summaries_conversation ON conversation_cli_summaries(conversation_id)"
            )

            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                    USING fts5(content, conversation_id UNINDEXED, message_id UNINDEXED, tokenize='unicode61')
                """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS messages_fts_ai
                    AFTER INSERT ON messages
                    BEGIN
                      INSERT INTO messages_fts(content, conversation_id, message_id)
                      VALUES (new.content, new.conversation_id, new.id);
                    END
                """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS messages_fts_ad
                    AFTER DELETE ON messages
                    BEGIN
                      DELETE FROM messages_fts WHERE message_id = old.id;
                    END
                """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS messages_fts_au
                    AFTER UPDATE OF content ON messages
                    BEGIN
                      UPDATE messages_fts SET content = new.content WHERE message_id = new.id;
                    END
                """
                )
            except Exception:
                pass

            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS soul_events_fts
                    USING fts5(content, user_id UNINDEXED, event_id UNINDEXED, tokenize='unicode61')
                """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS soul_events_fts_ai
                    AFTER INSERT ON user_soul_events
                    BEGIN
                      INSERT INTO soul_events_fts(content, user_id, event_id)
                      VALUES (new.content, new.user_id, new.id);
                    END
                """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS soul_events_fts_ad
                    AFTER DELETE ON user_soul_events
                    BEGIN
                      DELETE FROM soul_events_fts WHERE event_id = old.id;
                    END
                """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS soul_events_fts_au
                    AFTER UPDATE OF content ON user_soul_events
                    BEGIN
                      UPDATE soul_events_fts SET content = new.content WHERE event_id = new.id;
                    END
                """
                )
            except Exception:
                pass

            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        try:
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        try:
            conn.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass
        return conn

    def create_conversation(
        self,
        user_id: int,
        session_id: str,
        title: str,
        kind: str = "conversation",
        source: str = "user",
    ) -> int:
        """Cria nova conversa"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (user_id, session_id, title, kind, source) VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    session_id,
                    _redact_text(title) or "",
                    kind or "conversation",
                    (str(source or "user").strip().lower() or "user"),
                ),
            )
            conversation_id = cursor.lastrowid
            conn.commit()

        return conversation_id

    def get_user_conversations(
        self, user_id: int, kind: Optional[str] = None, source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtém conversas do usuário"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            where = "WHERE user_id = ?"
            args: List[Any] = [user_id]
            if kind:
                where += " AND kind = ?"
                args.append(kind)
            if source:
                where += " AND source = ?"
                args.append(source)
            conversations = conn.execute(
                f"""
                SELECT id, session_id, title, created_at, updated_at, kind, source,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count,
                       (SELECT COUNT(*) FROM task_todos t WHERE t.conversation_id = conversations.id AND t.status = 'pending') as pending_todo_count,
                       (SELECT COUNT(*) FROM task_todos t WHERE t.conversation_id = conversations.id AND t.status = 'done') as done_todo_count
                FROM conversations
                {where}
                ORDER BY updated_at DESC
            """,
                tuple(args),
            ).fetchall()

            return [dict(conv) for conv in conversations]

    def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Obtém mensagens de uma conversa"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            messages = conn.execute(
                """
                SELECT id, role, content, expert_id, provider, model, tokens, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """,
                (conversation_id,),
            ).fetchall()

            return [dict(msg) for msg in messages]

    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, role, content, expert_id, provider, model, tokens, created_at
                FROM messages
                WHERE id = ?
            """,
                (int(message_id),),
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
        tokens: Optional[int] = None,
    ) -> int:
        """Salva mensagem"""
        with self._connect() as conn:
            safe_content = _redact_text(content) or ""
            cursor = conn.execute(
                """
                INSERT INTO messages
                (conversation_id, role, content, expert_id, provider, model, tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    conversation_id,
                    role,
                    safe_content,
                    expert_id,
                    provider,
                    model,
                    tokens,
                ),
            )

            message_id = cursor.lastrowid

            # Atualizar timestamp da conversa
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,),
            )

            conn.commit()

        return message_id

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Deleta conversa e suas mensagens"""
        with sqlite3.connect(self.db_path) as conn:
            # Verificar se a conversa pertence ao usuário
            conv = conn.execute(
                "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            ).fetchone()

            if not conv:
                return False

            # Deletar mensagens primeiro (foreign key)
            conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
            )

            # Deletar conversa
            conn.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )

            conn.commit()

        return True

    def update_conversation_title(
        self, conversation_id: int, user_id: int, title: str
    ) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """,
                (_redact_text(title) or "", conversation_id, user_id),
            )
            conn.commit()
            return bool(cur.rowcount)

    def search_user_messages(
        self,
        user_id: int,
        query: str,
        limit: int = 50,
        kind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = str(query or "").strip()
        if not q:
            return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            where = "c.user_id = ?"
            args: List[Any] = [user_id, q, int(limit)]
            if kind:
                where += " AND c.kind = ?"
                args = [user_id, kind, q, int(limit)]
            rows = conn.execute(
                f"""
                SELECT
                  f.message_id as message_id,
                  f.conversation_id as conversation_id,
                  c.title as conversation_title,
                  c.session_id as session_id,
                  c.kind as conversation_kind,
                  c.created_at as conversation_created_at,
                  c.updated_at as conversation_updated_at,
                  (SELECT created_at FROM messages WHERE id = f.message_id) as message_created_at,
                  snippet(messages_fts, 0, '', '', '…', 16) as snippet
                FROM messages_fts f
                JOIN conversations c ON c.id = f.conversation_id
                WHERE {where} AND messages_fts MATCH ?
                ORDER BY message_created_at DESC
                LIMIT ?
            """,
                tuple(args),
            ).fetchall()
            return [dict(r) for r in rows]

    def add_task_todo(
        self,
        user_id: int,
        conversation_id: int,
        text: str,
        kind: Optional[str] = None,
        actor: Optional[str] = None,
        origin: Optional[str] = None,
        scope: Optional[str] = None,
        priority: Optional[str] = None,
        due_at: Optional[str] = None,
        parent_todo_id: Optional[int] = None,
        delivery_path: Optional[str] = None,
        artifact_meta: Optional[Any] = None,
        source_conversation_id: Optional[int] = None,
        source_message_id: Optional[int] = None,
    ) -> int:
        kind_v = str(kind or "step").strip().lower() or "step"
        actor_v = str(actor or "human").strip().lower() or "human"
        origin_v = str(origin or "user").strip().lower() or "user"
        scope_v = str(scope or "project").strip().lower() or "project"
        priority_v = str(priority or "medium").strip().lower() or "medium"
        due_at_v = str(due_at).strip() if due_at else None
        artifact_meta_json = None
        if artifact_meta is not None:
            try:
                artifact_meta_json = json.dumps(artifact_meta, ensure_ascii=False)
            except Exception:
                artifact_meta_json = None
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO task_todos (
                  user_id, conversation_id, text,
                  kind, actor, origin, scope, priority, due_at,
                  parent_todo_id, delivery_path, artifact_meta,
                  source_conversation_id, source_message_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    conversation_id,
                    _redact_text(text) or "",
                    kind_v,
                    actor_v,
                    origin_v,
                    scope_v,
                    priority_v,
                    due_at_v,
                    int(parent_todo_id) if parent_todo_id is not None else None,
                    (str(delivery_path).strip() if delivery_path else None),
                    artifact_meta_json,
                    int(source_conversation_id)
                    if source_conversation_id is not None
                    else None,
                    int(source_message_id) if source_message_id is not None else None,
                ),
            )
            todo_id = cur.lastrowid
            conn.commit()
            return int(todo_id)

    def list_task_todos(
        self,
        user_id: int,
        conversation_id: int,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            where = "user_id = ? AND conversation_id = ?"
            args: List[Any] = [user_id, conversation_id]
            if status:
                where += " AND status = ?"
                args.append(status)
            rows = conn.execute(
                f"""
                SELECT
                  id, conversation_id, text, status, kind, actor, origin, scope, priority, due_at, created_at, updated_at,
                  parent_todo_id, delivery_path, artifact_meta,
                  source_conversation_id, source_message_id
                FROM task_todos
                WHERE {where}
                ORDER BY created_at DESC
            """,
                tuple(args),
            ).fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                try:
                    d["artifact_meta"] = (
                        json.loads(d.get("artifact_meta") or "{}")
                        if d.get("artifact_meta")
                        else None
                    )
                except Exception:
                    d["artifact_meta"] = None
                out.append(d)
            return out

    def list_pending_todos(self, user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                  t.id,
                  t.conversation_id,
                  t.text,
                  t.status,
                  t.kind,
                  t.actor,
                  t.origin,
                  t.scope,
                  t.priority,
                  t.due_at,
                  t.created_at,
                  t.updated_at,
                  t.parent_todo_id,
                  t.delivery_path,
                  t.artifact_meta,
                  t.source_conversation_id,
                  t.source_message_id,
                  c.title as task_title,
                  c.session_id as session_id,
                  c.updated_at as task_updated_at,
                  sc.title as source_conversation_title,
                  sc.session_id as source_session_id,
                  sc.kind as source_conversation_kind,
                  sm.created_at as source_message_created_at
                FROM task_todos t
                JOIN conversations c ON c.id = t.conversation_id
                LEFT JOIN conversations sc ON sc.id = t.source_conversation_id
                LEFT JOIN messages sm ON sm.id = t.source_message_id
                WHERE t.user_id = ? AND t.status = 'pending' AND c.kind = 'task'
                ORDER BY t.created_at DESC
            """,
                (user_id,),
            ).fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                try:
                    d["artifact_meta"] = (
                        json.loads(d.get("artifact_meta") or "{}")
                        if d.get("artifact_meta")
                        else None
                    )
                except Exception:
                    d["artifact_meta"] = None
                out.append(d)
            return out

    def update_task_todo(
        self,
        user_id: int,
        todo_id: int,
        text: Optional[str] = None,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        actor: Optional[str] = None,
        origin: Optional[str] = None,
        scope: Optional[str] = None,
        priority: Optional[str] = None,
        due_at: Optional[str] = None,
        parent_todo_id: Optional[int] = None,
        delivery_path: Optional[str] = None,
        artifact_meta: Optional[Any] = None,
        source_conversation_id: Optional[int] = None,
        source_message_id: Optional[int] = None,
    ) -> bool:
        sets: List[str] = []
        args: List[Any] = []
        if text is not None:
            sets.append("text = ?")
            args.append(_redact_text(text) or "")
        if status is not None:
            sets.append("status = ?")
            args.append(status)
        if kind is not None:
            sets.append("kind = ?")
            args.append(str(kind).strip().lower())
        if actor is not None:
            sets.append("actor = ?")
            args.append(str(actor).strip().lower())
        if origin is not None:
            sets.append("origin = ?")
            args.append(str(origin).strip().lower())
        if scope is not None:
            sets.append("scope = ?")
            args.append(str(scope).strip().lower())
        if priority is not None:
            sets.append("priority = ?")
            args.append(str(priority).strip().lower())
        if due_at is not None:
            sets.append("due_at = ?")
            args.append((str(due_at).strip() if due_at else None))
        if parent_todo_id is not None:
            sets.append("parent_todo_id = ?")
            args.append(int(parent_todo_id))
        if delivery_path is not None:
            sets.append("delivery_path = ?")
            args.append((str(delivery_path).strip() if delivery_path else None))
        if artifact_meta is not None:
            sets.append("artifact_meta = ?")
            try:
                args.append(json.dumps(artifact_meta, ensure_ascii=False))
            except Exception:
                args.append(None)
        if source_conversation_id is not None:
            sets.append("source_conversation_id = ?")
            args.append(int(source_conversation_id))
        if source_message_id is not None:
            sets.append("source_message_id = ?")
            args.append(int(source_message_id))
        if not sets:
            return False
        sets.append("updated_at = CURRENT_TIMESTAMP")
        args.extend([todo_id, user_id])
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                f"""
                UPDATE task_todos
                SET {", ".join(sets)}
                WHERE id = ? AND user_id = ?
            """,
                tuple(args),
            )
            conn.commit()
            return bool(cur.rowcount)

    def get_task_todo(self, user_id: int, todo_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT
                  id, conversation_id, text, status, created_at, updated_at,
                  parent_todo_id, delivery_path, artifact_meta,
                  source_conversation_id, source_message_id
                FROM task_todos
                WHERE id = ? AND user_id = ?
                LIMIT 1
            """,
                (int(todo_id), int(user_id)),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            try:
                d["artifact_meta"] = (
                    json.loads(d.get("artifact_meta") or "{}")
                    if d.get("artifact_meta")
                    else None
                )
            except Exception:
                d["artifact_meta"] = None
            return d

    def get_conversation_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém conversa ativa por session_id"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conversation = conn.execute(
                """
                SELECT id, user_id, session_id, title, kind, source, created_at, updated_at
                FROM conversations
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (session_id,),
            ).fetchone()

            if conversation:
                return dict(conversation)

        return None

    def get_conversation_by_session_for_user(
        self, user_id: int, session_id: str
    ) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conversation = conn.execute(
                """
                SELECT id, user_id, session_id, title, kind, source, created_at, updated_at
                FROM conversations
                WHERE session_id = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (str(session_id), int(user_id)),
            ).fetchone()
            if not conversation:
                return None
            return dict(conversation)

    def get_user_skills(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT skills_json FROM user_skills WHERE user_id = ?",
                (int(user_id),),
            ).fetchone()
            if not row:
                return None
            try:
                parsed = json.loads(row[0] or "[]")
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return None
            return None

    def upsert_user_skills(self, user_id: int, skills: List[Dict[str, Any]]) -> None:
        payload = json.dumps(skills or [])
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_skills (user_id, skills_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  skills_json=excluded.skills_json,
                  updated_at=CURRENT_TIMESTAMP
            """,
                (int(user_id), payload),
            )
            conn.commit()

    def upsert_user_api_key_ciphertext(
        self, user_id: int, api_key_ciphertext: str
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_api_secrets (user_id, api_key_ciphertext, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  api_key_ciphertext=excluded.api_key_ciphertext,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (int(user_id), str(api_key_ciphertext)),
            )
            conn.commit()

    def add_user_llm_provider_key_ciphertext(
        self, user_id: int, provider: str, api_key_ciphertext: str, set_active: bool = True
    ) -> int:
        prov = str(provider or "").strip().lower()
        if not prov:
            raise ValueError("provider required")
        with sqlite3.connect(self.db_path) as conn:
            if set_active:
                conn.execute(
                    """
                    UPDATE user_llm_provider_keys
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND provider = ?
                    """,
                    (int(user_id), prov),
                )
            cur = conn.execute(
                """
                INSERT INTO user_llm_provider_keys (user_id, provider, api_key_ciphertext, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (int(user_id), prov, str(api_key_ciphertext), 1 if set_active else 0),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def list_user_llm_provider_keys(
        self, user_id: int, provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        prov = str(provider or "").strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            if prov:
                rows = conn.execute(
                    """
                    SELECT id, provider, is_active, created_at, updated_at
                    FROM user_llm_provider_keys
                    WHERE user_id = ? AND provider = ?
                    ORDER BY id DESC
                    """,
                    (int(user_id), prov),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, provider, is_active, created_at, updated_at
                    FROM user_llm_provider_keys
                    WHERE user_id = ?
                    ORDER BY provider ASC, id DESC
                    """,
                    (int(user_id),),
                ).fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows or []:
                out.append(
                    {
                        "id": int(r[0]),
                        "provider": str(r[1] or ""),
                        "is_active": bool(r[2]),
                        "created_at": r[3],
                        "updated_at": r[4],
                    }
                )
            return out

    def get_active_user_llm_provider_key_ciphertext(
        self, user_id: int, provider: str
    ) -> Optional[str]:
        prov = str(provider or "").strip().lower()
        if not prov:
            return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT api_key_ciphertext
                FROM user_llm_provider_keys
                WHERE user_id = ? AND provider = ? AND is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(user_id), prov),
            ).fetchone()
            if not row:
                return None
            return str(row[0] or "")

    def set_active_user_llm_provider_key(
        self, user_id: int, provider: str, key_id: int
    ) -> bool:
        prov = str(provider or "").strip().lower()
        if not prov:
            return False
        kid = int(key_id)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM user_llm_provider_keys WHERE id = ? AND user_id = ? AND provider = ?",
                (kid, int(user_id), prov),
            ).fetchone()
            if not row:
                return False
            conn.execute(
                """
                UPDATE user_llm_provider_keys
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND provider = ?
                """,
                (int(user_id), prov),
            )
            conn.execute(
                """
                UPDATE user_llm_provider_keys
                SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND provider = ?
                """,
                (kid, int(user_id), prov),
            )
            conn.commit()
            return True

    def delete_user_llm_provider_key(self, user_id: int, provider: str, key_id: int) -> bool:
        prov = str(provider or "").strip().lower()
        if not prov:
            return False
        kid = int(key_id)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT is_active FROM user_llm_provider_keys WHERE id = ? AND user_id = ? AND provider = ?",
                (kid, int(user_id), prov),
            ).fetchone()
            if not row:
                return False
            was_active = bool(row[0])
            cur = conn.execute(
                "DELETE FROM user_llm_provider_keys WHERE id = ? AND user_id = ? AND provider = ?",
                (kid, int(user_id), prov),
            )
            if was_active:
                next_row = conn.execute(
                    """
                    SELECT id FROM user_llm_provider_keys
                    WHERE user_id = ? AND provider = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (int(user_id), prov),
                ).fetchone()
                if next_row:
                    conn.execute(
                        """
                        UPDATE user_llm_provider_keys
                        SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ? AND provider = ?
                        """,
                        (int(next_row[0]), int(user_id), prov),
                    )
            conn.commit()
            return int(cur.rowcount or 0) > 0

    def get_user_onboarding_completed(self, user_id: int) -> Optional[bool]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT completed FROM user_onboarding WHERE user_id = ?",
                (int(user_id),),
            ).fetchone()
            if row is None:
                return None
            return bool(row[0])

    def set_user_onboarding_completed(self, user_id: int, completed: bool) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_onboarding (user_id, completed, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  completed=excluded.completed,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (int(user_id), 1 if bool(completed) else 0),
            )
            conn.commit()

    def upsert_user_connector_secret_ciphertext(
        self, user_id: int, connector_key: str, secret_ciphertext: str
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_connector_secrets (user_id, connector_key, secret_ciphertext, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, connector_key) DO UPDATE SET
                  secret_ciphertext=excluded.secret_ciphertext,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (
                    int(user_id),
                    str(connector_key or "").strip().lower(),
                    str(secret_ciphertext),
                ),
            )
            conn.commit()

    def get_user_connector_secret_ciphertext(
        self, user_id: int, connector_key: str
    ) -> Optional[str]:
        key = str(connector_key or "").strip().lower()
        if not key:
            return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT secret_ciphertext
                FROM user_connector_secrets
                WHERE user_id = ? AND connector_key = ?
                """,
                (int(user_id), key),
            ).fetchone()
            if not row:
                return None
            return str(row[0] or "")

    def delete_user_connector_secret(self, user_id: int, connector_key: str) -> bool:
        key = str(connector_key or "").strip().lower()
        if not key:
            return False
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM user_connector_secrets WHERE user_id = ? AND connector_key = ?",
                (int(user_id), key),
            )
            conn.commit()
            return int(cursor.rowcount or 0) > 0

    def list_user_connector_keys(self, user_id: int) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT connector_key FROM user_connector_secrets WHERE user_id = ?",
                (int(user_id),),
            ).fetchall()
            return [str(r[0] or "") for r in (rows or []) if str(r[0] or "").strip()]

    def create_telegram_link_code(
        self, user_id: int, ttl_seconds: int = 600
    ) -> Dict[str, Any]:
        ttl = int(ttl_seconds or 600)
        if ttl < 60:
            ttl = 60
        now_epoch = int(__import__("time").time())
        code = secrets.token_urlsafe(16).rstrip("=")
        expires_at = now_epoch + ttl
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO telegram_link_codes (code, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (str(code), int(user_id), int(expires_at)),
            )
            conn.commit()
        return {"code": code, "expires_at": expires_at}

    def consume_telegram_link_code(self, code: str) -> Optional[int]:
        cleaned = str(code or "").strip()
        if not cleaned:
            return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT user_id
                FROM telegram_link_codes
                WHERE code = ?
                  AND used_at IS NULL
                  AND expires_at > CAST(strftime('%s','now') AS INTEGER)
                """,
                (cleaned,),
            ).fetchone()
            if not row:
                return None
            user_id = int(row[0])
            conn.execute(
                "UPDATE telegram_link_codes SET used_at = CURRENT_TIMESTAMP WHERE code = ?",
                (cleaned,),
            )
            conn.commit()
            return user_id

    def upsert_telegram_link(
        self, user_id: int, telegram_user_id: str, chat_id: str
    ) -> None:
        tuid = str(telegram_user_id or "").strip()
        cid = str(chat_id or "").strip()
        if not (tuid and cid):
            raise ValueError("telegram_user_id e chat_id são obrigatórios")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE telegram_links
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE telegram_user_id = ? AND chat_id = ? AND revoked_at IS NULL
                """,
                (tuid, cid),
            )
            conn.execute(
                """
                INSERT INTO telegram_links (user_id, telegram_user_id, chat_id)
                VALUES (?, ?, ?)
                """,
                (int(user_id), tuid, cid),
            )
            conn.commit()

    def revoke_telegram_link(self, telegram_user_id: str, chat_id: str) -> bool:
        tuid = str(telegram_user_id or "").strip()
        cid = str(chat_id or "").strip()
        if not (tuid and cid):
            return False
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE telegram_links
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE telegram_user_id = ? AND chat_id = ? AND revoked_at IS NULL
                """,
                (tuid, cid),
            )
            conn.commit()
            return int(cursor.rowcount or 0) > 0

    def list_telegram_links(self, user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT telegram_user_id, chat_id, created_at, revoked_at
                FROM telegram_links
                WHERE user_id = ? AND revoked_at IS NULL
                ORDER BY created_at DESC
                """,
                (int(user_id),),
            ).fetchall()
            return [dict(r) for r in (rows or [])]

    def get_telegram_linked_user_id(
        self, telegram_user_id: str, chat_id: str
    ) -> Optional[int]:
        tuid = str(telegram_user_id or "").strip()
        cid = str(chat_id or "").strip()
        if not (tuid and cid):
            return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT user_id
                FROM telegram_links
                WHERE telegram_user_id = ? AND chat_id = ? AND revoked_at IS NULL
                LIMIT 1
                """,
                (tuid, cid),
            ).fetchone()
            return int(row[0]) if row else None

    def log_cli_command(
        self,
        *,
        user_id: int,
        conversation_id: int,
        app_name: str,
        action: str,
        command_executed: str,
        status: str,
        output: Optional[str] = None,
        visual_state_summary: Optional[str] = None,
    ) -> int:
        uid = int(user_id)
        conv_id = int(conversation_id)
        app = str(app_name or "").strip()
        act = str(action or "").strip()
        cmd = str(command_executed or "").strip()
        st = str(status or "").strip().lower()
        if not (uid and conv_id and app and act and cmd and st in {"success", "error"}):
            raise ValueError("Parâmetros inválidos para log_cli_command")
        with sqlite3.connect(self.db_path) as conn:
            project_id = None
            try:
                row = conn.execute(
                    "SELECT project_id FROM conversations WHERE id = ? AND user_id = ?",
                    (conv_id, uid),
                ).fetchone()
                if row and row[0]:
                    project_id = int(row[0])
            except Exception:
                project_id = None
            cur = conn.execute(
                """
                INSERT INTO cli_command_logs
                    (user_id, project_id, conversation_id, app_name, action, command_executed, status, output, visual_state_summary)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    project_id,
                    conv_id,
                    app,
                    act,
                    _redact_text(cmd),
                    st,
                    _redact_text(output),
                    _redact_text(visual_state_summary),
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_user_api_key_ciphertext(self, user_id: int) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT api_key_ciphertext FROM user_api_secrets WHERE user_id = ?",
                (int(user_id),),
            ).fetchone()
            if not row:
                return None
            return str(row[0] or "")

    def delete_user_api_key(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM user_api_secrets WHERE user_id = ?", (int(user_id),)
            )
            conn.commit()
            return int(cursor.rowcount or 0) > 0

    def upsert_user_system_profile(
        self,
        user_id: int,
        profile_md: str,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        profile_json = json.dumps(profile_data or {}, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_system_profile (user_id, profile_md, profile_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  profile_md=excluded.profile_md,
                  profile_json=excluded.profile_json,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (int(user_id), profile_md or "", profile_json),
            )
            conn.commit()

    def get_user_system_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT profile_md, profile_json, updated_at FROM user_system_profile WHERE user_id = ?",
                (int(user_id),),
            ).fetchone()
            if not row:
                return None
            data = {}
            try:
                data = json.loads(row["profile_json"] or "{}")
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                data = {}
            return {
                "markdown": row["profile_md"] or "",
                "data": data,
                "updated_at": row["updated_at"],
            }

    def update_user_system_profile_data(
        self, user_id: int, patch: Dict[str, Any]
    ) -> Dict[str, Any]:
        current = self.get_user_system_profile(user_id) or {
            "markdown": "",
            "data": {},
            "updated_at": None,
        }
        current_data = (
            current.get("data") if isinstance(current.get("data"), dict) else {}
        )
        merged = {**(current_data or {}), **(patch or {})}
        self.upsert_user_system_profile(
            int(user_id), current.get("markdown") or "", merged
        )
        return self.get_user_system_profile(int(user_id)) or {
            "markdown": current.get("markdown") or "",
            "data": merged,
            "updated_at": None,
        }

    def delete_user_system_profile(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM user_system_profile WHERE user_id = ?", (int(user_id),)
            )
            conn.commit()
            return int(cursor.rowcount or 0) > 0

    def upsert_system_kv_cache(self, cache_key: str, value: Dict[str, Any]) -> None:
        key = str(cache_key or "").strip()
        if not key:
            return
        value_json = json.dumps(value or {}, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO system_kv_cache (cache_key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(cache_key) DO UPDATE SET
                  value_json=excluded.value_json,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (key, value_json),
            )
            conn.commit()

    def get_system_kv_cache(
        self, cache_key: str, max_age_s: int = 21600
    ) -> Optional[Dict[str, Any]]:
        key = str(cache_key or "").strip()
        if not key:
            return None
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT value_json, updated_at
                FROM system_kv_cache
                WHERE cache_key = ?
                  AND updated_at >= datetime('now', ?)
                LIMIT 1
                """,
                (key, f"-{int(max_age_s)} seconds"),
            ).fetchone()
            if not row:
                return None
            data = {}
            try:
                data = json.loads(row["value_json"] or "{}")
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                data = {}
            data["_updated_at"] = row["updated_at"]
            return data

    def get_cached_answer(
        self, user_id: int, question_hash: str, max_age_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        if not question_hash:
            return None
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT answer, created_at
                FROM answer_cache
                WHERE user_id = ? AND question_hash = ?
                  AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (int(user_id), str(question_hash), f"-{int(max_age_hours)} hours"),
            ).fetchone()
            if not row:
                return None
            return {"answer": row["answer"], "created_at": row["created_at"]}

    def put_cached_answer(
        self, user_id: int, question_hash: str, question: str, answer: str
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO answer_cache (user_id, question_hash, question, answer) VALUES (?, ?, ?, ?)",
                (
                    int(user_id),
                    str(question_hash),
                    _redact_text(question) or "",
                    _redact_text(answer) or "",
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def search_user_memory(
        self, user_id: int, query: str, limit: int = 6
    ) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        limit_n = max(1, int(limit))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows: List[sqlite3.Row] = []
            try:
                rows = conn.execute(
                    """
                    SELECT 'chat' as src, m.content as content, m.created_at as created_at
                    FROM messages_fts f
                    JOIN messages m ON m.id = f.message_id
                    JOIN conversations c ON c.id = m.conversation_id
                    WHERE c.user_id = ? AND messages_fts MATCH ?
                    ORDER BY m.created_at DESC
                    LIMIT ?
                    """,
                    (int(user_id), q, limit_n),
                ).fetchall()
            except Exception:
                like = f"%{q[:80]}%"
                rows = conn.execute(
                    """
                    SELECT 'chat' as src, m.content as content, m.created_at as created_at
                    FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id
                    WHERE c.user_id = ? AND m.content LIKE ?
                    ORDER BY m.created_at DESC
                    LIMIT ?
                    """,
                    (int(user_id), like, limit_n),
                ).fetchall()

            rows2: List[sqlite3.Row] = []
            try:
                rows2 = conn.execute(
                    """
                    SELECT 'soul' as src, e.content as content, e.created_at as created_at
                    FROM soul_events_fts f
                    JOIN user_soul_events e ON e.id = f.event_id
                    WHERE e.user_id = ? AND soul_events_fts MATCH ?
                    ORDER BY e.created_at DESC
                    LIMIT ?
                    """,
                    (int(user_id), q, limit_n),
                ).fetchall()
            except Exception:
                like = f"%{q[:80]}%"
                rows2 = conn.execute(
                    """
                    SELECT 'soul' as src, e.content as content, e.created_at as created_at
                    FROM user_soul_events e
                    WHERE e.user_id = ? AND e.content LIKE ?
                    ORDER BY e.created_at DESC
                    LIMIT ?
                    """,
                    (int(user_id), like, limit_n),
                ).fetchall()

            out = [dict(r) for r in rows] + [dict(r) for r in rows2]
            out.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
            return out[:limit_n]

    def upsert_user_llm_settings(
        self, user_id: int, llm_settings: Dict[str, Any]
    ) -> None:
        llm_json = json.dumps(llm_settings or {}, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_llm_settings (user_id, llm_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  llm_json=excluded.llm_json,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, llm_json),
            )
            conn.commit()

    def get_user_llm_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT llm_json, updated_at FROM user_llm_settings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            try:
                data = json.loads(row["llm_json"] or "{}")
            except Exception:
                data = {}
            return {
                "settings": data,
                "updated_at": row["updated_at"],
            }

    def upsert_user_security_settings(
        self, user_id: int, security_settings: Dict[str, Any]
    ) -> None:
        security_json = json.dumps(security_settings or {}, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_security_settings (user_id, security_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  security_json=excluded.security_json,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, security_json),
            )
            conn.commit()

    def get_user_security_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT security_json, updated_at FROM user_security_settings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            try:
                data = json.loads(row["security_json"] or "{}")
            except Exception:
                data = {}
            return {
                "settings": data,
                "updated_at": row["updated_at"],
            }

    def add_user_command_autoapprove(self, user_id: int, command_norm: str) -> bool:
        v = str(command_norm or "").strip().lower()
        if not v:
            return False
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO user_command_autoapprove (user_id, command_norm)
                VALUES (?, ?)
                """,
                (int(user_id), v),
            )
            conn.commit()
            return bool(cur.rowcount and int(cur.rowcount) > 0)

    def list_user_command_autoapprove(self, user_id: int, limit: int = 200) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT command_norm
                FROM user_command_autoapprove
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(user_id), int(limit)),
            ).fetchall()
            return [str(r[0] or "") for r in rows if r and r[0]]

    def delete_user_command_autoapprove(self, user_id: int, command_norm: str) -> bool:
        v = str(command_norm or "").strip().lower()
        if not v:
            return False
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "DELETE FROM user_command_autoapprove WHERE user_id = ? AND command_norm = ?",
                (int(user_id), v),
            )
            conn.commit()
            return bool(cur.rowcount and int(cur.rowcount) > 0)

    def add_conversation_cli_summary(
        self, user_id: int, conversation_id: int, execution_id: str, summary: str
    ) -> bool:
        eid = str(execution_id or "").strip()
        text = _redact_text(summary) or ""
        if not eid or not text:
            return False
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO conversation_cli_summaries
                (user_id, conversation_id, execution_id, summary)
                VALUES (?, ?, ?, ?)
                """,
                (int(user_id), int(conversation_id), eid, text),
            )
            conn.commit()
            return bool(cur.rowcount and int(cur.rowcount) > 0)

    def has_conversation_cli_summary(self, user_id: int, execution_id: str) -> bool:
        eid = str(execution_id or "").strip()
        if not eid:
            return False
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM conversation_cli_summaries
                WHERE user_id = ? AND execution_id = ?
                LIMIT 1
                """,
                (int(user_id), eid),
            ).fetchone()
            return bool(row)

    def upsert_user_soul(
        self, user_id: int, soul_data: Dict[str, Any], soul_markdown: str
    ) -> None:
        soul_json = json.dumps(soul_data or {}, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_soul (user_id, soul_json, soul_markdown, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                  soul_json=excluded.soul_json,
                  soul_markdown=excluded.soul_markdown,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, soul_json, soul_markdown or ""),
            )
            conn.commit()

    def get_user_soul(self, user_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT soul_json, soul_markdown, updated_at FROM user_soul WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            try:
                data = json.loads(row["soul_json"] or "{}")
            except Exception:
                data = {}
            return {
                "data": data,
                "markdown": row["soul_markdown"] or "",
                "updated_at": row["updated_at"],
            }

    def append_soul_event(self, user_id: int, source: str, content: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO user_soul_events (user_id, source, content) VALUES (?, ?, ?)",
                (user_id, source or "unknown", _redact_text(content) or ""),
            )
            event_id = cursor.lastrowid
            conn.commit()
            return event_id

    def list_soul_events(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, source, content, created_at
                FROM user_soul_events
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, int(limit)),
            ).fetchall()
            return [dict(r) for r in rows]

    def set_soul_event_salience(self, user_id: int, event_id: int, salience: float) -> bool:
        try:
            s = float(salience)
        except Exception:
            s = 0.5
        s = max(0.0, min(1.0, s))
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE user_soul_events SET salience=?, last_used_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                (s, int(event_id), int(user_id)),
            )
            conn.commit()
            return cur.rowcount > 0

    def list_imported_soul_events(self, user_id: int, limit: int = 25) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, source, content, created_at, salience, pinned
                FROM user_soul_events
                WHERE user_id = ? AND source LIKE 'imported%'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(user_id), int(limit)),
            ).fetchall()
            return [dict(r) for r in rows]

    def set_soul_event_pinned(self, user_id: int, event_id: int, pinned: bool) -> bool:
        v = 1 if bool(pinned) else 0
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE user_soul_events SET pinned=? WHERE id=? AND user_id=?",
                (v, int(event_id), int(user_id)),
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_imported_soul_event(self, user_id: int, event_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT source FROM user_soul_events WHERE id=? AND user_id=?",
                (int(event_id), int(user_id)),
            ).fetchone()
            if not row:
                return False
            src = str(row[0] or "")
            if not src.startswith("imported"):
                return False
            cur = conn.execute(
                "DELETE FROM user_soul_events WHERE id=? AND user_id=?",
                (int(event_id), int(user_id)),
            )
            conn.commit()
            return cur.rowcount > 0

    def create_friction_event(self, payload: Dict[str, Any], mode: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            payload_json = _redact_text(json.dumps(payload, ensure_ascii=False)) or "{}"
            user_message = payload.get("event", {}).get("user_message")
            if isinstance(user_message, str):
                user_message = _redact_text(user_message)
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
                    user_message,
                    str(payload.get("context", {}).get("os", "")),
                    str(payload.get("context", {}).get("runtime", "")),
                    payload.get("context", {}).get("skill_active"),
                    payload.get("context", {}).get("connector_active"),
                    payload_json,
                    mode,
                ),
            )
            event_id = cursor.lastrowid
            conn.commit()
        return int(event_id)

    def list_friction_events(
        self, sent: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
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
            row = conn.execute(
                "SELECT COUNT(*) FROM friction_events WHERE sent = 0"
            ).fetchone()
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
            cur = conn.execute(
                "DELETE FROM friction_events WHERE id = ?", (int(event_id),)
            )
            conn.commit()
            return cur.rowcount > 0

    def get_conversation_stats(self, conversation_id: int) -> Dict[str, Any]:
        """Obtém estatísticas da conversa"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Estatísticas gerais
            stats = conn.execute(
                """
                SELECT
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
                    SUM(tokens) as total_tokens,
                    MIN(created_at) as started_at,
                    MAX(created_at) as last_activity
                FROM messages
                WHERE conversation_id = ?
            """,
                (conversation_id,),
            ).fetchone()

            # Providers usados
            providers = conn.execute(
                """
                SELECT DISTINCT provider, COUNT(*) as usage_count
                FROM messages
                WHERE conversation_id = ? AND provider IS NOT NULL
                GROUP BY provider
            """,
                (conversation_id,),
            ).fetchall()

            # Experts usados
            experts = conn.execute(
                """
                SELECT DISTINCT expert_id, COUNT(*) as usage_count
                FROM messages
                WHERE conversation_id = ? AND expert_id IS NOT NULL
                GROUP BY expert_id
            """,
                (conversation_id,),
            ).fetchall()

            return {
                **dict(stats),
                "providers": [dict(p) for p in providers],
                "experts": [dict(e) for e in experts],
            }

    # ── Feedback ──────────────────────────────────────────────────────────────

    def upsert_message_feedback(
        self, user_id: int, message_id: int, rating: int
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO message_feedback (user_id, message_id, rating)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id, message_id) DO UPDATE SET rating=excluded.rating""",
                (user_id, message_id, rating),
            )
            conn.commit()
            # Reinforce memory salience when user gives positive feedback
            if rating == 1:
                msg = conn.execute(
                    "SELECT content FROM messages WHERE id=?", (message_id,)
                ).fetchone()
                if msg:
                    conn.execute(
                        """UPDATE user_soul_events
                           SET salience = MIN(1.0, salience + 0.1),
                               last_used_at = CURRENT_TIMESTAMP
                           WHERE user_id=? AND last_used_at IS NOT NULL""",
                        (user_id,),
                    )
            conn.commit()

    def get_message_feedback(self, user_id: int, message_id: int) -> Optional[int]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT rating FROM message_feedback WHERE user_id=? AND message_id=?",
                (user_id, message_id),
            ).fetchone()
            return row[0] if row else None

    # ── Plan tasks ────────────────────────────────────────────────────────────

    def create_plan_tasks(
        self, user_id: int, parent_conversation_id: int, tasks: list
    ) -> list:
        """tasks = [{"title": str, "skill_id": str|None}]"""
        ids = []
        with sqlite3.connect(self.db_path) as conn:
            for i, task in enumerate(tasks):
                cur = conn.execute(
                    """INSERT INTO plan_tasks
                       (user_id, parent_conversation_id, title, skill_id, position)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        parent_conversation_id,
                        task.get("title", ""),
                        task.get("skill_id"),
                        i,
                    ),
                )
                ids.append(cur.lastrowid)
            conn.commit()
        return ids

    def get_plan_tasks(self, parent_conversation_id: int) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM plan_tasks WHERE parent_conversation_id=?
                   ORDER BY position""",
                (parent_conversation_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_plan_task_status(
        self, task_id: int, status: str, conversation_id: Optional[int] = None
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            if conversation_id is not None:
                conn.execute(
                    "UPDATE plan_tasks SET status=?, conversation_id=? WHERE id=?",
                    (status, conversation_id, task_id),
                )
            else:
                conn.execute(
                    "UPDATE plan_tasks SET status=? WHERE id=?", (status, task_id)
                )
            conn.commit()

    # ── Projects ──────────────────────────────────────────────────────────────

    def create_project(self, user_id: int, name: str, context_md: str = "") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO projects (user_id, name, context_md) VALUES (?, ?, ?)",
                (user_id, name, context_md),
            )
            conn.commit()
            return cur.lastrowid

    def get_user_projects(self, user_id: int) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM projects WHERE user_id=? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_project(self, project_id: int, user_id: int) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM projects WHERE id=? AND user_id=?",
                (project_id, user_id),
            ).fetchone()
            return dict(row) if row else None

    def update_project_context(
        self, project_id: int, user_id: int, context_md: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE projects SET context_md=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=? AND user_id=?""",
                (context_md, project_id, user_id),
            )
            conn.commit()

    def update_project_name(self, project_id: int, user_id: int, name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE projects SET name=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=? AND user_id=?""",
                (name, project_id, user_id),
            )
            conn.commit()

    def delete_project(self, project_id: int, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM projects WHERE id=? AND user_id=?",
                (project_id, user_id),
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE conversations SET project_id=NULL WHERE project_id=?",
                (project_id,),
            )
            conn.execute(
                "DELETE FROM projects WHERE id=? AND user_id=?",
                (project_id, user_id),
            )
            conn.commit()
            return True

    def set_conversation_project(
        self, conversation_id: int, project_id: Optional[int]
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE conversations SET project_id=? WHERE id=?",
                (project_id, conversation_id),
            )
            conn.commit()

    # ── Memory Phase 2-4 ─────────────────────────────────────────────────────

    def decay_memory(self, user_id: int, days_threshold: int = 14) -> int:
        """Decay salience of memories not used recently. Returns count decayed."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """UPDATE user_soul_events
                   SET salience = MAX(0.05, salience - decay_rate)
                   WHERE user_id=? AND pinned=0
                     AND (last_used_at IS NULL
                          OR last_used_at < datetime('now', ? || ' days'))""",
                (user_id, f"-{days_threshold}"),
            )
            conn.commit()
            return cur.rowcount

    def reinforce_memory_usage(self, user_id: int, event_ids: list) -> None:
        """Boost salience of memories that were used in a RAG hit."""
        if not event_ids:
            return
        placeholders = ",".join("?" * len(event_ids))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""UPDATE user_soul_events
                    SET salience = MIN(1.0, salience + 0.08),
                        last_used_at = CURRENT_TIMESTAMP
                    WHERE user_id=? AND id IN ({placeholders})""",
                [user_id] + list(event_ids),
            )
            conn.commit()

    def prune_low_salience_memories(
        self, user_id: int, min_salience: float = 0.1, keep_pinned: bool = True
    ) -> int:
        """Delete memories below salience threshold. Returns count pruned."""
        with sqlite3.connect(self.db_path) as conn:
            query = """DELETE FROM user_soul_events
                       WHERE user_id=? AND salience < ?"""
            args: list = [user_id, min_salience]
            if keep_pinned:
                query += " AND pinned=0"
            cur = conn.execute(query, args)
            conn.commit()
            return cur.rowcount

    def get_consolidated_memory_snapshot(self, user_id: int) -> str:
        """Return top memories by salience as a consolidated snapshot string."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT content, salience, source FROM user_soul_events
                   WHERE user_id=?
                   ORDER BY pinned DESC, salience DESC
                   LIMIT 40""",
                (user_id,),
            ).fetchall()
            if not rows:
                return ""
            lines = []
            for r in rows:
                pin = " [pinned]" if r["source"] == "pinned" else ""
                lines.append(f"- {r['content']}{pin}")
            return "\n".join(lines)

    # ── Expert ratings ────────────────────────────────────────────────────────

    def record_expert_rating(
        self, user_id: int, expert_id: str, positive: bool
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO expert_ratings (user_id, expert_id, total_responses, positive, negative)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, expert_id) DO UPDATE SET
                    total_responses = total_responses + 1,
                    positive = positive + excluded.positive,
                    negative = negative + excluded.negative,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (user_id, expert_id, 1 if positive else 0, 0 if positive else 1),
            )
            conn.commit()

    def get_expert_rating_summary(self, user_id: int) -> dict:
        """Returns {expert_id: approval_rate} for all rated experts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT expert_id, positive, total_responses FROM expert_ratings WHERE user_id=?",
                (user_id,),
            ).fetchall()
            return {
                r["expert_id"]: (r["positive"] / r["total_responses"])
                if r["total_responses"] > 0
                else 0.5
                for r in rows
            }

    def get_message_with_preceding_user_message(
        self, message_id: int
    ) -> Optional[tuple]:
        """Returns (user_msg, assistant_msg) pair for the given assistant message_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            msg = conn.execute(
                "SELECT * FROM messages WHERE id=?", (message_id,)
            ).fetchone()
            if not msg or msg["role"] != "assistant":
                return None
            prev = conn.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id=? AND id < ? AND role='user'
                ORDER BY id DESC LIMIT 1
            """,
                (msg["conversation_id"], message_id),
            ).fetchone()
            if not prev:
                return None
            return (dict(prev), dict(msg))

    # ── Orchestration ─────────────────────────────────────────────────────────

    def create_orchestration_run(
        self, user_id: int, parent_conversation_id: int
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO orchestration_runs (user_id, parent_conversation_id) VALUES (?, ?)",
                (user_id, parent_conversation_id),
            )
            conn.commit()
            return cur.lastrowid

    def update_orchestration_run(self, run_id: int, status: str, log: list) -> None:
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE orchestration_runs
                SET status=?, log_json=?,
                    finished_at = CASE WHEN ? IN ('completed','failed')
                                       THEN CURRENT_TIMESTAMP ELSE NULL END
                WHERE id=?
            """,
                (status, json.dumps(log), status, run_id),
            )
            conn.commit()

    def get_orchestration_run(self, run_id: int) -> Optional[dict]:
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM orchestration_runs WHERE id=?", (run_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            try:
                d["log"] = json.loads(d.get("log_json") or "[]")
            except Exception:
                d["log"] = []
            return d


# Instância global
db_manager = DatabaseManager()


# Funções auxiliares
def create_conversation(
    user_id: int,
    session_id: str,
    title: str,
    kind: str = "conversation",
    source: str = "user",
) -> int:
    return db_manager.create_conversation(
        user_id, session_id, title, kind=kind, source=source
    )


def get_user_conversations(
    user_id: int, kind: Optional[str] = None, source: Optional[str] = None
) -> List[Dict[str, Any]]:
    return db_manager.get_user_conversations(user_id, kind=kind, source=source)


def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
    """Obtém mensagens de uma conversa"""
    return db_manager.get_conversation_messages(conversation_id)

def get_message(message_id: int) -> Optional[Dict[str, Any]]:
    return db_manager.get_message(message_id)


def save_message(
    conversation_id: int,
    role: str,
    content: str,
    expert_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    tokens: Optional[int] = None,
) -> int:
    """Salva mensagem"""
    return db_manager.save_message(
        conversation_id, role, content, expert_id, provider, model, tokens
    )


def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """Deleta conversa"""
    return db_manager.delete_conversation(conversation_id, user_id)


def update_conversation_title(conversation_id: int, user_id: int, title: str) -> bool:
    return db_manager.update_conversation_title(conversation_id, user_id, title)


def search_user_messages(
    user_id: int, query: str, limit: int = 50, kind: Optional[str] = None
) -> List[Dict[str, Any]]:
    return db_manager.search_user_messages(user_id, query, limit=limit, kind=kind)


def add_task_todo(
    user_id: int,
    conversation_id: int,
    text: str,
    kind: Optional[str] = None,
    actor: Optional[str] = None,
    origin: Optional[str] = None,
    scope: Optional[str] = None,
    priority: Optional[str] = None,
    due_at: Optional[str] = None,
    parent_todo_id: Optional[int] = None,
    delivery_path: Optional[str] = None,
    artifact_meta: Optional[Any] = None,
    source_conversation_id: Optional[int] = None,
    source_message_id: Optional[int] = None,
) -> int:
    return db_manager.add_task_todo(
        user_id,
        conversation_id,
        text,
        kind=kind,
        actor=actor,
        origin=origin,
        scope=scope,
        priority=priority,
        due_at=due_at,
        parent_todo_id=parent_todo_id,
        delivery_path=delivery_path,
        artifact_meta=artifact_meta,
        source_conversation_id=source_conversation_id,
        source_message_id=source_message_id,
    )


def list_task_todos(
    user_id: int, conversation_id: int, status: Optional[str] = None
) -> List[Dict[str, Any]]:
    return db_manager.list_task_todos(user_id, conversation_id, status=status)


def list_pending_todos(user_id: int) -> List[Dict[str, Any]]:
    return db_manager.list_pending_todos(user_id)


def update_task_todo(
    user_id: int,
    todo_id: int,
    text: Optional[str] = None,
    status: Optional[str] = None,
    kind: Optional[str] = None,
    actor: Optional[str] = None,
    origin: Optional[str] = None,
    scope: Optional[str] = None,
    priority: Optional[str] = None,
    due_at: Optional[str] = None,
    parent_todo_id: Optional[int] = None,
    delivery_path: Optional[str] = None,
    artifact_meta: Optional[Any] = None,
    source_conversation_id: Optional[int] = None,
    source_message_id: Optional[int] = None,
) -> bool:
    return db_manager.update_task_todo(
        user_id,
        todo_id,
        text=text,
        status=status,
        kind=kind,
        actor=actor,
        origin=origin,
        scope=scope,
        priority=priority,
        due_at=due_at,
        parent_todo_id=parent_todo_id,
        delivery_path=delivery_path,
        artifact_meta=artifact_meta,
        source_conversation_id=source_conversation_id,
        source_message_id=source_message_id,
    )


def get_task_todo(user_id: int, todo_id: int) -> Optional[Dict[str, Any]]:
    return db_manager.get_task_todo(user_id, todo_id)


def get_conversation_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtém conversa ativa por session_id"""
    return db_manager.get_conversation_by_session(session_id)


def get_conversation_by_session_for_user(
    user_id: int, session_id: str
) -> Optional[Dict[str, Any]]:
    return db_manager.get_conversation_by_session_for_user(user_id, session_id)


def get_user_skills(user_id: int) -> Optional[List[Dict[str, Any]]]:
    return db_manager.get_user_skills(user_id)


def upsert_user_skills(user_id: int, skills: List[Dict[str, Any]]) -> None:
    return db_manager.upsert_user_skills(user_id, skills)


def create_friction_event(payload: Dict[str, Any], mode: str) -> int:
    return db_manager.create_friction_event(payload, mode)


def list_friction_events(
    sent: Optional[int] = None, limit: int = 100
) -> List[Dict[str, Any]]:
    return db_manager.list_friction_events(sent=sent, limit=limit)


def count_pending_friction_events() -> int:
    return db_manager.count_pending_friction_events()


def mark_friction_event_sent(event_id: int, github_url: str) -> bool:
    return db_manager.mark_friction_event_sent(event_id, github_url)


def delete_friction_event(event_id: int) -> bool:
    return db_manager.delete_friction_event(event_id)


def upsert_user_llm_settings(user_id: int, llm_settings: Dict[str, Any]) -> None:
    return db_manager.upsert_user_llm_settings(user_id, llm_settings)


def get_user_llm_settings(user_id: int) -> Optional[Dict[str, Any]]:
    return db_manager.get_user_llm_settings(user_id)


def upsert_user_security_settings(
    user_id: int, security_settings: Dict[str, Any]
) -> None:
    return db_manager.upsert_user_security_settings(user_id, security_settings)


def get_user_security_settings(user_id: int) -> Optional[Dict[str, Any]]:
    return db_manager.get_user_security_settings(user_id)

def add_user_command_autoapprove(user_id: int, command_norm: str) -> bool:
    return db_manager.add_user_command_autoapprove(user_id, command_norm)


def list_user_command_autoapprove(user_id: int, limit: int = 200) -> List[str]:
    return db_manager.list_user_command_autoapprove(user_id, limit=limit)


def delete_user_command_autoapprove(user_id: int, command_norm: str) -> bool:
    return db_manager.delete_user_command_autoapprove(user_id, command_norm)

def add_conversation_cli_summary(
    user_id: int, conversation_id: int, execution_id: str, summary: str
) -> bool:
    return db_manager.add_conversation_cli_summary(user_id, conversation_id, execution_id, summary)


def has_conversation_cli_summary(user_id: int, execution_id: str) -> bool:
    return db_manager.has_conversation_cli_summary(user_id, execution_id)


def upsert_user_api_key_ciphertext(user_id: int, api_key_ciphertext: str) -> None:
    return db_manager.upsert_user_api_key_ciphertext(user_id, api_key_ciphertext)


def get_user_api_key_ciphertext(user_id: int) -> Optional[str]:
    return db_manager.get_user_api_key_ciphertext(user_id)

def set_soul_event_salience(user_id: int, event_id: int, salience: float) -> bool:
    return db_manager.set_soul_event_salience(user_id, event_id, salience)


def list_imported_soul_events(user_id: int, limit: int = 25) -> List[Dict[str, Any]]:
    return db_manager.list_imported_soul_events(user_id, limit=limit)


def set_soul_event_pinned(user_id: int, event_id: int, pinned: bool) -> bool:
    return db_manager.set_soul_event_pinned(user_id, event_id, pinned)


def delete_imported_soul_event(user_id: int, event_id: int) -> bool:
    return db_manager.delete_imported_soul_event(user_id, event_id)


def delete_user_api_key(user_id: int) -> bool:
    return db_manager.delete_user_api_key(user_id)


def add_user_llm_provider_key_ciphertext(
    user_id: int, provider: str, api_key_ciphertext: str, set_active: bool = True
) -> int:
    return db_manager.add_user_llm_provider_key_ciphertext(
        user_id, provider, api_key_ciphertext, set_active=set_active
    )


def list_user_llm_provider_keys(user_id: int, provider: Optional[str] = None) -> List[Dict[str, Any]]:
    return db_manager.list_user_llm_provider_keys(user_id, provider=provider)


def get_active_user_llm_provider_key_ciphertext(user_id: int, provider: str) -> Optional[str]:
    return db_manager.get_active_user_llm_provider_key_ciphertext(user_id, provider)


def set_active_user_llm_provider_key(user_id: int, provider: str, key_id: int) -> bool:
    return db_manager.set_active_user_llm_provider_key(user_id, provider, key_id)


def delete_user_llm_provider_key(user_id: int, provider: str, key_id: int) -> bool:
    return db_manager.delete_user_llm_provider_key(user_id, provider, key_id)


def get_user_onboarding_completed(user_id: int) -> Optional[bool]:
    return db_manager.get_user_onboarding_completed(user_id)


def set_user_onboarding_completed(user_id: int, completed: bool) -> None:
    return db_manager.set_user_onboarding_completed(user_id, completed)


def upsert_user_connector_secret_ciphertext(
    user_id: int, connector_key: str, secret_ciphertext: str
) -> None:
    return db_manager.upsert_user_connector_secret_ciphertext(
        user_id, connector_key, secret_ciphertext
    )


def get_user_connector_secret_ciphertext(
    user_id: int, connector_key: str
) -> Optional[str]:
    return db_manager.get_user_connector_secret_ciphertext(user_id, connector_key)


def delete_user_connector_secret(user_id: int, connector_key: str) -> bool:
    return db_manager.delete_user_connector_secret(user_id, connector_key)


def list_user_connector_keys(user_id: int) -> List[str]:
    return db_manager.list_user_connector_keys(user_id)


def create_telegram_link_code(user_id: int, ttl_seconds: int = 600) -> Dict[str, Any]:
    return db_manager.create_telegram_link_code(user_id, ttl_seconds=ttl_seconds)


def consume_telegram_link_code(code: str) -> Optional[int]:
    return db_manager.consume_telegram_link_code(code)


def upsert_telegram_link(user_id: int, telegram_user_id: str, chat_id: str) -> None:
    return db_manager.upsert_telegram_link(user_id, telegram_user_id, chat_id)


def revoke_telegram_link(telegram_user_id: str, chat_id: str) -> bool:
    return db_manager.revoke_telegram_link(telegram_user_id, chat_id)


def list_telegram_links(user_id: int) -> List[Dict[str, Any]]:
    return db_manager.list_telegram_links(user_id)


def get_telegram_linked_user_id(telegram_user_id: str, chat_id: str) -> Optional[int]:
    return db_manager.get_telegram_linked_user_id(telegram_user_id, chat_id)


def log_cli_command(
    *,
    user_id: int,
    conversation_id: int,
    app_name: str,
    action: str,
    command_executed: str,
    status: str,
    output: Optional[str] = None,
    visual_state_summary: Optional[str] = None,
) -> int:
    return db_manager.log_cli_command(
        user_id=user_id,
        conversation_id=conversation_id,
        app_name=app_name,
        action=action,
        command_executed=command_executed,
        status=status,
        output=output,
        visual_state_summary=visual_state_summary,
    )


def upsert_user_system_profile(
    user_id: int, profile_md: str, profile_data: Optional[Dict[str, Any]] = None
) -> None:
    return db_manager.upsert_user_system_profile(user_id, profile_md, profile_data)


def get_user_system_profile(user_id: int) -> Optional[Dict[str, Any]]:
    return db_manager.get_user_system_profile(user_id)


def update_user_system_profile_data(
    user_id: int, patch: Dict[str, Any]
) -> Dict[str, Any]:
    return db_manager.update_user_system_profile_data(user_id, patch)


def delete_user_system_profile(user_id: int) -> bool:
    return db_manager.delete_user_system_profile(user_id)


def upsert_system_kv_cache(cache_key: str, value: Dict[str, Any]) -> None:
    return db_manager.upsert_system_kv_cache(cache_key, value)


def get_system_kv_cache(cache_key: str, max_age_s: int = 21600) -> Optional[Dict[str, Any]]:
    return db_manager.get_system_kv_cache(cache_key, max_age_s=max_age_s)


def upsert_user_soul(
    user_id: int, soul_data: Dict[str, Any], soul_markdown: str
) -> None:
    return db_manager.upsert_user_soul(user_id, soul_data, soul_markdown)


def get_user_soul(user_id: int) -> Optional[Dict[str, Any]]:
    return db_manager.get_user_soul(user_id)


def append_soul_event(user_id: int, source: str, content: str) -> int:
    return db_manager.append_soul_event(user_id, source, content)


def list_soul_events(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    return db_manager.list_soul_events(user_id, limit=limit)


def get_cached_answer(
    user_id: int, question_hash: str, max_age_hours: int = 24
) -> Optional[Dict[str, Any]]:
    return db_manager.get_cached_answer(
        user_id, question_hash, max_age_hours=max_age_hours
    )


def put_cached_answer(
    user_id: int, question_hash: str, question: str, answer: str
) -> int:
    return db_manager.put_cached_answer(user_id, question_hash, question, answer)


def search_user_memory(
    user_id: int, query: str, limit: int = 6
) -> List[Dict[str, Any]]:
    return db_manager.search_user_memory(user_id, query, limit=limit)


# ── Module-level wrappers for new features ────────────────────────────────────


def upsert_message_feedback(user_id: int, message_id: int, rating: int) -> None:
    db_manager.upsert_message_feedback(user_id, message_id, rating)


def get_message_feedback(user_id: int, message_id: int) -> Optional[int]:
    return db_manager.get_message_feedback(user_id, message_id)


def create_plan_tasks(user_id: int, parent_conversation_id: int, tasks: list) -> list:
    return db_manager.create_plan_tasks(user_id, parent_conversation_id, tasks)


def get_plan_tasks(parent_conversation_id: int) -> list:
    return db_manager.get_plan_tasks(parent_conversation_id)


def update_plan_task_status(
    task_id: int, status: str, conversation_id: Optional[int] = None
) -> None:
    db_manager.update_plan_task_status(task_id, status, conversation_id)


def create_project(user_id: int, name: str, context_md: str = "") -> int:
    return db_manager.create_project(user_id, name, context_md)


def get_user_projects(user_id: int) -> list:
    return db_manager.get_user_projects(user_id)


def get_project(project_id: int, user_id: int) -> Optional[dict]:
    return db_manager.get_project(project_id, user_id)

def update_project_name(project_id: int, user_id: int, name: str) -> None:
    return db_manager.update_project_name(project_id, user_id, name)

def delete_project(project_id: int, user_id: int) -> bool:
    return db_manager.delete_project(project_id, user_id)


def update_project_context(project_id: int, user_id: int, context_md: str) -> None:
    db_manager.update_project_context(project_id, user_id, context_md)


def set_conversation_project(conversation_id: int, project_id: Optional[int]) -> None:
    db_manager.set_conversation_project(conversation_id, project_id)


def decay_memory(user_id: int, days_threshold: int = 14) -> int:
    return db_manager.decay_memory(user_id, days_threshold)


def reinforce_memory_usage(user_id: int, event_ids: list) -> None:
    db_manager.reinforce_memory_usage(user_id, event_ids)


def prune_low_salience_memories(user_id: int, min_salience: float = 0.1) -> int:
    return db_manager.prune_low_salience_memories(user_id, min_salience)


def record_expert_rating(user_id: int, expert_id: str, positive: bool) -> None:
    db_manager.record_expert_rating(user_id, expert_id, positive)


def get_expert_rating_summary(user_id: int) -> dict:
    return db_manager.get_expert_rating_summary(user_id)


def get_message_with_preceding_user_message(message_id: int) -> Optional[tuple]:
    return db_manager.get_message_with_preceding_user_message(message_id)


def create_orchestration_run(user_id: int, parent_conversation_id: int) -> int:
    return db_manager.create_orchestration_run(user_id, parent_conversation_id)


def update_orchestration_run(run_id: int, status: str, log: list) -> None:
    db_manager.update_orchestration_run(run_id, status, log)


def get_orchestration_run(run_id: int) -> Optional[dict]:
    return db_manager.get_orchestration_run(run_id)


def get_db_path() -> str:
    """Return the path to the active SQLite database file."""
    return str(db_manager.db_path)


def get_consolidated_memory_snapshot(user_id: int) -> str:
    return db_manager.get_consolidated_memory_snapshot(user_id)
