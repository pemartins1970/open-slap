import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CACHE_TTL_S = 60
_cache_ts: float = 0.0
_cache: Optional[List[Dict[str, Any]]] = None

_KNOWN_HARNESSES = [
    "blender",
    "gimp",
    "inkscape",
    "audacity",
    "libreoffice",
    "obs-studio",
    "kdenlive",
    "shotcut",
    "drawio",
    "mermaid",
    "comfyui",
    "ollama",
    "adguardhome",
    "notebooklm",
    "anygen",
    "zoom",
    "mubu",
]


def _parse_skill_md(content: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"name": "", "description": "", "commands": []}
    if not content:
        return info

    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for line in fm.splitlines():
            if line.startswith("name:"):
                info["name"] = line.split(":", 1)[-1].strip().strip('"').strip("'")
            elif line.startswith("description:"):
                info["description"] = (
                    line.split(":", 1)[-1].strip().strip('"').strip("'")
                )

    cmds: List[str] = []
    for line in content.splitlines():
        stripped = line.lstrip("#").strip()
        if line.startswith("###") and stripped:
            cmds.append(stripped)
        elif line.startswith("- `") and "`" in line:
            cmd = re.findall(r"`([^`]+)`", line)
            if cmd:
                cmds.extend(cmd[:1])
    info["commands"] = cmds[:20]
    return info


def _probe_harness(name: str) -> Optional[Dict[str, Any]]:
    bin_name = f"cli-anything-{name}"
    exe_path = shutil.which(bin_name) or ""

    skill_content = ""
    skill_path = ""

    try:
        pkg_name = f"cli-anything-{name}"
        result = subprocess.run(
            ["pip", "show", pkg_name], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Location:"):
                    loc = line.split(":", 1)[-1].strip()
                    candidate = (
                        Path(loc)
                        / "cli_anything"
                        / name.replace("-", "_")
                        / "skills"
                        / "SKILL.md"
                    )
                    if not candidate.exists():
                        candidate = Path(loc) / "cli_anything" / name / "skills" / "SKILL.md"
                    if candidate.exists():
                        skill_content = candidate.read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        skill_path = str(candidate)
                        break
    except Exception:
        pass

    if not skill_content:
        extra_dirs = str(os.getenv("FORGE_HARNESS_DIRS") or "").strip()
        for d in extra_dirs.split(os.pathsep):
            d = d.strip()
            if not d:
                continue
            for sub in (name, name.replace("-", "_")):
                candidate = Path(d) / sub / "skills" / "SKILL.md"
                if candidate.exists():
                    skill_content = candidate.read_text(
                        encoding="utf-8", errors="ignore"
                    )
                    skill_path = str(candidate)
                    break
            if skill_content:
                break

    if not exe_path and not skill_content:
        return None

    parsed = _parse_skill_md(skill_content)
    display_name = parsed.get("name") or bin_name
    description = parsed.get("description") or f"CLI-Anything harness for {name}"

    return {
        "name": name,
        "bin_name": bin_name,
        "display_name": display_name,
        "description": description,
        "commands": parsed.get("commands") or [],
        "exe_path": exe_path,
        "skill_path": skill_path,
        "available": bool(exe_path),
    }


def discover_harnesses(force: bool = False) -> List[Dict[str, Any]]:
    global _cache, _cache_ts
    if not force and _cache is not None and (time.time() - _cache_ts) < _CACHE_TTL_S:
        return _cache

    results: List[Dict[str, Any]] = []
    seen: set = set()

    for name in _KNOWN_HARNESSES:
        try:
            h = _probe_harness(name)
            if h:
                results.append(h)
                seen.add(name)
        except Exception as e:
            logger.debug("probe harness %s failed: %s", name, e)

    try:
        path_dirs = (os.getenv("PATH") or "").split(os.pathsep)
        for d in path_dirs:
            try:
                p = Path(d)
                if not p.is_dir():
                    continue
                for f in p.iterdir():
                    bname = f.name
                    if bname.startswith("cli-anything-") and f.is_file():
                        extra_name = bname[len("cli-anything-") :]
                        if extra_name and extra_name not in seen:
                            try:
                                h = _probe_harness(extra_name)
                                if h:
                                    results.append(h)
                                    seen.add(extra_name)
                            except Exception:
                                pass
            except Exception:
                pass
    except Exception:
        pass

    _cache = results
    _cache_ts = time.time()
    return results


def build_harnesses_context_block(
    harnesses: Optional[List[Dict[str, Any]]] = None,
) -> str:
    h_list = harnesses if harnesses is not None else discover_harnesses()
    available = [h for h in h_list if h.get("available")]
    if not available:
        return ""

    lines = ["Ferramentas CLI-Anything disponíveis na máquina:"]
    for h in available:
        cmds_preview = ", ".join(h.get("commands") or [])[:120]
        line = f"- {h['bin_name']}: {h.get('description') or ''}".rstrip()
        if cmds_preview:
            line += f" | comandos: {cmds_preview}"
        lines.append(line)
    lines.append("Para usar: TOOL_CALL: <bin_name> <subcommand> --json [args]")
    return "\n".join(lines)


def harnesses_to_json() -> str:
    return json.dumps(discover_harnesses(), ensure_ascii=False, indent=2)

