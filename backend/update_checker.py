import base64
import json
import os
import platform
import tarfile
import urllib.request
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .backup_manager import create_backup, restore_backup
from .migration_engine import run_migrations


GITHUB_API = "https://api.github.com"
REPO = (os.getenv("SLAP_UPDATE_GITHUB_REPO") or "").strip() or "owner/open-slap"
ENABLED = ((os.getenv("SLAP_UPDATE_CHECK_ENABLED") or "true").strip().lower() == "true")
INTERVAL_H = int((os.getenv("SLAP_UPDATE_CHECK_INTERVAL_HOURS") or "").strip() or "24")
VERSION = (os.getenv("SLAP_VERSION") or "").strip() or "0.0.0"
STATE_FILE = Path("state/update_check.json")
DOWNLOAD_DIR = Path("data/downloads")


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_check": None, "ignored_version": None}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _version_tuple(v: str) -> tuple[int, ...]:
    parts = [p for p in v.lstrip("v").split(".") if p != ""]
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out)


def _detect_asset_suffix() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "x64" if machine in ("x86_64", "amd64") else "arm64"
    if system == "linux":
        return f"linux-{arch}.tar.gz"
    if system == "darwin":
        return f"mac-{arch}.tar.gz"
    if system == "windows":
        return f"win-{arch}.zip"
    raise RuntimeError(f"Sistema não suportado: {system}/{machine}")


def check_for_updates() -> dict | None:
    if not ENABLED:
        return None

    state = _load_state()
    last_check = state.get("last_check")
    if last_check:
        try:
            last_dt = datetime.fromisoformat(last_check)
        except ValueError:
            last_dt = None
        if last_dt and datetime.now(timezone.utc) - last_dt < timedelta(hours=INTERVAL_H):
            return None

    try:
        url = f"{GITHUB_API}/repos/{REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": f"open-slap/{VERSION}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            release = json.loads(resp.read())
    except Exception:
        return None

    state["last_check"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)

    remote_version = (release.get("tag_name") or "").lstrip("v")
    ignored = state.get("ignored_version")
    if _version_tuple(remote_version) <= _version_tuple(VERSION):
        return None
    if ignored and _version_tuple(remote_version) <= _version_tuple(ignored):
        return None

    return {
        "version": remote_version,
        "name": release.get("name"),
        "changelog": release.get("body", ""),
        "published_at": release.get("published_at"),
        "assets": release.get("assets", []),
    }


def ignore_version(version: str) -> None:
    state = _load_state()
    state["ignored_version"] = version
    _save_state(state)


def verify_sha256(file_path: Path, expected: str) -> bool:
    import hashlib

    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    return actual.lower() == expected.lower().split()[0]


def _decode_sig_bytes(value: str) -> bytes:
    v = value.strip()
    if v == "":
        return b""
    try:
        return base64.b64decode(v, validate=True)
    except Exception:
        pass
    try:
        return bytes.fromhex(v)
    except Exception:
        return b""


def verify_manifest_signature(manifest_bytes: bytes, signature_bytes: bytes) -> None:
    key_b64 = (os.getenv("SLAP_UPDATE_PUBLIC_KEY") or "").strip()
    if not key_b64:
        raise RuntimeError("CRÍTICO: SLAP_UPDATE_PUBLIC_KEY não configurada; update abortado.")
    try:
        public_key_bytes = base64.b64decode(key_b64, validate=True)
    except Exception as e:
        raise RuntimeError(f"CRÍTICO: SLAP_UPDATE_PUBLIC_KEY inválida ({e}); update abortado.")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception as e:
        raise RuntimeError(f"CRÍTICO: Dependência de verificação de assinatura ausente ({e}); update abortado.")

    try:
        key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        key.verify(signature_bytes, manifest_bytes)
    except Exception:
        raise RuntimeError("CRÍTICO: Assinatura do manifest inválida; update abortado.")


def _is_within_directory(base_dir: Path, target: Path) -> bool:
    base = base_dir.resolve()
    try:
        target_resolved = target.resolve()
    except FileNotFoundError:
        target_resolved = target.parent.resolve() / target.name
    return str(target_resolved).startswith(str(base) + os.sep) or target_resolved == base


def safe_extract_tar(tar: tarfile.TarFile, dest_dir: Path) -> None:
    import stat

    dest_dir.mkdir(parents=True, exist_ok=True)
    for member in tar.getmembers():
        name = member.name
        if name.startswith("/") or name.startswith("\\"):
            raise RuntimeError("CRÍTICO: Asset contém caminho absoluto; instalação abortada.")
        if ":" in name.split("/")[0]:
            raise RuntimeError("CRÍTICO: Asset contém caminho absoluto; instalação abortada.")
        if member.islnk() or member.issym():
            raise RuntimeError("CRÍTICO: Asset contém link; instalação abortada.")
        if stat.S_ISLNK(member.mode):
            raise RuntimeError("CRÍTICO: Asset contém link; instalação abortada.")

        target_path = dest_dir / name
        if not _is_within_directory(dest_dir, target_path):
            raise RuntimeError("CRÍTICO: Path traversal detectado no asset; instalação abortada.")

    tar.extractall(dest_dir)


