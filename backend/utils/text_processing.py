"""
Utilitários de Processamento de Texto
"""

import re
from typing import Dict, Any, List


def strip_assistant_directives(text: str) -> str:
    """Remove diretivas especiais do assistant do texto"""
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r"\[\[assistant_split(?::\d{1,5})?\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\[open_settings:[a-z0-9_-]+\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(
        r"\[\[(?:set_expert|force_expert):[a-z0-9_-]+\]\]", "", s, flags=re.IGNORECASE
    )
    s = re.sub(r"\[\[clear_expert\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s


def build_ide_context_block(ide_ctx: Dict[str, Any]) -> str:
    """Constrói bloco de contexto IDE para exibição"""
    if not isinstance(ide_ctx, dict) or not ide_ctx:
        return ""

    parts: List[str] = ["--- IDE context ---"]

    ws = ide_ctx.get("workspace") or {}
    if isinstance(ws, dict):
        name = str(ws.get("name") or "").strip()
        root = str(ws.get("rootPath") or ws.get("root") or "").strip()
        if name or root:
            parts.append(f"workspace: {name}".rstrip() if name else "workspace: (sem nome)")
        if root:
            parts.append(f"root: {root}")

    editor = ide_ctx.get("editor") or {}
    if isinstance(editor, dict):
        active_file = str(editor.get("activeFile") or "").strip()
        language = str(editor.get("languageId") or "").strip()
        selection = editor.get("selection") or {}
        if active_file:
            parts.append(f"activeFile: {active_file}" + (f" ({language})" if language else ""))
        if isinstance(selection, dict):
            s = selection.get("text")
            if isinstance(s, str) and s.strip():
                s2 = s.strip()
                if len(s2) > 1200:
                    s2 = s2[:1200].rstrip() + "..."
                parts.append("selection:\n" + s2)

    diag = ide_ctx.get("diagnostics")
    if isinstance(diag, list) and diag:
        parts.append(f"diagnostics_count: {len(diag)}")

    parts.append("--- End IDE context ---")
    return "\n".join(parts).strip()


def todo_items_from_user_message(user_message: str) -> List[str]:
    """Extrai itens TODO da mensagem do usuário"""
    text = (user_message or "").strip()
    if not text:
        return []

    # Procura por marcadores TODO em vários formatos
    todo_patterns = [
        r'- \[ \]\s*(.+?)(?=\n|$)',  # - [ ] item
        r'-\s*\[ \]\s*(.+?)(?=\n|$)',  # -[ ] item
        r'\*\s*\[ \]\s*(.+?)(?=\n|$)',  # *[ ] item
        r'(\[\s*\]\s*.+?)(?=\n|$)',  # [ ] item
        r'(TODO:\s*.+?)(?=\n|$)',  # TODO: item
        r'(AFazer:\s*.+?)(?=\n|$)',  # AFazer: item
    ]

    items = []
    for pattern in todo_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            item = match.strip()
            if item and len(item) > 2:  # Ignora itens muito curtos
                # Remove marcadores restantes
                item = re.sub(r'^\[\s*\]\s*', '', item).strip()
                item = re.sub(r'^(TODO:|AFazer:)\s*', '', item, flags=re.IGNORECASE).strip()
                if item:
                    items.append(item)

    return items


def looks_like_personal_todo_capture(user_message: str) -> bool:
    """Verifica se a mensagem parece ser uma captura de TODO pessoal"""
    lower = " ".join(str(user_message or "").lower().split()).strip()
    if not lower:
        return False

    todo_indicators = [
        "todo", "afazer", "fazer", "preciso", "lembrete", "anotar",
        "registrar", "adicionar", "criar tarefa", "nova tarefa"
    ]

    return any(indicator in lower for indicator in todo_indicators) and len(lower) < 200
