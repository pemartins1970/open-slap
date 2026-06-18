"""
📜 Chronicle — Session memory system (mid-term, cross-session)
Write-only from chat pipeline perspective; queried via /search and /standup.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.db import db_manager
from backend.utils.text_processing import strip_internal_markup

logger = logging.getLogger(__name__)

USER_TRUNCATE = 1000
ASSISTANT_TRUNCATE = 5000

_closed_stale = False


def _ensure_tables() -> None:
    """Create chronicle tables + FTS5 if they don't exist."""
    global _closed_stale
    if not _closed_stale:
        _closed_stale = True
        _close_stale_sessions()
    with db_manager._connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chronicle_entries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role            TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content         TEXT NOT NULL,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chronicle_sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL UNIQUE,
                started_at      TEXT NOT NULL,
                ended_at        TEXT,
                summary         TEXT,
                messages_count  INTEGER NOT NULL DEFAULT 0,
                files_count     INTEGER NOT NULL DEFAULT 0,
                standup_at      TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chronicle_files (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                file_path       TEXT NOT NULL,
                action          TEXT NOT NULL CHECK(action IN ('read', 'write', 'create', 'delete')),
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chronicle_entries_conv
                ON chronicle_entries(conversation_id, created_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chronicle_files_conv
                ON chronicle_files(conversation_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chronicle_sessions_standup
                ON chronicle_sessions(standup_at)
        """)

        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chronicle_entries_fts
                USING fts5(content, content='chronicle_entries', content_rowid='id')
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chronicle_entries_ai
                AFTER INSERT ON chronicle_entries
                BEGIN
                    INSERT INTO chronicle_entries_fts(rowid, content)
                    VALUES (new.id, new.content);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chronicle_entries_ad
                AFTER DELETE ON chronicle_entries
                BEGIN
                    INSERT INTO chronicle_entries_fts(chronicle_entries_fts, rowid, content)
                    VALUES ('delete', old.id, old.content);
                END
            """)
        except Exception as e:
            logger.error("Chronicle FTS5 table creation failed: %s", e)

        conn.commit()


def _prepare_content(role: str, content: str) -> str:
    """Strip internal markup and truncate by role limit."""
    clean = strip_internal_markup(content)
    limit = USER_TRUNCATE if role == "user" else ASSISTANT_TRUNCATE
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + " \u2026"


def _ensure_session_row(conversation_id: int) -> None:
    """Create a chronicle_sessions row if none exists for this conversation."""
    with db_manager._connect() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO chronicle_sessions (conversation_id, started_at)
               VALUES (?, datetime('now'))""",
            (conversation_id,),
        )
        conn.commit()


def append_chronicle_entry(conversation_id: int, role: str, content: str) -> None:
    """Append a truncated entry to chronicle."""
    _ensure_tables()
    _ensure_session_row(conversation_id)
    prepared = _prepare_content(role, content)
    with db_manager._connect() as conn:
        conn.execute(
            "INSERT INTO chronicle_entries (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, prepared),
        )
        conn.execute(
            "UPDATE chronicle_sessions SET messages_count = messages_count + 1 WHERE conversation_id = ?",
            (conversation_id,),
        )
        conn.commit()


def append_chronicle_file(conversation_id: int, file_path: str, action: str) -> None:
    """Register a file touched by a tool call."""
    _ensure_tables()
    with db_manager._connect() as conn:
        conn.execute(
            "INSERT INTO chronicle_files (conversation_id, file_path, action) VALUES (?, ?, ?)",
            (conversation_id, file_path, action),
        )
        conn.execute(
            "UPDATE chronicle_sessions SET files_count = files_count + 1 WHERE conversation_id = ?",
            (conversation_id,),
        )
        conn.commit()


def _build_summary(conversation_id: int) -> str:
    """Heuristic summary — no LLM."""
    with db_manager._connect() as conn:
        conn.row_factory = sqlite3.Row
        entries = conn.execute(
            "SELECT role, content FROM chronicle_entries WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        files = conn.execute(
            "SELECT DISTINCT file_path, action FROM chronicle_files WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchall()

    first_user = next((e["content"] for e in entries if e["role"] == "user"), "")
    last_assistant = next(
        (e["content"] for e in reversed(entries) if e["role"] == "assistant"), ""
    )
    exchanges = len(entries)
    file_list = [f"{f['action']}: {f['file_path']}" for f in files] if files else []

    parts = [f"Início: {first_user[:200]}"]
    if exchanges:
        parts.append(f"{exchanges} mensagens")
    if file_list:
        parts.append("Arquivos: " + ", ".join(file_list[:10]))
    if last_assistant:
        parts.append(f"Última resposta: {last_assistant[:100]}")

    return " \u00b7 ".join(parts)


def close_chronicle_session(conversation_id: int) -> None:
    """Mark a session as ended and generate a heuristic summary."""
    _ensure_tables()
    summary = _build_summary(conversation_id)
    with db_manager._connect() as conn:
        conn.execute(
            """UPDATE chronicle_sessions SET
                ended_at = datetime('now'),
                summary = ?
            WHERE conversation_id = ?""",
            (summary, conversation_id),
        )
        conn.commit()


def close_any_open_session(exclude_conversation_id: Optional[int] = None) -> None:
    """Close any chronicle session that has ended_at IS NULL.

    Safe to call on every new conversation creation — no-op if nothing open.
    """
    _ensure_tables()
    with db_manager._connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT conversation_id FROM chronicle_sessions WHERE ended_at IS NULL",
        ).fetchall()
    for row in rows:
        cid = row["conversation_id"]
        if exclude_conversation_id is not None and cid == exclude_conversation_id:
            continue
        close_chronicle_session(cid)


def _close_stale_sessions() -> None:
    """Close sessions inactive for > 24h — crash recovery on startup.

    Uses last chronicle_entry activity, not started_at, so long-running
    conversations with recent activity are preserved.
    """
    _ensure_tables()
    with db_manager._connect() as conn:
        conn.row_factory = sqlite3.Row
        stale = conn.execute(
            """SELECT cs.conversation_id
               FROM chronicle_sessions cs
               LEFT JOIN (
                   SELECT conversation_id, MAX(created_at) as last_entry
                   FROM chronicle_entries
                   GROUP BY conversation_id
               ) ce ON cs.conversation_id = ce.conversation_id
               WHERE cs.ended_at IS NULL
                 AND COALESCE(ce.last_entry, cs.started_at) < datetime('now', '-24 hours')"""
        ).fetchall()
    for row in stale:
        try:
            close_chronicle_session(row["conversation_id"])
            logger.info("Chronicle closed stale session %s", row["conversation_id"])
        except Exception as e:
            logger.error("Chronicle failed to close stale session %s: %s", row["conversation_id"], e)


def chronicle_health() -> Dict[str, Any]:
    """Health metrics for the chronicle subsystem."""
    _ensure_tables()
    with db_manager._connect() as conn:
        conn.row_factory = sqlite3.Row
        last_write = conn.execute(
            "SELECT MAX(created_at) as last FROM chronicle_entries"
        ).fetchone()["last"]
        open_sessions = conn.execute(
            "SELECT COUNT(*) as c FROM chronicle_sessions WHERE ended_at IS NULL"
        ).fetchone()["c"]
        total_entries = conn.execute(
            "SELECT COUNT(*) as c FROM chronicle_entries"
        ).fetchone()["c"]
    return {
        "healthy": True,
        "last_write_at": last_write,
        "open_sessions": open_sessions,
        "total_entries": total_entries,
    }


def chronicle_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Full-text search across chronicle entries."""
    _ensure_tables()
    with db_manager._connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT ce.conversation_id, ce.role, ce.content, ce.created_at
               FROM chronicle_entries_fts fts
               JOIN chronicle_entries ce ON ce.id = fts.rowid
               WHERE chronicle_entries_fts MATCH ?
               ORDER BY rank LIMIT ?""",
            (query, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def chronicle_standup(since: Optional[str] = None) -> str:
    """Return a text report of sessions since `since` (ISO datetime or None = 7 days ago)."""
    _ensure_tables()
    if since is None:
        since = (datetime.utcnow() - timedelta(days=7)).isoformat()

    with db_manager._connect() as conn:
        conn.row_factory = sqlite3.Row
        sessions = conn.execute(
            """SELECT cs.*, ce.content as first_message
               FROM chronicle_sessions cs
               LEFT JOIN chronicle_entries ce ON ce.id = (
                   SELECT MIN(id) FROM chronicle_entries
                   WHERE conversation_id = cs.conversation_id AND role = 'user'
               )
               WHERE cs.started_at >= ?
               ORDER BY cs.started_at DESC""",
            (since,),
        ).fetchall()

    if not sessions:
        return "Nenhuma sess\u00e3o nova desde o \u00faltimo standup."

    lines = [f"\uD83D\uDCCB Standup \u2014 {len(sessions)} sess\u00f5es (desde {since[:10]}):\n"]
    for s in sessions:
        date = (s.get("started_at") or "")[:10]
        preview = (s.get("first_message") or "")[:80].replace("\n", " ")
        exchanges = s.get("messages_count") or 0
        fc = s.get("files_count") or 0
        lines.append(f"\u2022 [{date}] {preview} \u2014 {exchanges} trocas, {fc} arquivos")
        if s.get("summary"):
            lines.append(f"  {s['summary'][:120]}")

    lines.append("\nUse /search <termo> para buscar no hist\u00f3rico.")
    return "\n".join(lines)
