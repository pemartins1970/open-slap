"""
🕵️ Soul Extractor — Heurística/regex para extração de campos de perfil
do texto de mensagens (user e assistant). Sem dependências circulares.
"""

import re
from typing import Dict, Set, Any, List

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

KNOWN_LANGUAGES: Set[str] = {
    "inglês", "english", "português", "portuguese", "espanhol", "spanish",
    "francês", "french", "alemão", "german", "italiano", "italian",
    "japonês", "japanese", "coreano", "korean", "mandarim", "chinese",
    "árabe", "arabic", "russo", "russian", "holandês", "dutch",
}

KNOWN_ROLES: Set[str] = {
    "estudante", "student", "engenheiro", "engineer", "programador",
    "programmer", "developer", "desenvolvedor", "analista", "analyst",
    "designer", "professor", "teacher", "pesquisador", "researcher",
    "cientista", "scientist", "gerente", "manager", "consultor",
    "consultant", "estagiário", "intern", "tech lead", "cto", "ceo",
}

_MAX_NOTES = 10

_AI_NAMES = {"sabrina", "assistant", "ai", "bot", "gpt", "alexa", "siri", "cortana"}

# --- name (self-introduction only; no greeting patterns — too unreliable) ---
# Decisão durante Sprint Beta (M-03):
# Greeting patterns ("Olá [Nome]", "Hi [Nome]") foram removidos porque
# produziam falsos positivos inaceitáveis: capturavam o nome do assistente
# (Sabrina, AI, etc.) ou palavras acidentais ("Olá, tudo bem?" capturava
# "tudo" como nome). Se necessário no futuro, reativar com validação
# adicional (ex: verificar se o nome capturado NÃO é um AI_NAME conhecido
# ou se coincide com auto-introdução explícita na mesma mensagem).
_NAME_PATTERNS = [
    r"(?:meu nome|me chamo|eu sou o|eu sou a) (?:[eé] )?([A-ZÀ-Ÿ][a-zà-ÿ]{2,30})",
    r"my name is ([A-Z][a-z]{2,30})",
    r"i'?m ([A-Z][a-z]{2,30})",
    r"nome[:\s]+([A-ZÀ-Ÿ][a-zà-ÿ]{2,30})",
    r"your name is ([A-Z][a-z]{2,30})",
]

# --- programming_language ---
_LANG_TRIGGER_PATTERNS = [
    r"linguagem de programação[^é]*é\s+(\w[\w+#]*)",
    r"linguagem principal[^é]*é\s+(\w[\w+#]*)",
    r"trabalha(?:ndo)? com\s+(\w[\w+#]*)",
    r"usa\s+(\w[\w+#]*)\s+(?:como|para|em)",
    r"programando em\s+(\w[\w+#]*)",
    r"programming language[^i]*is\s+(\w[\w+#]*)",
    r"works? with\s+(\w[\w+#]*)",
    r"uses?\s+(\w[\w+#]*)\s+(?:as|for|in)",
]

# --- age_range ---
_AGE_PATTERNS = [
    r"tenho (\d{2})\s*(?:anos|ano)",
    r"idade[:\s]+(\d{2})",
    r"sou de (\d{2})\s*(?:anos|ano)",
    r"i'?m (\d{2})\s*(?:years? old|yo)",
    r"age[:\s]+(\d{2})",
    r"tengo (\d{2})\s*(?:años|año)",
]

# --- interests ---
_INTEREST_PATTERNS = [
    r"(?:gosto|curto) (?:muito )?(?:de )?(.+?)(?:\.|,|$| e | e também)",
    r"interessado em (.+?)(?:\.|,|$| e | e também)",
    r"me interesso por (.+?)(?:\.|,|$| e | e também)",
    r"(?:sou|sou muito) (?:apaixonado|fã) por (.+?)(?:\.|,|$| e | e também)",
    r"interested in (.+?)(?:\.|,|$| and | and also)",
    r"passionate about (.+?)(?:\.|,|$| and | and also)",
    r"i (?:like|love) (.+?)(?:\.|,|$| and | and also)",
]

# --- goals ---
_GOAL_PATTERNS = [
    r"(?:quero|gostaria de|pretendo) (.+?)(?:\.|,|$| e | e também)",
    r"meu objetivo é (.+?)(?:\.|,|$| e | e também)",
    r"estou (?:aprendendo|estudando) (.+?)(?:\.|,|$| e | e também)",
    r"i (?:want to|would like to|plan to|will) (.+?)(?:\.|,|$| and )",
    r"my goal is (.+?)(?:\.|,|$| and )",
    r"i'?m (?:learning|studying) (.+?)(?:\.|,|$| and )",
]

# --- education ---
_EDUCATION_PATTERNS = [
    r"(?:sou|sou um|sou uma) (estudante|engenheiro|programador|analista|designer|desenvolvedor|professor|pesquisador|cientista|gerente|consultor|estagiário|tech lead|cto|ceo)",
    r"(?:formado|graduado) (.+?)(?:\.|,|$| pela | na | no | por )",
    r"estudo (.+?)(?:\.|,|$| na | no )",
    r"i'?m (?:a|an) (student|engineer|programmer|analyst|designer|developer|teacher|researcher|scientist|manager|consultant|intern)",
    r"(?:graduated|studied) (.+?)(?:\.|,|$| at | in | from )",
]

