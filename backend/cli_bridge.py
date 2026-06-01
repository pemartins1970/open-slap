import os
import re
import sys
import json
import time
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List


def _sanitize_text(v: Any) -> str:
    s = str(v or "").strip()
    if (
        (s.startswith("`") and s.endswith("`"))
        or (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    return s


_SAFE_TOKEN_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_-]{0,63}$")
_SAFE_PARAM_KEY_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")


def _is_safe_token(v: str) -> bool:
    return bool(_SAFE_TOKEN_RE.match(str(v or "").strip()))


def _is_safe_param_key(v: str) -> bool:
    return bool(_SAFE_PARAM_KEY_RE.match(str(v or "").strip()))


def _safe_str_value(v: Any, *, max_len: int = 512) -> str:
    s = _sanitize_text(v)
    s = s.replace("\r", " ").replace("\n", " ").strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s


def _default_whitelist() -> Dict[str, Dict[str, Any]]:
    return {
        "drawio-cli": {
            "exe": os.getenv("OPENSLAP_DRAWIO_CLI_EXE") or "drawio-cli",
            "artifacts_env": "OPENSLAP_DRAWIO_ARTIFACTS_DIR",
        },
        "blender-cli": {
            "exe": os.getenv("OPENSLAP_BLENDER_CLI_EXE") or "blender-cli",
            "artifacts_env": "OPENSLAP_BLENDER_ARTIFACTS_DIR",
        },
        "gimp-cli": {
            "exe": os.getenv("OPENSLAP_GIMP_CLI_EXE") or "gimp-cli",
            "artifacts_env": "OPENSLAP_GIMP_ARTIFACTS_DIR",
        },
        "irfanview": {
            "exe": os.getenv("OPENSLAP_IRFANVIEW_EXE") or "i_view64.exe",
            "artifacts_env": "OPENSLAP_IRFANVIEW_ARTIFACTS_DIR",
        },
        "python-inline": {
            "exe": sys.executable or "python",
            "artifacts_env": "",
        },
        "winget": {
            "exe": "winget",
            "artifacts_env": "",
        },
        "brew": {
            "exe": "brew",
            "artifacts_env": "",
        },
        "apt": {
            "exe": "apt",
            "artifacts_env": "",
        },
    }


_EXE_HINTS: List[tuple] = [
    ("gimp", "gimp"),
    ("inkscape", "inkscape"),
    ("irfanview", "i_view64"),
    ("imagemagick", "magick"),
    ("drawio", "drawio"),
    ("draw.io", "drawio"),
    ("blender", "blender"),
    ("ffmpeg", "ffmpeg"),
    ("vlc", "vlc"),
    ("obs", "obs64"),
    ("sharex", "sharex"),
    ("greenshot", "greenshot"),
    ("7-zip", "7z"),
    ("notepad++", "notepad++"),
    ("autohotkey", "autohotkey"),
    ("nircmd", "nircmd"),
]


def _resolve_exe_from_item(item: Dict[str, Any]) -> Optional[str]:
    name = str(item.get("name") or "").strip().lower()
    pkg_id = str(item.get("id") or "").strip().lower()
    for keyword, exe_candidate in _EXE_HINTS:
        if keyword in name or keyword in pkg_id:
            resolved = shutil.which(exe_candidate)
            if resolved:
                return resolved
    return None


def build_dynamic_whitelist(
    installed: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    wl = _default_whitelist()
    if not installed:
        return wl
    for item in installed:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in wl:
            continue
        exe = _resolve_exe_from_item(item)
        if exe:
            wl[key] = {
                "exe": exe,
                "artifacts_env": "",
            }
    return wl


def parse_cli_command_text(
    command_text: str,
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    text = _sanitize_text(command_text)
    if not text:
        return None, None, {}
    try:
        parts = shlex.split(text, posix=False)
    except Exception:
        parts = text.split()
    if not parts:
        return None, None, {}
    app_name = _sanitize_text(parts[0])
    action = None
    params: Dict[str, Any] = {}
    i = 1
    while i < len(parts):
        token = str(parts[i] or "").strip()
        if token.startswith("--"):
            key = token[2:].strip()
            val: Any = True
            if i + 1 < len(parts) and not parts[i + 1].startswith("--"):
                val = _sanitize_text(parts[i + 1])
                i += 1
            if key:
                params[key] = val
        i += 1
    if "action" in params:
        action = _sanitize_text(params.get("action"))
        params.pop("action", None)
    return app_name, action, params


def _collect_artifacts(artifacts_dir: Optional[str]) -> Dict[str, Any]:
    p = Path(str(artifacts_dir or "").strip())
    if not (p and p.exists() and p.is_dir()):
        return {"summary": "", "files": []}

    files: List[Path] = []
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".txt", ".log", ".json"):
        try:
            files.extend(list(p.glob(f"*{ext}")))
        except Exception:
            continue
    files = [f for f in files if f.is_file()]
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    files = files[:10]

    summary_parts: List[str] = []
    out_files: List[Dict[str, Any]] = []
    for f in files:
        try:
            stat = f.stat()
            out_files.append(
                {
                    "path": str(f),
                    "size": int(stat.st_size),
                    "mtime": int(stat.st_mtime),
                }
            )
            if f.suffix.lower() in {".txt", ".log", ".json"}:
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    content = content.strip()
                    if content:
                        snippet = content[-1200:].lstrip()
                        summary_parts.append(f"{f.name}: {snippet}")
                except Exception:
                    summary_parts.append(f"{f.name}: (não foi possível ler)")
            else:
                summary_parts.append(f"{f.name}: arquivo gerado ({stat.st_size} bytes)")
        except Exception:
            continue

    summary = "\n".join([s for s in summary_parts if s]).strip()
    return {"summary": summary, "files": out_files}


def execute_cli_command(
    app_name: str,
    action: str,
    params: Dict[str, Any],
    *,
    timeout_s: Optional[int] = None,
    whitelist: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    wl = whitelist or _default_whitelist()
    app_key = _sanitize_text(app_name)
    if app_key not in wl:
        return {
            "status": "error",
            "command_executed": "",
            "output": "",
            "visual_state_summary": "",
            "error": f"Executável não permitido: {app_key}",
        }
    if not _is_safe_token(action):
        return {
            "status": "error",
            "command_executed": "",
            "output": "",
            "visual_state_summary": "",
            "error": "Ação inválida.",
        }

    timeout_final = int(
        timeout_s
        or int(str(os.getenv("OPENSLAP_CLI_TIMEOUT_S") or "25").strip() or "25")
    )
    exe = _sanitize_text((wl.get(app_key) or {}).get("exe") or app_key)

    native_cmd = app_key in {"winget", "apt", "brew"}
    if native_cmd:
        args: List[str] = [exe, _sanitize_text(action)]
    else:
        args = [exe, "--action", _sanitize_text(action)]
    safe_params: Dict[str, Any] = {}
    for k, v in (params or {}).items():
        key = _sanitize_text(k)
        if not _is_safe_param_key(key):
            continue
        if v is True:
            args.append(f"--{key}")
            safe_params[key] = True
            continue
        if v in (False, None, ""):
            continue
        sval = _safe_str_value(v)
        if not sval:
            continue
        args.extend([f"--{key}", sval])
        safe_params[key] = sval

    if app_key == "winget":
        flags = {"--accept-source-agreements", "--accept-package-agreements"}
        present = set([a for a in args if a.startswith("--accept-")])
        for f in flags - present:
            args.append(f)
        if action == "install" and "--silent" not in args:
            args.append("--silent")
    if app_key == "apt":
        if action in {"install", "remove", "update", "upgrade"} and "-y" not in args and "--yes" not in args:
            args.append("-y")
    if app_key == "brew":
        pass

    started_at = time.time()
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_final,
            check=False,
        )
        stdout = str(proc.stdout or "")
        stderr = str(proc.stderr or "")
        ok = proc.returncode == 0
        status = "success" if ok else "error"
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = f"Timeout após {timeout_final}s"
        status = "error"
    except Exception as e:
        stdout = ""
        stderr = str(e)
        status = "error"

    artifacts_dir = (
        _safe_str_value((params or {}).get("artifacts_dir"))
        or _sanitize_text(os.getenv((wl.get(app_key) or {}).get("artifacts_env") or ""))
        or _sanitize_text(os.getenv("OPENSLAP_CLI_ARTIFACTS_DIR") or "")
    )

    artifacts = _collect_artifacts(artifacts_dir)
    visual_summary = _sanitize_text(artifacts.get("summary") or "")

    output_bundle = {
        "stdout": stdout[-8000:],
        "stderr": stderr[-8000:],
        "return_ms": int((time.time() - started_at) * 1000),
        "params": safe_params,
        "artifacts": artifacts.get("files") or [],
    }

    return {
        "status": status,
        "command_executed": " ".join(args),
        "output": json.dumps(output_bundle, ensure_ascii=False),
        "visual_state_summary": visual_summary[:4000],
    }
