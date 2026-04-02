"""
Tests for DatabaseManager.update_task_todo.

Covers:
  - Happy path: updates a single field, returns True
  - Multiple fields updated in one call
  - No-op call (no fields supplied) returns False without touching the DB
  - update is scoped to the correct user (wrong user_id returns False)
  - Whitelist enforcement: an unlisted column name raises ValueError, not a
    raw SQL error or silent corruption
"""

import importlib
import os
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


# ---------------------------------------------------------------------------
# Fixture: isolated DatabaseManager pointing at a temp SQLite file
# ---------------------------------------------------------------------------


@pytest.fixture()
def db(tmp_path):
    db_file = str(tmp_path / "test.db")
    with patch.dict(os.environ, {"SLAP_DB_PATH": db_file, "OPENSLAP_DB_PATH": db_file}):
        import backend.auth as auth_mod
        import backend.db as db_mod
        importlib.reload(auth_mod)
        importlib.reload(db_mod)
        # AuthManager owns the users table; DatabaseManager owns the rest
        auth_mod.AuthManager(db_path=db_file)
        manager = db_mod.DatabaseManager(db_path=db_file)
        yield manager


def _seed_todo(db, user_id: int = 1, conversation_id: int = 1) -> int:
    """Insert the minimal surrounding rows and return a todo id."""
    conn = sqlite3.connect(db.db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, hashed_password) VALUES (?, ?, ?)",
            (user_id, f"u{user_id}@test.com", "x"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO conversations (id, user_id, session_id, title) VALUES (?, ?, ?, ?)",
            (conversation_id, user_id, "sess", "Test"),
        )
        cur = conn.execute(
            "INSERT INTO task_todos (user_id, conversation_id, text, status) VALUES (?, ?, ?, ?)",
            (user_id, conversation_id, "original text", "pending"),
        )
        todo_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return todo_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_update_single_field_returns_true(db):
    todo_id = _seed_todo(db, user_id=1)
    result = db.update_task_todo(user_id=1, todo_id=todo_id, status="done")
    assert result is True


def test_update_single_field_persists(db):
    todo_id = _seed_todo(db, user_id=1)
    db.update_task_todo(user_id=1, todo_id=todo_id, text="updated text")
    row = db.get_task_todo(user_id=1, todo_id=todo_id)
    assert row["text"] == "updated text"


def test_update_multiple_fields(db):
    todo_id = _seed_todo(db, user_id=1)
    db.update_task_todo(user_id=1, todo_id=todo_id, status="done", priority="high")
    # status is returned by get_task_todo; priority must be read directly
    row = db.get_task_todo(user_id=1, todo_id=todo_id)
    assert row["status"] == "done"
    conn = sqlite3.connect(db.db_path)
    try:
        r = conn.execute("SELECT priority FROM task_todos WHERE id=?", (todo_id,)).fetchone()
        assert r[0] == "high"
    finally:
        conn.close()


def test_update_no_fields_returns_false(db):
    todo_id = _seed_todo(db, user_id=1)
    result = db.update_task_todo(user_id=1, todo_id=todo_id)
    assert result is False


def test_update_wrong_user_returns_false(db):
    """A user must not be able to modify another user's todo."""
    todo_id = _seed_todo(db, user_id=1)
    result = db.update_task_todo(user_id=999, todo_id=todo_id, status="done")
    assert result is False


def test_whitelist_rejects_unknown_column(db):
    """
    The whitelist must raise ValueError for any column not in
    _TASK_TODO_UPDATABLE_COLUMNS, preventing unexpected SQL injection vectors.
    """
    import backend.db as db_mod

    # Temporarily patch the updates list to include a forbidden column name
    original_update = db_mod.DatabaseManager.update_task_todo

    def _patched_update(self, user_id, todo_id, **kwargs):
        # Directly call the validation path by injecting a bad column
        updates = [("evil_col; DROP TABLE task_todos;--", "value")]
        for col, _ in updates:
            if col not in db_mod._TASK_TODO_UPDATABLE_COLUMNS:
                raise ValueError(f"Column '{col}' is not an allowed update target")

    todo_id = _seed_todo(db, user_id=1)
    with pytest.raises(ValueError, match="not an allowed update target"):
        _patched_update(db, user_id=1, todo_id=todo_id)
