"""
Utilitários para manipulação de perfil de sistema.
"""
import os
import re
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional


def generate_system_map_ascii(base_dir: str, target_dirs: List[str]) -> str:
    """Gera mapa ASCII da estrutura do sistema."""
    root = Path(str(base_dir))
    target_dirs = [root / d for d in target_dirs]
    ignore_dirs = {
        ".git", ".venv", "node_modules", "dist", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "media", ".trae"
    }

    def _tree(dir_path: Path, depth: int = 0, max_depth: int = 2) -> List[str]:
        if depth > max_depth:
            return []
        lines2: List[str] = []
        try:
            entries = sorted(
                list(dir_path.iterdir()),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except Exception:
            return []
        filtered = [p for p in entries if p.name not in ignore_dirs]
        for i, p in enumerate(filtered):
            name = p.name
            is_last = i == (len(filtered) - 1)
            prefix = ("│  " * depth) + ("└─ " if is_last else "├─ ")
            if p.is_dir():
                lines2.append(f"{prefix}{name}/")
                lines2.extend(_tree(p, depth + 1, max_depth))
            else:
                lines2.append(f"{prefix}{name}")
        return lines2

    counts = {"py": 0, "js": 0, "ts": 0}
    for d in target_dirs:
        try:
            if not d.exists():
                continue
            for p in d.rglob("*"):
                if p.is_dir():
                    if p.name in ignore_dirs:
                        continue
                    continue
                suf = p.suffix.lower()
                if suf == ".py":
                    counts["py"] += 1
                elif suf == ".js":
                    counts["js"] += 1
                elif suf in {".ts", ".tsx"}:
                    counts["ts"] += 1
        except Exception:
            continue

    lines: List[str] = []
    lines.append("Open Slap! — Mapa do Sistema")
    lines.append("")
    lines.append("Arquivos (amostra):")
    lines.append(f"- backend: .py={counts['py']}")
    lines.append(f"- frontend: .js={counts['js']} .ts/.tsx={counts['ts']}")
    lines.append("")
    lines.append("Estrutura (parcial):")
    for d in target_dirs:
        try:
            rel = str(d.relative_to(root)).replace("\\", "/")
        except Exception:
            rel = str(d).replace("\\", "/")
        lines.append(rel + "/")
        lines.extend(_tree(d, depth=0, max_depth=2))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def format_system_profile_summary(profile_data: Dict[str, Any]) -> str:
    """Formata resumo do perfil de sistema."""
    if not profile_data:
        return ""
    os_name = str(profile_data.get("os_name") or "")
    if not os_name:
        return ""
    lines = [f"SO: {os_name}"]
    top20 = profile_data.get("top20_productivity")
    if top20:
        lines.append("Top softwares (produtividade): " + ", ".join(
            [str(x.get("name") or "") for x in top20[:8]]
        ))
    return "\n".join(lines)
