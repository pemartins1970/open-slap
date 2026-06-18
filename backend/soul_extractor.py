"""
🕵️ Soul Extractor — Heurística/regex para extração de campos de perfil
do texto de mensagens assistant. Sem dependências circulares.
"""

import re
from typing import Dict, Set, Any

from .db import (
    get_user_soul,
    upsert_user_soul,
    append_soul_event,
)

KNOWN_PROGRAMMING_LANGUAGES: Set[str] = {
    "python", "javascript", "typescript", "java", "rust", "go", "golang",
    "ruby", "php", "c++", "c#", "swift", "kotlin", "scala", "r",
    "haskell", "elixir", "clojure", "dart", "lua", "perl", "bash",
}


def extract_soul_fields(text: str) -> Dict[str, str]:
    """
    Extrai campos SOUL do texto de uma mensagem assistant usando heurística/regex.
    Retorna apenas campos extraídos com confiança suficiente.
    """
    fields: Dict[str, str] = {}
    text_lower = text.lower()

    # --- name ---
    name_patterns = [
        r"olá[,\s]+([A-ZÀ-Ÿ][a-zà-ÿ]{1,30})[\s!,\.]",
        r"seu nome é ([A-ZÀ-Ÿ][a-zà-ÿ]{1,30})",
        r"nome[:\s]+([A-ZÀ-Ÿ][a-zà-ÿ]{1,30})",
        r"hi[,\s]+([A-Z][a-z]{1,30})[\s!,\.]",
        r"your name is ([A-Z][a-z]{1,30})",
    ]
    for pattern in name_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            fields["name"] = m.group(1).strip()
            break

    # --- programming_language ---
    lang_trigger_patterns = [
        r"linguagem de programação[^é]*é\s+(\w[\w+#]*)",
        r"linguagem principal[^é]*é\s+(\w[\w+#]*)",
        r"trabalha(?:ndo)? com\s+(\w[\w+#]*)",
        r"usa\s+(\w[\w+#]*)\s+(?:como|para|em)",
        r"programando em\s+(\w[\w+#]*)",
        r"programming language[^i]*is\s+(\w[\w+#]*)",
        r"works? with\s+(\w[\w+#]*)",
        r"uses?\s+(\w[\w+#]*)\s+(?:as|for|in)",
    ]
    for pattern in lang_trigger_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().lower().rstrip(".,;")
            if candidate in KNOWN_PROGRAMMING_LANGUAGES:
                fields["programming_language"] = m.group(1).strip().rstrip(".,;")
                break

    # Fallback: short names need \b to avoid false positives
    if "programming_language" not in fields:
        for lang in sorted(KNOWN_PROGRAMMING_LANGUAGES, key=len, reverse=True):
            if lang in ("r", "go"):
                if re.search(rf"\b{re.escape(lang)}\b", text_lower):
                    fields["programming_language"] = lang.capitalize()
                    break
            else:
                if lang in text_lower:
                    fields["programming_language"] = lang.capitalize()
                    break

    return fields


def save_to_soul(user_id: int, fields: Dict[str, str], source_content: str) -> None:
    """Persiste campos extraídos no SOUL do usuário."""
    if not fields:
        return

    existing = get_user_soul(user_id)
    soul_update = dict(existing["data"]) if existing and existing.get("data") else {}

    if "name" in fields:
        soul_update["name"] = fields["name"]
    if "programming_language" in fields:
        soul_update["programming_language"] = fields["programming_language"]

    upsert_user_soul(user_id, soul_update, "")

    for field, value in fields.items():
        append_soul_event(
            user_id=user_id,
            source="assistant_message_save",
            content=f"{field}: {value}",
        )