# --- learning_style ---
_LEARNING_PATTERNS = [
    r"aprendo melhor (.+?)(?:\.|,|$)",
    r"prefiro (?:ler|ver|praticar|video|audio|escrever|ler|assistir|fazer)",
    r"me ajuda mais (.+?)(?:\.|,|$)",
    r"i learn best (.+?)(?:\.|,|$)",
    r"i prefer (?:reading|watching|practicing|video|audio|writing|listening|doing)",
]

# --- language ---
_LANGUAGE_PATTERNS = [
    r"falo ([\w\s]+?)(?:\.|,|$| e | fluente| fluentemente)",
    r"idioma[:\s]+([\w\s]+?)(?:\.|,|$)",
    r"languages?[:\s]+([\w\s]+?)(?:\.|,|$)",
    r"i speak ([\w\s]+?)(?:\.|,|$| and | fluently)",
    r"fluent in ([\w\s]+?)(?:\.|,|$| and )",
]

# --- audience ---
_AUDIENCE_PATTERNS = [
    r"(?:para|focado em|voltado para) (iniciantes|devs|desenvolvedores|profissionais|estudantes|junior|senior|pleno|beginners|developers|professionals|students)",
    r"(?:targeting|aimed at|for) (beginners|developers|professionals|students|junior|senior)",
]

_SINGLE_VALUE_FIELDS = {
    "name", "programming_language", "age_range", "education",
    "learning_style", "language", "audience",
}

_LIST_FIELDS = {"interests", "goals"}
_NOTES_FIELD = "notes"


def _match_any(text: str, patterns: List[str]) -> str:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return ""


def extract_soul_fields(text: str) -> Dict[str, Any]:
    """
    Extrai campos SOUL do texto usando heurística/regex.
    Retorna dict com campos encontrados. Para list-fields, retorna lista.
    """
    fields: Dict[str, Any] = {}
    text_lower = text.lower()

    # --- name (skip patterns that capture AI/assistant names) ---
    for pattern in _NAME_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in _AI_NAMES:
                fields["name"] = candidate
                break

    # --- programming_language ---
    for pattern in _LANG_TRIGGER_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().lower().rstrip(".,;")
            if candidate in KNOWN_PROGRAMMING_LANGUAGES:
                fields["programming_language"] = m.group(1).strip().rstrip(".,;")
                break
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

    # --- age_range ---
    val = _match_any(text, _AGE_PATTERNS)
    if val:
        fields["age_range"] = val

    # --- interests (list) ---
    interests = []
    for pattern in _INTEREST_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            val = m.group(1).strip().rstrip(".,;!?")
            if val and len(val) < 60 and val.lower() not in ("disso", "nisso", "como", "que", "isso", "it", "that"):
                interests.append(val.capitalize())
    if interests:
        fields["interests"] = list(dict.fromkeys(interests))[:5]

    # --- goals (list) ---
    goals = []
    for pattern in _GOAL_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            val = m.group(1).strip().rstrip(".,;!?")
            if val and len(val) < 80 and val.lower() not in ("disso", "nisso", "como", "que", "isso", "it", "that", "saber", "saber mais", "fazer"):
                goals.append(val[0].upper() + val[1:] if val else val)
    if goals:
        fields["goals"] = list(dict.fromkeys(goals))[:5]

    # --- education ---
    for pattern in _EDUCATION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().rstrip(".,;")
            if val and len(val) < 50:
                fields["education"] = val
                break

    # --- learning_style ---
    val = _match_any(text, _LEARNING_PATTERNS)
    if val:
        fields["learning_style"] = val

    # --- language ---
    for pattern in _LANGUAGE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().rstrip(".,;").lower()
            words = val.split()
            matched = [w for w in words if w in KNOWN_LANGUAGES]
            if matched:
                fields["language"] = ", ".join(matched).title()
                break

    # --- audience ---
    val = _match_any(text, _AUDIENCE_PATTERNS)
    if val:
        fields["audience"] = val

    # --- notes (gender excluded — see M-04) ---
    # TODO: reativar extração de gender quando M-04 (SOUL edit UI) estiver implementado
    # para que o usuário possa visualizar e corrigir o dado extraído.

    return fields


def save_to_soul(user_id: int, fields: Dict[str, Any], source_content: str) -> None:
    """Persiste campos extraídos no SOUL do usuário."""
    if not fields:
        return

    existing = get_user_soul(user_id)
    soul_update: Dict[str, Any] = (
        dict(existing["data"]) if existing and existing.get("data") else {}
    )

    changed = False

    for key, value in fields.items():
        if key in _SINGLE_VALUE_FIELDS:
            old = soul_update.get(key)
            if value != old:
                soul_update[key] = value
                changed = True
        elif key in _LIST_FIELDS:
            old = soul_update.get(key, [])
            if isinstance(old, list):
                merged = list(dict.fromkeys(old + value))
                if merged != old:
                    soul_update[key] = merged[:5]
                    changed = True
            else:
                soul_update[key] = value[:5]
                changed = True
        elif key == _NOTES_FIELD:
            old = soul_update.get(key, [])
            if isinstance(old, list):
                merged = old + [value] if isinstance(value, str) else old + list(value)
                soul_update[key] = merged[-_MAX_NOTES:]
                if soul_update[key] != old:
                    changed = True
            else:
                soul_update[key] = [value] if isinstance(value, str) else list(value)
                changed = True

    if not changed:
        return

    upsert_user_soul(user_id, soul_update, "")

    for key, value in fields.items():
        append_soul_event(
            user_id=user_id,
            source="chat_pipeline",
            content=f"{key}: {value}",
        )