def safe_extract_zip(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    import stat

    dest_dir.mkdir(parents=True, exist_ok=True)
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or name.startswith("\\"):
            raise RuntimeError("CRÍTICO: Asset contém caminho absoluto; instalação abortada.")
        if ":" in name.split("/")[0]:
            raise RuntimeError("CRÍTICO: Asset contém caminho absoluto; instalação abortada.")
        norm = Path(name)
        if any(part == ".." for part in norm.parts):
            raise RuntimeError("CRÍTICO: Path traversal detectado no asset; instalação abortada.")
        mode = info.external_attr >> 16
        is_symlink = stat.S_IFMT(mode) == stat.S_IFLNK
        if is_symlink:
            raise RuntimeError("CRÍTICO: Asset contém link; instalação abortada.")
        target_path = dest_dir / norm
        if not _is_within_directory(dest_dir, target_path):
            raise RuntimeError("CRÍTICO: Path traversal detectado no asset; instalação abortada.")

    zf.extractall(dest_dir)


def apply_update(release_info: dict) -> None:
    version = release_info["version"]
    suffix = _detect_asset_suffix()
    product = "open-slap"

    asset_name = f"{product}-v{version}-{suffix}"
    hash_name = f"{asset_name}.sha256"
    manifest_name = "release.manifest.json"
    manifest_sig_name = "release.manifest.json.sig"

    assets = release_info.get("assets", [])
    asset = next((a for a in assets if a.get("name") == asset_name), None)
    asset_hash = next((a for a in assets if a.get("name") == hash_name), None)
    manifest = next((a for a in assets if a.get("name") == manifest_name), None)
    manifest_sig = next((a for a in assets if a.get("name") == manifest_sig_name), None)

    if not asset or not asset_hash:
        raise RuntimeError(f"CRÍTICO: Asset '{asset_name}' ou hash '{hash_name}' não encontrado no release.")
    if not manifest or not manifest_sig:
        raise RuntimeError("CRÍTICO: Manifest assinado não encontrado no release; update abortado.")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    asset_path = DOWNLOAD_DIR / asset_name
    hash_path = DOWNLOAD_DIR / hash_name
    manifest_path = DOWNLOAD_DIR / manifest_name
    manifest_sig_path = DOWNLOAD_DIR / manifest_sig_name

    urllib.request.urlretrieve(asset["browser_download_url"], asset_path)
    urllib.request.urlretrieve(asset_hash["browser_download_url"], hash_path)
    urllib.request.urlretrieve(manifest["browser_download_url"], manifest_path)
    urllib.request.urlretrieve(manifest_sig["browser_download_url"], manifest_sig_path)

    manifest_bytes = manifest_path.read_bytes()
    signature_bytes = _decode_sig_bytes(manifest_sig_path.read_text(encoding="utf-8", errors="ignore"))
    if not signature_bytes:
        raise RuntimeError("CRÍTICO: Assinatura do manifest vazia/ilegível; update abortado.")
    verify_manifest_signature(manifest_bytes, signature_bytes)

    expected = hash_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not verify_sha256(asset_path, expected):
        asset_path.unlink(missing_ok=True)
        hash_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        manifest_sig_path.unlink(missing_ok=True)
        raise RuntimeError(
            "CRÍTICO: Hash SHA256 do arquivo baixado não confere. Download abortado. "
            "Tente novamente ou reporte o incidente."
        )

    backup_path = create_backup(f"pre_update_v{version}")

    try:
        _install_asset(asset_path, suffix)
        run_migrations()
    except Exception as e:
        restore_backup(backup_path, clean=True)
        raise RuntimeError(f"CRÍTICO: Update falhou ({e}). Backup restaurado de {backup_path}.")
    finally:
        asset_path.unlink(missing_ok=True)
        hash_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        manifest_sig_path.unlink(missing_ok=True)


def _install_asset(asset_path: Path, suffix: str) -> None:
    install_dir = Path((os.getenv("SLAP_INSTALL_DIR") or "").strip() or ".")
    if suffix.endswith(".tar.gz"):
        with tarfile.open(asset_path, "r:gz") as tar:
            safe_extract_tar(tar, install_dir)
    elif suffix.endswith(".zip"):
        with zipfile.ZipFile(asset_path, "r") as zf:
            safe_extract_zip(zf, install_dir)
    else:
        raise RuntimeError("CRÍTICO: Formato de asset não suportado; instalação abortada.")
