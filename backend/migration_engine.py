import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .backup_manager import create_backup, restore_backup


def _env_path(name: str, default: str) -> Path:
    raw = (os.getenv(name) or "").strip()
    return Path(raw) if raw else Path(default)


DB_PATH = _env_path("SLAP_DB_PATH", "data/auth.db")
MIGRATIONS_DIR = _env_path("SLAP_MIGRATIONS_DIR", str(Path(__file__).parent / "migrations"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          version     INTEGER NOT NULL UNIQUE,
          applied_at  TEXT    NOT NULL,
          description TEXT    NOT NULL,
          checksum    TEXT    NOT NULL
        )
        """
    )
    conn.commit()


def get_current_version(conn: sqlite3.Connection) -> int:
    _ensure_schema_version_table(conn)
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return int(row[0] or 0)


def _iter_migration_scripts() -> Iterable[Path]:
    if not MIGRATIONS_DIR.exists():
        MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _parse_version(script: Path) -> Optional[int]:
    try:
        return int(script.stem.split("_")[0])
    except Exception:
        return None


def list_pending_migrations(current_version: int) -> list[Path]:
    pending: list[Path] = []
    for script in _iter_migration_scripts():
        version = _parse_version(script)
        if version is None:
            continue
        if version > current_version:
            pending.append(script)
    return pending


def extract_description(script: Path) -> str:
    for line in script.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- Description:"):
            return line.replace("-- Description:", "").strip()
    return script.stem


def verify_applied_migrations(conn: sqlite3.Connection) -> None:
    _ensure_schema_version_table(conn)
    rows = conn.execute(
        "SELECT version, checksum FROM schema_version ORDER BY version ASC"
    ).fetchall()
    for version, expected_checksum in rows:
        scripts = sorted(MIGRATIONS_DIR.glob(f"{int(version):03d}_*.sql"))
        if not scripts:
            raise RuntimeError(
                f"CRÍTICO: Script da migration {int(version):03d} não encontrado em {MIGRATIONS_DIR}."
            )
        script = scripts[0]
        actual_checksum = sha256_file(script)
        if actual_checksum != expected_checksum:
            raise RuntimeError(
                f"CRÍTICO: Checksum diverge para migration {int(version):03d}. "
                f"Esperado={expected_checksum} Atual={actual_checksum}. ABORT."
            )


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return bool(row)


def _bootstrap_baseline_if_legacy(conn: sqlite3.Connection) -> None:
    current = get_current_version(conn)
    if current != 0:
        return

    legacy = _table_exists(conn, "users") or _table_exists(conn, "conversations") or _table_exists(conn, "messages")
    if not legacy:
        return

    baseline_scripts = sorted(MIGRATIONS_DIR.glob("001_*.sql"))
    if not baseline_scripts:
        raise RuntimeError(
            f"CRÍTICO: Banco legado detectado, mas migration 001 não existe em {MIGRATIONS_DIR}."
        )
    baseline = baseline_scripts[0]
    checksum = sha256_file(baseline)
    description = extract_description(baseline)

    with conn:
        conn.execute(
            "INSERT INTO schema_version (version, applied_at, description, checksum) VALUES (?, ?, ?, ?)",
            (1, datetime.now(timezone.utc).isoformat(), description, checksum),
        )


def run_migrations() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_schema_version_table(conn)
        _bootstrap_baseline_if_legacy(conn)
        verify_applied_migrations(conn)

        current = get_current_version(conn)
        pending = list_pending_migrations(current)
        if not pending:
            return

        for script in pending:
            version = _parse_version(script)
            if version is None:
                continue
            checksum = sha256_file(script)
            description = extract_description(script)

            backup_path = create_backup(label=f"pre_migration_{int(version):03d}")

            try:
                sql = script.read_text(encoding="utf-8")
                up_sql = sql.split("-- DOWN")[0]
                with conn:
                    conn.executescript(up_sql)
                    conn.execute(
                        "INSERT INTO schema_version (version, applied_at, description, checksum) VALUES (?, ?, ?, ?)",
                        (int(version), datetime.now(timezone.utc).isoformat(), description, checksum),
                    )
            except Exception as e:
                conn.close()
                restore_backup(backup_path, clean=True)
                raise RuntimeError(
                    f"CRÍTICO: Migration {int(version):03d} falhou ({e}). Backup restaurado de {backup_path}."
                )

        smoke_test(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def smoke_test(conn: sqlite3.Connection) -> None:
    checks = [
        ("schema_version", "SELECT COUNT(*) FROM schema_version"),
        ("users", "SELECT COUNT(*) FROM users"),
        ("conversations", "SELECT COUNT(*) FROM conversations"),
        ("messages", "SELECT COUNT(*) FROM messages"),
        ("friction_events", "SELECT COUNT(*) FROM friction_events"),
    ]
    for name, query in checks:
        try:
            conn.execute(query)
        except Exception as e:
            raise RuntimeError(f"CRÍTICO: Smoke test falhou em {name} ({e}).")
