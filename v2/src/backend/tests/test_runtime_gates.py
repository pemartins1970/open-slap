import importlib
import io
import sqlite3
import tarfile
from pathlib import Path


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_modules(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SLAP_DB_PATH", "data/auth.db")
    monkeypatch.setenv("SLAP_BACKUP_DIR", "data/backups")
    monkeypatch.setenv("SLAP_MIGRATIONS_DIR", "migrations")
    monkeypatch.setenv("SLAP_BACKUP_MAX_RETAIN", "50")

    import backend.backup_manager as backup_manager
    import backend.migration_engine as migration_engine
    import backend.update_checker as update_checker

    backup_manager = importlib.reload(backup_manager)
    migration_engine = importlib.reload(migration_engine)
    update_checker = importlib.reload(update_checker)

    return backup_manager, migration_engine, update_checker


def test_migration_adulterada_abort(monkeypatch, tmp_path: Path):
    _, migration_engine, _ = _load_modules(monkeypatch, tmp_path)

    _write_text(
        tmp_path / "migrations" / "001_initial_schema.sql",
        """
-- Migration: 001
-- Description: init
-- UP
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

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
);

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
);
-- DOWN
""".lstrip(),
    )

    migration_engine.run_migrations()

    _write_text(
        tmp_path / "migrations" / "001_initial_schema.sql",
        """
-- Migration: 001
-- Description: init (changed)
-- UP
CREATE TABLE IF NOT EXISTS t1 (id INTEGER PRIMARY KEY);
-- DOWN
""".lstrip(),
    )

    try:
        migration_engine.run_migrations()
        assert False, "Era esperado abortar por checksum divergente"
    except RuntimeError as e:
        assert "Checksum diverge" in str(e)


def test_migration_rollback_restore_clean(monkeypatch, tmp_path: Path):
    _, migration_engine, _ = _load_modules(monkeypatch, tmp_path)

    _write_text(
        tmp_path / "migrations" / "001_ok.sql",
        """
-- Migration: 001
-- Description: ok
-- UP
CREATE TABLE IF NOT EXISTS ok_table (id INTEGER PRIMARY KEY);
-- DOWN
""".lstrip(),
    )

    _write_text(
        tmp_path / "migrations" / "002_fail.sql",
        """
-- Migration: 002
-- Description: fail
-- UP
THIS IS NOT SQL;
-- DOWN
""".lstrip(),
    )

    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    _write_text(tmp_path / "state" / "before.json", '{"v": 1}')

    created_marker = {"created": False}
    original_create_backup = migration_engine.create_backup

    def _create_backup_and_poison(label: str):
        backup_path = original_create_backup(label)
        if label.endswith("pre_migration_002"):
            _write_text(tmp_path / "state" / "new_after_backup.json", '{"new": true}')
            created_marker["created"] = True
        return backup_path

    migration_engine.create_backup = _create_backup_and_poison

    try:
        migration_engine.run_migrations()
        assert False, "Era esperado abortar por migration inválida"
    except RuntimeError as e:
        assert "Migration 002 falhou" in str(e)

    assert created_marker["created"] is True
    assert not (tmp_path / "state" / "new_after_backup.json").exists()

    db_path = tmp_path / "data" / "auth.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("SELECT 1 FROM ok_table LIMIT 1")
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        assert int(row[0] or 0) == 1
    finally:
        conn.close()


def test_safe_extract_tar_blocks_traversal(monkeypatch, tmp_path: Path):
    _, _, update_checker = _load_modules(monkeypatch, tmp_path)

    tar_path = tmp_path / "evil.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        info = tarfile.TarInfo(name="../../../evil.txt")
        content = b"evil"
        info.size = len(content)
        tar.addfile(info, fileobj=io.BytesIO(content))

    dest = tmp_path / "install"
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        try:
            update_checker.safe_extract_tar(tar, dest)
            assert False, "Era esperado abortar por path traversal"
        except RuntimeError as e:
            assert "Path traversal" in str(e) or "caminho absoluto" in str(e).lower()

    assert not any(dest.rglob("*"))


def test_verify_manifest_signature_invalid_key(monkeypatch, tmp_path: Path):
    _, _, update_checker = _load_modules(monkeypatch, tmp_path)
    monkeypatch.setenv("SLAP_UPDATE_PUBLIC_KEY", "not-base64")
    try:
        update_checker.verify_manifest_signature(b"{}", b"\x00" * 64)
        assert False, "Era esperado abortar por chave inválida"
    except RuntimeError as e:
        assert "SLAP_UPDATE_PUBLIC_KEY" in str(e)


def test_restore_backup_clean_removes_new_files(monkeypatch, tmp_path: Path):
    backup_manager, _, _ = _load_modules(monkeypatch, tmp_path)

    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "auth.db").write_bytes(b"db")
    _write_text(tmp_path / "state" / "user.json", '{"u": 1}')

    backup_path = backup_manager.create_backup("manual")

    _write_text(tmp_path / "state" / "extra.json", '{"x": 1}')
    assert (tmp_path / "state" / "extra.json").exists()

    backup_manager.restore_backup(backup_path, clean=True)
    assert not (tmp_path / "state" / "extra.json").exists()
