import hashlib
import json
import os
import stat
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _env_path(name: str, default: str) -> Path:
    raw = (os.getenv(name) or "").strip()
    return Path(raw) if raw else Path(default)


DB_PATH = _env_path("SLAP_DB_PATH", "data/auth.db")
BACKUP_DIR = _env_path("SLAP_BACKUP_DIR", "data/backups")

STATE_DIR = Path("state")
BRAIN_DIR = Path("brain")
CONTEXTS_DIR = Path("storage/contexts")
PROJECTS_DIR = Path("projects")

MAX_BACKUPS = int((os.getenv("SLAP_BACKUP_MAX_RETAIN") or "").strip() or "10")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _project_root() -> Path:
    return Path.cwd().resolve()


def _is_safe_relative_path(rel: Path) -> bool:
    if rel.is_absolute():
        return False
    if getattr(rel, "drive", ""):
        return False
    if ".." in rel.parts:
        return False
    return True


def _relativize(path: Path, base: Path) -> Path:
    resolved = path.resolve()
    try:
        return resolved.relative_to(base)
    except Exception:
        raise RuntimeError(f"CRÍTICO: Caminho fora do diretório do projeto: {path}")


def _copy_file_to_backup(
    src: Path, backup_path: Path, base: Path, manifest_files: list[dict[str, Any]]
) -> None:
    rel = _relativize(src, base)
    if not _is_safe_relative_path(rel):
        raise RuntimeError(f"CRÍTICO: Caminho inválido para backup: {src}")
    dest = backup_path / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    manifest_files.append({"path": rel.as_posix(), "sha256": sha256_path(src)})


def _rmtree_force(path: Path) -> None:
    def _onerror(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            raise

    shutil.rmtree(path, onerror=_onerror)


def sha256_path(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return _sha256_bytes(path.read_bytes())


def _write_env_keys_only(dest_path: Path) -> bool:
    src = Path(".env")
    if not src.exists() or not src.is_file():
        return False
    out_lines: list[str] = []
    for line in src.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if not key:
            continue
        out_lines.append(f"{key}=")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(
        "\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8"
    )
    return True


def _iter_files_under(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            files.append(p)
    return files


def _prune_old_backups() -> None:
    if not BACKUP_DIR.exists() or MAX_BACKUPS <= 0:
        return
    dirs = [d for d in BACKUP_DIR.iterdir() if d.is_dir()]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    for old in dirs[MAX_BACKUPS:]:
        shutil.rmtree(old, ignore_errors=True)


def _get_schema_version() -> int:
    try:
        import sqlite3

        if not DB_PATH.exists():
            return 0
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
            return int(row[0] or 0)
        finally:
            conn.close()
    except Exception:
        return 0


def create_backup(label: str) -> Path:
    base = _project_root()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    backup_path = BACKUP_DIR / f"{timestamp}_{label}"
    backup_path.mkdir(parents=True, exist_ok=True)

    sources = [DB_PATH, STATE_DIR, BRAIN_DIR, CONTEXTS_DIR, PROJECTS_DIR]

    manifest_files: list[dict[str, Any]] = []
    for root in sources:
        root_resolved = root.resolve() if root.exists() else root
        if root_resolved.exists() and root_resolved.is_dir():
            for f in _iter_files_under(root_resolved):
                _copy_file_to_backup(f, backup_path, base, manifest_files)
        elif root_resolved.exists() and root_resolved.is_file():
            _copy_file_to_backup(root_resolved, backup_path, base, manifest_files)

    env_dest = backup_path / ".env"
    if _write_env_keys_only(env_dest):
        manifest_files.append({"path": ".env", "sha256": sha256_path(env_dest)})

    manifest = {
        "label": label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "product": "open-slap",
        "product_version": os.getenv("SLAP_VERSION", "unknown"),
        "schema_version": _get_schema_version(),
        "trigger": label,
        "files": manifest_files,
        "restorable": True,
    }

    (backup_path / "backup_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _prune_old_backups()
    return backup_path


def restore_backup(backup_path: Path, clean: bool = False) -> None:
    base = _project_root()
    backup_path = Path(backup_path)
    manifest_path = backup_path / "backup_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest não encontrado em {backup_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if clean:
        targets_to_clean = [DB_PATH, STATE_DIR, BRAIN_DIR, CONTEXTS_DIR, PROJECTS_DIR]
        for t in targets_to_clean:
            target = t if t.is_absolute() else (base / t).resolve()
            if target.exists():
                _relativize(target, base)
            if target.exists() and target.is_file():
                target.unlink()
            elif target.exists() and target.is_dir():
                _rmtree_force(target)

    for entry in manifest.get("files", []):
        rel_raw = str(entry.get("path", "")).replace("\\", "/")
        if not rel_raw:
            continue
        rel_path = Path(rel_raw)
        if not _is_safe_relative_path(rel_path):
            raise RuntimeError(
                "CRÍTICO: Manifest contém caminho inválido; restore abortado."
            )

        src = backup_path / rel_path
        dst = (base / rel_path).resolve()
        _relativize(dst, base)
        if not src.exists() or not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def list_backups() -> list[dict[str, Any]]:
    if not BACKUP_DIR.exists():
        return []
    result: list[dict[str, Any]] = []
    for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
        manifest = d / "backup_manifest.json"
        if manifest.exists():
            result.append(json.loads(manifest.read_text(encoding="utf-8")))
    return result
