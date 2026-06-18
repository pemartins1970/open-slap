"""
🤖 LLM MANAGER SIMPLES - Versão sem dependências externas
Gerenciamento de providers LLM (Gemini, Groq, Ollama)
"""

import os
import json
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple
import aiohttp
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
import itertools
from backend.utils.text_processing import strip_internal_markup


class RateLimitError(Exception):
    """Indica rate limit (HTTP 429) — usado para gatilhar rotação de chave ou fallback de provider"""
    pass


def _parse_retry_after(response) -> Optional[float]:
    """Lê header Retry-After e retorna segundos de espera, ou None se ausente/inválido.
    Suporta formato decimal (ex: '120') e HTTP-date (ex: 'Fri, 31 Dec 1999 23:59:59 GMT')."""
    raw = response.headers.get("Retry-After") if hasattr(response, "headers") else None
    if not raw:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        retry_time = parsedate_to_datetime(raw)
        if retry_time:
            now = datetime.now(retry_time.tzinfo) if retry_time.tzinfo else datetime.now()
            return max(0.0, (retry_time - now).total_seconds())
    except Exception:
        pass
    return None


def _extract_retry_from_body(body: str) -> Optional[float]:
    """Tenta extrair tempo de retry do corpo da resposta (fallback para providers que enviam no JSON)."""
    match = re.search(r'[Rr]etry\s+[Ii]n\s+([\d.]+)\s*s', body or "")
    if match:
        return float(match.group(1))
    return None


async def _wait_retry_after(response, body: str = "", default_seconds: float = 5.0, cap: float = 300.0) -> None:
    """Espera o tempo do header Retry-After, com fallback no body, default e cap de segurança."""
    seconds = _parse_retry_after(response)
    if seconds is None and body:
        seconds = _extract_retry_from_body(body)
    if seconds is None:
        seconds = default_seconds
    seconds = min(seconds, cap)
    print(f"[llm_manager] Rate limit detectado — aguardando {seconds:.0f}s...")
    await asyncio.sleep(seconds)


def _is_rate_limited(status: int, body: str) -> bool:
    """Retorna True se status HTTP ou body indicam rate limit / quota exhaustion.
    Checks:
      1. status HTTP (429, 503)
      2. JSON body com error.status == "RESOURCE_EXHAUSTED" ou error.code == 429
      3. Fallback: string search se body não for JSON válido
    """
    if status in (429, 503):
        return True
    if not body or not body.strip():
        return False
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        lowered = body.lower()
        return "resource_exhausted" in lowered or "resource exhausted" in lowered or "rate limit" in lowered or "quota" in lowered
    err = parsed.get("error") if isinstance(parsed, dict) else None
    if not isinstance(err, dict):
        return False
    if str(err.get("status", "")).upper() == "RESOURCE_EXHAUSTED":
        return True
    if err.get("code") in (429, 8):
        return True
    return False


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

HTTP_TIMEOUT_S = float(str(os.getenv("OPENSLAP_HTTP_TIMEOUT_S") or "6").strip() or "6")
CONTEXT_WINDOW_MESSAGES = 10  # Número fixo de mensagens do histórico enviadas ao LLM


def _sanitize_text(v: Any) -> str:
    s = str(v or "").strip()
    if (
        (s.startswith("`") and s.endswith("`"))
        or (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    s = s.strip(" ,")
    return s


def _sanitize_api_key(v: Any) -> str:
    s = _sanitize_text(v)
    return "".join(s.split())


def _sanitize_url_base(v: Any) -> str:
    return _sanitize_text(v).rstrip("/")


def _normalize_openai_compatible_base_url(v: Any) -> str:
    base = _sanitize_url_base(v)
    if not base:
        return base
    for suffix in ("/chat/completions", "/models"):
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")
    return base


def _normalize_ollama_url(v: Any) -> str:
    base = _sanitize_url_base(v)
    if not base:
        return base
    for suffix in (
        "/api/generate",
        "/api/chat",
        "/api/tags",
        "/v1",
        "/api",
        "/openai/v1",
    ):
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")
    return base


def load_conversation_history(conversation_id: int, limit: int = CONTEXT_WINDOW_MESSAGES) -> List[Dict[str, str]]:
    try:
        from backend.db import get_conversation_messages
        all_msgs = get_conversation_messages(conversation_id) or []
    except Exception:
        return []
    filtered = [m for m in all_msgs if m.get("role") in ("user", "assistant")]
    recent = filtered[-limit:] if len(filtered) > limit else filtered
    for m in recent:
        raw = m.get("content") or ""
        cleaned = strip_internal_markup(raw)
        m["content"] = cleaned
    return recent


class LLMManager:
    """Gerenciador de LLMs - Versão Simplificada"""

    def __init__(self):
        self.providers = self._load_providers()
        self.provider_order = self._get_provider_order()
        self._gemini_models_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._gemini_model_pick_cache: Dict[str, str] = {}

    def _load_providers(self) -> Dict[str, Dict[str, Any]]:
        """Carrega configurações dos providers do ambiente"""
        providers = {}

        # Gemini
        gemini_keys = os.getenv("GEMINI_API_KEYS", "").split(",")
        if gemini_keys and gemini_keys[0]:
            providers["gemini"] = {
                "name": "Gemini",
                "keys": [
                    _sanitize_api_key(key)
                    for key in gemini_keys
                    if _sanitize_api_key(key)
                ],
                "current_key_index": 0,
                "model": _sanitize_text(os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
                "base_url": _sanitize_url_base(
                    os.getenv(
                        "GEMINI_BASE_URL",
                        "https://generativelanguage.googleapis.com/v1",
                    )
                ),
                "enabled": True,
            }

        # Groq
        groq_keys = os.getenv("GROQ_API_KEYS", "").split(",")
        if groq_keys and groq_keys[0]:
            providers["groq"] = {
                "name": "Groq",
                "keys": [
                    _sanitize_api_key(key)
                    for key in groq_keys
                    if _sanitize_api_key(key)
                ],
                "current_key_index": 0,
                "model": _sanitize_text(
                    os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
                ),
                "base_url": _normalize_openai_compatible_base_url(
                    os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
                ),
                "enabled": True,
            }

        # Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_model = _sanitize_text(os.getenv("OLLAMA_MODEL", "llama3.2"))
        if ollama_url:
            providers["ollama"] = {
                "name": "Ollama",
                "url": _normalize_ollama_url(ollama_url),
                "model": ollama_model,
                "enabled": True,
            }

        # OpenAI
        openai_key = _sanitize_api_key(os.getenv("OPENAI_API_KEY", ""))
        if openai_key:
            providers["openai"] = {
                "name": "OpenAI",
                "key": openai_key,
                "model": _sanitize_text(os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
                "base_url": _normalize_openai_compatible_base_url(
                    os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
                ),
                "enabled": True,
            }

        # OpenRouter (OpenAI-compatible)
        openrouter_key = _sanitize_api_key(os.getenv("OPENROUTER_API_KEY", ""))
        if openrouter_key:
            default_model = _sanitize_text(
                os.getenv(
                    "OPENROUTER_MODEL",
                    "nvidia/nemotron-3-nano-30b-a3b:free",
                )
            )
            providers["openrouter"] = {
                "name": "OpenRouter",
                "key": openrouter_key,
                "model": default_model,
                "models": [
                    default_model,
                    "qwen/qwen3-coder:free",
                    "meta-llama/llama-3.2-3b-instruct:free",
                    "google/gemma-3-12b-it:free",
                ],
                "base_url": _normalize_openai_compatible_base_url(
                    os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
                ),
                "enabled": True,
            }

        return providers

    def _get_provider_order(self) -> List[str]:
        """Obtém ordem de fallback dos providers"""
        order = os.getenv("PROVIDER_ORDER", "gemini,groq,ollama,openai,openrouter")
        return [provider.strip() for provider in order.split(",") if provider.strip()]

    def _get_next_key(self, provider_id: str) -> Optional[str]:
        """Obtém próxima chave API (round-robin)"""
        provider = self.providers.get(provider_id)
        if not provider or "keys" not in provider:
            return None

        keys = provider["keys"]
        if not keys:
            return None

        current_index = provider["current_key_index"]
        key = _sanitize_api_key(keys[current_index])

        # Avançar para próxima chave
        provider["current_key_index"] = (current_index + 1) % len(keys)

        return key or None

    async def _test_provider(self, provider_id: str) -> bool:
        """Testa se provider está funcionando"""
        try:
            provider = self.providers[provider_id]

            if provider_id == "gemini":
                return await self._test_gemini(provider)
            elif provider_id == "groq":
                return await self._test_groq(provider)
            elif provider_id == "ollama":
                return await self._test_ollama(provider)
            elif provider_id == "openai":
                return await self._test_openai(provider)
            elif provider_id == "openrouter":
                return await self._test_openrouter(provider)

        except Exception as e:
            print(f"[llm_manager] Erro ao testar {provider_id}: {e}")
            return False

        return False

    async def _test_gemini(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Gemini"""
        key = self._get_next_key("gemini")
        if not key:
            return False

        url = f"{_sanitize_url_base(provider.get('base_url'))}/models"
        headers = {"x-goog-api-key": key}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def _test_groq(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Groq"""
        key = self._get_next_key("groq")
        if not key:
            return False

        url = (
            f"{_normalize_openai_compatible_base_url(provider.get('base_url'))}/models"
        )
        headers = {"Authorization": f"Bearer {key}"}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def _test_ollama(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Ollama"""
        url = f"{_normalize_ollama_url(provider.get('url'))}/api/tags"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.get(url) as response:
                return response.status == 200

    async def _test_openai(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com OpenAI"""
        url = (
            f"{_normalize_openai_compatible_base_url(provider.get('base_url'))}/models"
        )
        headers = {"Authorization": f"Bearer {_sanitize_api_key(provider.get('key'))}"}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def _test_openrouter(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com OpenRouter"""
        url = (
            f"{_normalize_openai_compatible_base_url(provider.get('base_url'))}/models"
        )
        headers = {
            "Authorization": f"Bearer {_sanitize_api_key(provider.get('key'))}",
        }
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def get_provider_status(self) -> Dict[str, Any]:
        """Obtém status de todos os providers (testes em paralelo)"""
        status = {}
        provider_ids = list(self.providers.keys())
        results = await asyncio.gather(
            *[self._test_provider(pid) for pid in provider_ids],
            return_exceptions=True,
        )

        for provider_id, result in zip(provider_ids, results):
            provider = self.providers[provider_id]
            status[provider_id] = {
                "name": provider["name"],
                "enabled": provider["enabled"],
                "model": provider.get("model", "unknown"),
                "online": bool(result) if isinstance(result, bool) else False,
                "keys_count": (
                    len(provider.get("keys", [])) if "keys" in provider else 1
                ),
            }

        return status

    def _summarize_sqlite_schema(self) -> str:
        try:
            from .db import get_db_path  # type: ignore
        except Exception:
            return ""
        try:
            db_path = str(get_db_path() or "").strip()
            if not db_path:
                return ""
            tables: List[Tuple[str, List[str]]] = []
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
                for (tname,) in rows:
                    cols = []
                    try:
                        info = conn.execute(f"PRAGMA table_info('{tname}')").fetchall()
                        for c in info:
                            cname = str(c[1] if len(c) > 1 else "")
                            ctype = str(c[2] if len(c) > 2 else "")
                            if cname:
                                cols.append(f"{cname}:{ctype}")
                    except Exception:
                        pass
                    tables.append((str(tname), cols))
            lines: List[str] = []
            for t, cols in itertools.islice(tables, 18):
                cols_part = ", ".join(cols[:8]) if cols else ""
                if cols_part:
                    lines.append(f"- {t}({cols_part}{'…' if len(cols) > 8 else ''})")
                else:
                    lines.append(f"- {t}")
            return "\n".join(lines).strip()
        except Exception:
            return ""

    def _summarize_project_tree(self) -> str:
        root = BASE_DIR
        max_dirs = 6
        max_files_per_dir = 6
        try:
            parts: List[str] = []
            for entry in sorted(root.iterdir()):
                if not entry.is_dir():
                    continue
                parts.append(f"/{entry.name}")
                files = []
                for child in sorted(entry.iterdir()):
                    if child.is_file():
                        files.append(child.name)
                    if len(files) >= max_files_per_dir:
                        break
                if files:
                    suffix = ", ".join(files[:max_files_per_dir])
                    parts.append(f"  - {suffix}")
                if len(parts) >= (max_dirs * 2):
                    break
            return "\n".join(parts).strip()
        except Exception:
            return ""

    def _build_full_prompt(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str],
        *,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        expert_prompt = (expert or {}).get("prompt") or ""
        base = expert_prompt.strip()
        ctx = (user_context or "").strip()
        expert_id = str((expert or {}).get("id") or "").strip().lower()
        if ctx and "SYS_GLOBAL" in ctx and "--- Instruções internas ---" in ctx:
            start = ctx.find("--- Instruções internas ---")
            end = ctx.find("--- Fim instruções ---", start)
            if start != -1 and end != -1:
                end = end + len("--- Fim instruções ---")
                internal_block = ctx[start:end].strip()
                ctx = f"{ctx[:start].strip()}\n\n{ctx[end:].strip()}".strip()
                base = f"{internal_block}\n\n{base}".strip()

        if expert_id in {"cto", "general"}:
            tree = self._summarize_project_tree()
            schema = self._summarize_sqlite_schema()
            tech_blocks: List[str] = []
            if tree:
                tech_blocks.append(f"Pastas/arquivos principais:\n{tree}")
            if schema:
                tech_blocks.append(f"Tabelas/colunas (SQLite):\n{schema}")
            if tech_blocks:
                detected = "\n\n".join(tech_blocks).strip()
                directive = (
                    "Você tem acesso ao código. Não pergunte ao usuário sobre a estrutura técnica; "
                    "deduza-a do seu contexto de arquivos."
                )
                ctx = f"{directive}\n\n{detected}\n\n{ctx}".strip()
        if expert_id == "general":
            base = (
                f"{base}\n\n"
                "Quando o pedido exigir execução imediata via software_operator (ex.: gerar um diagrama simples no Draw.io), "
                "limite a resposta visível ao usuário a uma única frase curta de confirmação e inclua o bloco ```plan``` "
                "com apenas uma tarefa software_operator suficiente para executar, sem pedir permissão. "
                "Use exatamente um bloco ```plan``` e uma linha no formato: Título | skill_id."
            ).strip()

        if expert_id == "cto":
            base = (
                f"{base}\n\n"
                "Não peça confirmação para etapas óbvias. Gere tarefas com comandos CLI concretos prontos para o software_operator. "
                "Se a ação for simples, minimize o plano e evite burocracia. "
                "Se o software necessário não estiver no inventário enviado, proponha instalar via 'winget' com flags de aceitação e em seguida execute a ação. "
                "Quando retornar um plano, use exatamente um bloco ```plan``` e linhas no formato: Título | skill_id."
            ).strip()

        if str((expert or {}).get("id") or "").strip().lower() == "software_operator":
            strict = (
                "ALGORITMO DE SELEÇÃO DE FERRAMENTA (obrigatório — execute nesta ordem):\n"
                "1. Leia a seção 'Softwares instalados disponíveis como ferramentas' no contexto.\n"
                "2. Se existe um software instalado adequado para a tarefa → gere o comando para ele.\n"
                "3. Se NÃO existe nenhum software adequado → use python-inline com um script Python.\n"
                "4. python-inline está SEMPRE disponível como ferramenta universal, mesmo sem contexto.\n"
                "5. NUNCA invente executáveis que não estejam na lista de instalados ou nas exceções abaixo.\n"
                "\n"
                "Executáveis sempre disponíveis (independente do inventário):\n"
                "- python-inline --action run --code \"<script>\" [--cwd <pasta>]\n"
                "- winget --action install --id <PACKAGE_ID> (Windows)\n"
                "- apt --action install <pacote> (Linux)\n"
                "- brew --action install <pacote> (macOS)\n"
                "\n"
                "Exemplos de uso do python-inline para tarefas comuns:\n"
                "  Screenshot:\n"
                "    python-inline --action run --code \"import mss,mss.tools; m=mss.mss(); p=m.shot(output='screen.png'); print('Capturado:',p)\"\n"
                "  Screenshot + retângulo vermelho:\n"
                "    python-inline --action run --code \"import mss; from PIL import Image,ImageDraw; m=mss.mss(); d=m.grab(m.monitors[0]); img=Image.frombytes('RGB',d.size,d.rgb); draw=ImageDraw.Draw(img); draw.rectangle([100,100,400,300],outline='red',width=3); img.save('result.png'); print('Salvo: result.png')\"\n"
                "  Redimensionar imagem:\n"
                "    python-inline --action run --code \"from PIL import Image; img=Image.open('<FILE>'); img.thumbnail((800,600)); img.save('<OUTPUT>')\"\n"
                "  Converter imagem:\n"
                "    python-inline --action run --code \"from PIL import Image; Image.open('<INPUT>').save('<OUTPUT>')\"\n"
                "\n"
                "Formato de saída obrigatório:\n"
                "- Retorne APENAS um único comando CLI em uma única linha.\n"
                "- Não use Markdown, crases, explicações, JSON, ou texto extra.\n"
                "- Inclua sempre: --action <acao> (exceto para python-inline que usa --action run).\n"
                "- Se faltar dado, use placeholders explícitos (ex.: <FILE>, <OUTPUT>, <TEXT>).\n"
                "- Mantenha --cwd consistente entre captura e edição quando a tarefa tiver múltiplos passos.\n"
                "- Se precisar instalar antes de usar, instale primeiro com winget/apt/brew.\n"
            )
            base = f"{base}\n\n{strict}".strip()
            if ctx:
                base = f"{base}\n\nContexto do sistema (lista de softwares, hardware, etc.):\n{ctx}".strip()
            if history:
                lines = []
                for m in history:
                    label = "Usuário" if m.get("role") == "user" else "Assistente"
                    lines.append(f"{label}: {m.get('content', '')}")
                hist_text = "\n\n".join(lines)
                base = f"{base}\n\n---\n{hist_text}\n---"
            return f"{base}\n\nPedido do usuário:\n{prompt}\n\nComando:".strip()
        calibration_rules = (
            "Regras de resposta:\n"
            "- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.\n"
            "- Seja direto e útil; seja curto por padrão.\n"
            "- Não repita nem cite o perfil/SOUL; use apenas para ajustar tom e exemplos.\n"
            '- Não faça longas apresentações quando a mensagem for curta (ex.: "teste").\n'
            '- Se a pergunta for genérica (ex.: "o que você pode fazer?"), responda com:\n'
            "  1) Uma frase curta de enquadramento (Open Slap local).\n"
            "  2) Uma lista de 5–7 itens de capacidades (ex.: responder dúvidas, planejar, escrever/alterar código, criar/editar arquivos, depurar erros, integrar APIs/LLMs, organizar passos).\n"
            "  3) Uma lista curta de limites (2–4 itens) sem dramatizar (ex.: não tem acesso a contas/infra sem credenciais; não executa deploy fora do seu controle; não vê segredos; acesso ao sistema é via servidor local).\n"
            '- Use o contexto recente da conversa quando houver follow-up curto (ex.: "e em 2025?").\n'
            "- Você responde via o Open Slap (servidor local) neste computador; o modelo pode ser remoto ou local, mas a execução do app e as permissões (arquivos/SQLite) são do servidor local.\n"
            '- Você não executa ping ICMP. Se o usuário pedir "ping", ofereça teste de conectividade via HTTP/TCP (ex.: abrir um URL/porta) e peça o host/URL exato.\n'
            "- Se não tiver certeza sobre um fato atual, diga que pode estar desatualizado e peça para usar/buscar contexto da web.\n"
            "- Você pode criar/editar arquivos localmente neste computador.\n"
            "- Se o usuário pedir para criar/salvar arquivos em uma pasta local, responda com:\n"
            "  1) Uma frase curta confirmando o que foi gerado.\n"
            "  2) Um bloco <FILES_JSON>...</FILES_JSON> contendo JSON válido no formato:\n"
            '     {"base_path":"C:\\\\caminho\\\\da\\\\pasta","files":[{"path":"index.html","content":"..."},...]}\n'
            '- No bloco <FILES_JSON>, use somente paths relativos em "files[].path".\n'
            "- Não inclua crases, Markdown code fences ou texto extra dentro de <FILES_JSON>.\n"
            "- Se o usuário não informar um caminho, use a pasta destino que será fornecida na mensagem.\n"
            "- Se você precisar sugerir execução de comando no Windows, use um bloco <COMMAND_JSON>...</COMMAND_JSON> com JSON válido no formato:\n"
            '     {"title":"(curto)","intent":"(por quê)","command":"(powershell/cmd)","cwd":"C:\\\\pasta\\\\opcional"}\n'
            "- No bloco <COMMAND_JSON>, não use crases nem Markdown e não inclua texto extra.\n"
        )
        base = f"{base}\n\n{calibration_rules}".strip()
        if ctx:
            base = f"{base}\n\nContexto do usuário (SOUL, uso interno):\n{ctx}".strip()
        if history:
            lines = []
            for m in history:
                label = "Usuário" if m.get("role") == "user" else "Assistente"
                lines.append(f"{label}: {m.get('content', '')}")
            hist_text = "\n\n".join(lines)
            base = f"{base}\n\n---\n{hist_text}\n---"
        return f"{base}\n\nPergunta: {prompt}\n\nResposta:".strip()

    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        llm_override: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Gera resposta com streaming usando fallback automático"""
        override = llm_override or {}
        history: Optional[List[Dict[str, str]]] = None
        if conversation_id is not None:
            try:
                history = load_conversation_history(conversation_id)
            except Exception as exc:
                print(f"[llm_manager] Erro ao carregar histórico: {exc}")
                history = None
        override_mode = str(override.get("mode") or "").strip().lower()
        preferred_provider = str(override.get("provider") or "").strip().lower() or None
        api_key_override = _sanitize_api_key(override.get("api_key")) or None

        model_override = _sanitize_text(override.get("model")) or None
        base_url_override = _sanitize_url_base(override.get("base_url")) or None
        errors: List[str] = []
        attempted_preferred = False

        if preferred_provider and override_mode in {"api", "local"}:
            provider = dict(self.providers.get(preferred_provider) or {})
            if preferred_provider == "ollama":
                provider.setdefault(
                    "url", os.getenv("OLLAMA_URL", "http://localhost:11434")
                )
                provider.setdefault("model", os.getenv("OLLAMA_MODEL", "llama3.2"))
                provider["url"] = _normalize_ollama_url(
                    base_url_override or provider.get("url")
                )
                provider["model"] = model_override or provider.get("model")
            elif preferred_provider == "openai":
                provider.setdefault(
                    "base_url",
                    os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                )
                provider.setdefault("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
                provider["base_url"] = _normalize_openai_compatible_base_url(
                    base_url_override or provider.get("base_url")
                )
                provider["model"] = model_override or provider.get("model")
                provider["key"] = (
                    api_key_override or _sanitize_api_key(provider.get("key")) or ""
                )
            elif preferred_provider == "groq":
                provider.setdefault("base_url", "https://api.groq.com/openai/v1")
                provider.setdefault(
                    "model", os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
                )
                provider["base_url"] = _normalize_openai_compatible_base_url(
                    base_url_override or provider.get("base_url")
                )
                provider["model"] = model_override or provider.get("model")
                if api_key_override:
                    provider["keys"] = [api_key_override]
                    provider["current_key_index"] = 0
            elif preferred_provider == "gemini":
                provider.setdefault(
                    "base_url", "https://generativelanguage.googleapis.com/v1"
                )
                provider.setdefault(
                    "model", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                )
                provider["base_url"] = _sanitize_url_base(
                    base_url_override or provider.get("base_url")
                )
                provider["model"] = model_override or provider.get("model")
                bu = (
                    str(provider.get("base_url") or "")
                    .strip()
                    .strip("`\"' ,")
                    .rstrip("/")
                )
                if bu.endswith("/v1beta") and "generativelanguage.googleapis.com" in bu:
                    bu = bu[:-6] + "v1"
                if bu:
                    provider["base_url"] = bu
                if api_key_override:
                    provider["keys"] = [api_key_override]
                    provider["current_key_index"] = 0

            elif preferred_provider == "openrouter":
                provider.setdefault(
                    "base_url", os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
                )
                provider.setdefault(
                    "model", os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
                )
                provider["base_url"] = _normalize_openai_compatible_base_url(
                    base_url_override or provider.get("base_url")
                )
                provider["model"] = model_override or provider.get("model")
                provider["key"] = api_key_override or _sanitize_api_key(provider.get("key") or "")
                if not provider.get("models"):
                    provider["models"] = [provider["model"]]

            try:
                if preferred_provider == "gemini":
                    agen = self._stream_gemini(
                        prompt,
                        expert,
                        provider,
                        user_context=user_context,
                        api_key_override=api_key_override,
                        history=history,
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": preferred_provider,
                        "model": provider.get("model") or "unknown",
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                if preferred_provider == "groq":
                    agen = self._stream_groq(
                        prompt,
                        expert,
                        provider,
                        user_context=user_context,
                        api_key_override=api_key_override,
                        history=history,
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": preferred_provider,
                        "model": provider.get("model") or "unknown",
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                if preferred_provider == "ollama":
                    agen = self._stream_ollama(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": preferred_provider,
                        "model": provider.get("model") or "unknown",
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                if preferred_provider == "openai":
                    agen = self._stream_openai(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": preferred_provider,
                        "model": provider.get("model") or "unknown",
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                if preferred_provider == "openrouter":
                    agen = self._stream_openrouter_fallback(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": preferred_provider,
                        "model": provider.get("model") or "unknown",
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
            except Exception as e:
                msg = str(e) or repr(e)
                errors.append(f"{preferred_provider}: {msg}")
                print(f"[llm_manager] Erro no provider {preferred_provider}: {e}")
            finally:
                attempted_preferred = True

        for provider_id in self.provider_order:
            if (
                attempted_preferred
                and preferred_provider
                and provider_id == preferred_provider
            ):
                continue
            if provider_id not in self.providers:
                continue

            provider = self.providers[provider_id]
            if not provider["enabled"]:
                continue

            try:
                print(f"[llm_manager] Tentando provider: {provider_id}")

                if provider_id == "gemini":
                    agen = self._stream_gemini(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": provider_id,
                        "model": provider.get("model", "unknown"),
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                elif provider_id == "groq":
                    agen = self._stream_groq(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": provider_id,
                        "model": provider.get("model", "unknown"),
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                elif provider_id == "ollama":
                    agen = self._stream_ollama(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": provider_id,
                        "model": provider.get("model", "unknown"),
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                elif provider_id == "openrouter":
                    agen = self._stream_openrouter_fallback(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": provider_id,
                        "model": provider.get("model", "unknown"),
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return
                elif provider_id == "openai":
                    agen = self._stream_openai(
                        prompt, expert, provider, user_context=user_context, history=history
                    )
                    first = await agen.__anext__()
                    yield {
                        "provider": provider_id,
                        "model": provider.get("model", "unknown"),
                        "tokens": None,
                    }
                    yield first
                    async for chunk in agen:
                        yield chunk
                    return

            except Exception as e:
                msg = str(e) or repr(e)
                errors.append(f"{provider_id}: {msg}")
                print(f"[llm_manager] Erro no provider {provider_id}: {e}")
                continue

        # Se todos falharem, retornar mensagem de erro
        if errors:
            details = " | ".join(errors[-4:])
            yield f"❌ Todos os providers estão indisponíveis. Verifique suas configurações de API.\nDetalhes: {details}"
        else:
            yield "❌ Todos os providers estão indisponíveis. Verifique suas configurações de API."

    async def _stream_gemini(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        api_key_override: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming com Gemini com rotação de chave em 429"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context, history=history)

        keys_to_try: List[str] = []
        if api_key_override:
            keys_to_try = [api_key_override]
        else:
            num_keys = len(provider.get("keys") or [])
            for _ in range(num_keys if num_keys > 0 else 1):
                k = self._get_next_key("gemini")
                if k:
                    keys_to_try.append(k)
        keys_to_try = [k for k in keys_to_try if k]
        if not keys_to_try:
            raise Exception("Sem chaves Gemini disponíveis")

        def normalize_model_name(value: str) -> str:
            v = str(value or "").strip()
            v = v.strip("`\"' ,")
            if v.startswith("models/"):
                v = v.split("/", 1)[1]
            return v

        def normalize_base_url(value: str) -> str:
            v = str(value or "").strip()
            v = v.strip("`\"' ,").rstrip("/")
            if v.endswith("/v1beta"):
                return v
            if v.endswith("/v1"):
                return v
            return v

        def alternate_base_urls(value: str) -> List[str]:
            v = normalize_base_url(value)
            if v.endswith("/v1beta"):
                return [v[:-6] + "v1", v]
            if v.endswith("/v1"):
                return [v, v[:-2] + "v1beta"]
            return [v]

        async def list_models(base_url: str, key: str) -> List[Dict[str, Any]]:
            base_url = normalize_base_url(base_url)
            cache_key = f"{base_url}|{key[-8:]}"
            if cache_key in self._gemini_models_cache:
                return self._gemini_models_cache[cache_key]
            url = f"{base_url}/models"
            headers = {"x-goog-api-key": key}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        self._gemini_models_cache[cache_key] = []
                        return []
                    data = await response.json()
                    models = data.get("models") or []
                    if not isinstance(models, list):
                        models = []
                    self._gemini_models_cache[cache_key] = models
                    return models

        async def pick_model(base_url: str, key: str) -> Optional[str]:
            cache_key = f"{normalize_base_url(base_url)}|{key[-8:]}"
            if cache_key in self._gemini_model_pick_cache:
                return self._gemini_model_pick_cache[cache_key]
            models = await list_models(base_url, key)
            best = None
            for m in models:
                name = normalize_model_name(m.get("name") or "")
                methods = m.get("supportedGenerationMethods") or []
                if not name:
                    continue
                if isinstance(methods, list) and (
                    "streamGenerateContent" in methods or "generateContent" in methods
                ):
                    best = name
                    if "flash" in name:
                        break
            if best:
                self._gemini_model_pick_cache[cache_key] = best
            return best

        def emit_from_obj(obj: Any) -> List[str]:
            out: List[str] = []
            if not isinstance(obj, dict):
                return out
            candidates = obj.get("candidates") or []
            for cand in candidates:
                parts = ((cand or {}).get("content") or {}).get("parts") or []
                for p in parts:
                    t = str((p or {}).get("text") or "")
                    if t:
                        out.append(t)
            return out

        async def post_and_parse(base_url: str, model: str, key: str) -> List[str]:
            base_url = normalize_base_url(base_url)
            model = normalize_model_name(model)
            url = f"{base_url}/models/{model}:streamGenerateContent"
            headers = {"Content-Type": "application/json", "x-goog-api-key": key}
            data = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    body = await response.text()
                    body_str = (body or "").strip()
                    if _is_rate_limited(response.status, body_str):
                        await _wait_retry_after(response, body=body_str)
                        raise RateLimitError(
                            f"Gemini rate limit (key={key[-8:]}): {response.status}"
                        )
                    if response.status != 200:
                        clipped = body_str
                        if len(clipped) > 600:
                            clipped = clipped[:600] + "..."
                        raise Exception(
                            f"Gemini API error (base_url={base_url}, model={model}): {response.status}{f' - {clipped}' if clipped else ''}"
                        )

            if not body_str:
                raise Exception("Gemini: resposta vazia")

            chunks: List[str] = []
            try:
                parsed = json.loads(body_str)
                if isinstance(parsed, list):
                    for item in parsed:
                        chunks.extend(emit_from_obj(item))
                else:
                    chunks.extend(emit_from_obj(parsed))
            except json.JSONDecodeError:
                for line in body_str.splitlines():
                    s = line.strip()
                    if not s:
                        continue
                    if s.startswith("data:"):
                        s = s[5:].strip()
                    if not s or s == "[DONE]":
                        continue
                    try:
                        obj = json.loads(s)
                    except json.JSONDecodeError:
                        continue
                    chunks.extend(emit_from_obj(obj))

            chunks = [c for c in chunks if str(c).strip()]
            if not chunks:
                raise Exception("Gemini: não foi possível extrair texto da resposta")
            return chunks

        base_url = (
            provider.get("base_url") or "https://generativelanguage.googleapis.com/v1"
        )
        model = provider.get("model") or "gemini-2.5-flash"

        last_err: Optional[Exception] = None
        for key in keys_to_try:
            for base in alternate_base_urls(base_url):
                try:
                    chunks = await post_and_parse(base, model, key)
                    for c in chunks:
                        yield c
                    return
                except RateLimitError:
                    last_err = RateLimitError(
                        f"Gemini: todas as chaves excederam rate limit ({len(keys_to_try)} chaves testadas)"
                    )
                    break
                except Exception as e:
                    last_err = e
                    msg = str(e) or repr(e)
                    lowered = msg.lower()
                    if "models/" in lowered and "not found for api version" in lowered:
                        picked = await pick_model(base, key)
                        if picked and normalize_model_name(picked) != normalize_model_name(model):
                            try:
                                chunks = await post_and_parse(base, picked, key)
                                provider["model"] = picked
                                for c in chunks:
                                    yield c
                                return
                            except RateLimitError:
                                last_err = RateLimitError(
                                    f"Gemini: todas as chaves excederam rate limit ({len(keys_to_try)} chaves testadas)"
                                )
                                break
                            except Exception as ee:
                                last_err = ee
                        continue
                    if "404" in msg:
                        picked = await pick_model(base, key)
                        if picked and normalize_model_name(picked) != normalize_model_name(model):
                            try:
                                chunks = await post_and_parse(base, picked, key)
                                provider["model"] = picked
                                for c in chunks:
                                    yield c
                                return
                            except RateLimitError:
                                last_err = RateLimitError(
                                    f"Gemini: todas as chaves excederam rate limit ({len(keys_to_try)} chaves testadas)"
                                )
                                break
                            except Exception as ee:
                                last_err = ee
                                continue
                        break
                    # Para outros erros (não-429), tenta próxima base_url
                    continue

        raise last_err or Exception("Gemini: falha desconhecida")

    async def _stream_groq(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        api_key_override: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming com Groq"""
        keys_to_try: List[str] = []
        override_key = _sanitize_api_key(api_key_override) if api_key_override else ""
        if override_key:
            keys_to_try = [override_key]
        else:
            keys = provider.get("keys") or []
            for _ in range(len(keys) if keys else 1):
                k = self._get_next_key("groq")
                if k:
                    keys_to_try.append(k)

        keys_to_try = [k for k in keys_to_try if k]
        if not keys_to_try:
            raise Exception("Sem chaves Groq disponíveis")

        full_prompt = self._build_full_prompt(prompt, expert, user_context, history=history)

        base_url = _normalize_openai_compatible_base_url(provider.get("base_url"))
        model = _sanitize_text(provider.get("model"))
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        timeout = aiohttp.ClientTimeout(total=60)
        last_err: Optional[Exception] = None
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async def pick_model_for_key(key: str) -> Optional[str]:
                try:
                    models_url = f"{base_url}/models"
                    h = {"Authorization": f"Bearer {key}"}
                    async with session.get(models_url, headers=h) as r:
                        if r.status != 200:
                            return None
                        payload = await r.json()
                except Exception:
                    return None

                data_list = None
                if isinstance(payload, dict):
                    data_list = payload.get("data")
                if not isinstance(data_list, list):
                    return None
                ids: List[str] = []
                for item in data_list:
                    if isinstance(item, dict):
                        mid = item.get("id")
                        if isinstance(mid, str) and mid.strip():
                            ids.append(mid.strip())
                if not ids:
                    return None

                def norm(v: str) -> str:
                    return str(v or "").strip().strip("`\"' ,").lower()

                def score(mid: str) -> int:
                    m = mid.lower()
                    s = 0
                    if "llama" in m:
                        s += 50
                    if "versatile" in m:
                        s += 20
                    if "70b" in m:
                        s += 10
                    if "instant" in m:
                        s += 5
                    if "preview" in m or "beta" in m:
                        s -= 5
                    return s

                ids_sorted = sorted(ids, key=score, reverse=True)
                picked = ids_sorted[0] if ids_sorted else None
                if picked and norm(picked) != norm(model):
                    return picked
                for alt in ids_sorted[1:]:
                    if norm(alt) != norm(model):
                        return alt
                return None

            for key in keys_to_try:
                headers["Authorization"] = f"Bearer {key}"
                async with session.post(url, headers=headers, json=data) as response:
                    body = ""
                    try:
                        body = (await response.text()) or ""
                    except Exception:
                        body = ""
                    body = body.strip()
                    if _is_rate_limited(response.status, body):
                        await _wait_retry_after(response, body=body)
                        if len(keys_to_try) > 1:
                            print(f"[llm_manager] Groq rate limit (key={key[-8:]}), tentando próxima chave")
                            continue
                        raise RateLimitError(
                            f"Groq rate limit (key={key[-8:]}): {response.status}"
                        )
                    if response.status != 200:
                        if len(body) > 800:
                            body = body[:800] + "..."
                        lowered = body.lower()
                        if (
                            response.status == 400
                            and ("decommissioned" in lowered or "model_decommissioned" in lowered)
                        ):
                            picked = await pick_model_for_key(key)
                            if picked:
                                data["model"] = picked
                                async with session.post(url, headers=headers, json=data) as r2:
                                    if r2.status == 200:
                                        provider["model"] = picked
                                        async for line in r2.content:
                                            line = line.decode("utf-8").strip()
                                            if line.startswith("data: ") and not line.endswith("[DONE]"):
                                                try:
                                                    data_evt = json.loads(line[6:])
                                                    if "choices" in data_evt and data_evt["choices"]:
                                                        content = data_evt["choices"][0]["delta"].get(
                                                            "content", ""
                                                        )
                                                        if content:
                                                            yield content
                                                except json.JSONDecodeError:
                                                    continue
                                        return
                                    try:
                                        body2 = (await r2.text()) or ""
                                    except Exception:
                                        body2 = ""
                                    body2 = body2.strip()
                                    if len(body2) > 800:
                                        body2 = body2[:800] + "..."
                                    last_err = Exception(
                                        f"Groq API error (base_url={base_url}, model={picked}): "
                                        f"{r2.status}{f' - {body2}' if body2 else ''}"
                                    )
                                    continue
                        err = Exception(
                            f"Groq API error (base_url={base_url}, model={model}): "
                            f"{response.status}{f' - {body}' if body else ''}"
                        )
                        last_err = err
                        if (
                            response.status == 401
                            and not override_key
                            and len(keys_to_try) > 1
                        ):
                            continue
                        raise err

                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            try:
                                data = json.loads(line[6:])
                                if "choices" in data and data["choices"]:
                                    content = data["choices"][0]["delta"].get(
                                        "content", ""
                                    )
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                    return

        raise last_err or Exception("Groq: falha desconhecida")

    async def _stream_ollama(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming com Ollama"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context, history=history)

        base_url = _normalize_ollama_url(provider.get("url"))
        model = _sanitize_text(provider.get("model"))
        url_generate = f"{base_url}/api/generate"
        data_generate = {"model": model, "prompt": full_prompt, "stream": True}

        async def pick_installed_model() -> Optional[str]:
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
                ) as s:
                    async with s.get(f"{base_url}/api/tags") as r:
                        if r.status != 200:
                            return None
                        payload = await r.json()
                models = payload.get("models") if isinstance(payload, dict) else None
                if not isinstance(models, list) or not models:
                    return None
                for it in models:
                    if isinstance(it, dict):
                        name = str(it.get("name") or "").strip()
                        if name:
                            return name
                return None
            except Exception:
                return None

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.post(url_generate, json=data_generate) as response:
                if response.status == 404:
                    body0 = ""
                    try:
                        body0 = (await response.text()) or ""
                    except Exception:
                        body0 = ""
                    lowered0 = body0.lower()
                    if "model" in lowered0 and "not found" in lowered0:
                        picked = await pick_installed_model()
                        if picked and _sanitize_text(picked) and _sanitize_text(picked) != model:
                            model = _sanitize_text(picked)
                            data_generate["model"] = model
                            async with session.post(
                                url_generate, json=data_generate
                            ) as r0:
                                if r0.status == 200:
                                    provider["model"] = model
                                    async for line in r0.content:
                                        try:
                                            data0 = json.loads(line.decode("utf-8"))
                                            if "response" in data0:
                                                yield data0["response"]
                                        except json.JSONDecodeError:
                                            continue
                                    return

                    url_chat = f"{base_url}/api/chat"
                    data_chat = {
                        "model": model,
                        "messages": [{"role": "user", "content": full_prompt}],
                        "stream": True,
                    }
                    async with session.post(url_chat, json=data_chat) as r2:
                        if r2.status != 200:
                            body = ""
                            try:
                                body = (await r2.text()) or ""
                            except Exception:
                                body = ""
                            body = body.strip()
                            if len(body) > 600:
                                body = body[:600] + "..."
                            lowered = body.lower()
                            if (
                                r2.status == 404
                                and "model" in lowered
                                and "not found" in lowered
                            ):
                                picked = await pick_installed_model()
                                if picked and _sanitize_text(picked) and _sanitize_text(picked) != model:
                                    model = _sanitize_text(picked)
                                    data_chat["model"] = model
                                    async with session.post(
                                        url_chat, json=data_chat
                                    ) as r3:
                                        if r3.status == 200:
                                            provider["model"] = model
                                            async for line in r3.content:
                                                try:
                                                    obj = json.loads(line.decode("utf-8"))
                                                    content = ((obj or {}).get("message") or {}).get(
                                                        "content"
                                                    ) or ""
                                                    if content:
                                                        yield content
                                                except json.JSONDecodeError:
                                                    continue
                                            return
                            raise Exception(
                                f"Ollama API error (url={base_url}, model={model}): {r2.status}{f' - {body}' if body else ''}"
                            )
                        async for line in r2.content:
                            try:
                                obj = json.loads(line.decode("utf-8"))
                                content = ((obj or {}).get("message") or {}).get(
                                    "content"
                                ) or ""
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                    return

                if response.status != 200:
                    body = ""
                    try:
                        body = (await response.text()) or ""
                    except Exception:
                        body = ""
                    body = body.strip()
                    if len(body) > 600:
                        body = body[:600] + "..."
                    lowered = body.lower()
                    if (
                        response.status == 404
                        and "model" in lowered
                        and "not found" in lowered
                    ):
                        picked = await pick_installed_model()
                        if picked and _sanitize_text(picked) and _sanitize_text(picked) != model:
                            model = _sanitize_text(picked)
                            data_generate["model"] = model
                            async with session.post(
                                url_generate, json=data_generate
                            ) as r4:
                                if r4.status == 200:
                                    provider["model"] = model
                                    async for line in r4.content:
                                        try:
                                            data4 = json.loads(line.decode("utf-8"))
                                            if "response" in data4:
                                                yield data4["response"]
                                        except json.JSONDecodeError:
                                            continue
                                    return
                    raise Exception(
                        f"Ollama API error (url={base_url}, model={model}): {response.status}{f' - {body}' if body else ''}"
                    )

                async for line in response.content:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue

    async def _stream_openai(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming com OpenAI"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context, history=history)

        url = f"{provider['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}",
        }

        data = {
            "model": provider["model"],
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    err_body = await response.text()
                    if _is_rate_limited(response.status, err_body):
                        await _wait_retry_after(response, body=err_body)
                        raise RateLimitError(f"OpenAI rate limit: {response.status}")
                    raise Exception(f"OpenAI API error: {response.status}")

                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and data["choices"]:
                                content = data["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def _stream_openrouter(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        model_name: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming com OpenRouter (OpenAI-compatible) — modelo específico"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context, history=history)
        model = model_name or provider.get("model", "nvidia/nemotron-3-nano-30b-a3b:free")

        url = f"{provider['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}",
            "X-Title": "OpenSlap Local",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        ) as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 401:
                    raise Exception(f"OpenRouter: chave inválida")
                if response.status != 200:
                    err_body = (await response.read()).decode("utf-8", errors="replace")
                    if _is_rate_limited(response.status, err_body):
                        await _wait_retry_after(response, body=err_body)
                        raise RateLimitError(f"OpenRouter ({model}): rate limit - {response.status}")
                    clipped = err_body[:200] if len(err_body) > 200 else err_body
                    raise Exception(f"OpenRouter ({model}): status {response.status} - {clipped}")

                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and data["choices"]:
                                content = data["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def _stream_openrouter_fallback(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Tenta múltiplos modelos OpenRouter; falha apenas se todos rejeitarem."""
        models = provider.get("models", [provider.get("model", "")])
        if not models:
            models = [provider.get("model", "nvidia/nemotron-3-nano-30b-a3b:free")]

        last_error: Optional[str] = None
        for model in models:
            if not model:
                continue
            try:
                agen = self._stream_openrouter(
                    prompt, expert, provider,
                    user_context=user_context, model_name=model,
                    history=history,
                )
                first = await agen.__anext__()
                yield first
                async for chunk in agen:
                    yield chunk
                return
            except Exception as e:
                last_error = str(e)
                model_debug = model.split("/")[-1] if "/" in model else model
                print(f"[llm_manager] OpenRouter model '{model_debug}' falhou: {last_error}")

        raise Exception(f"OpenRouter: todos os modelos falharam. Último erro: {last_error}")

    async def get_active_provider(
        self, preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retorna qual provider seria selecionado agora, sem fazer chamada LLM real.
        Simula a lógica de stream_generate() apenas com estado local + env."""
        result: Dict[str, Any] = {
            "provider": None,
            "model": None,
            "has_key": False,
            "fallback": False,
            "inferred_from": "none",
        }

        if preferred_provider:
            prov = self.providers.get(preferred_provider)
            if prov and prov.get("enabled"):
                keys = prov.get("keys", [])
                valid = [k for k in keys if _sanitize_api_key(k)]
                if valid:
                    result["provider"] = preferred_provider
                    result["model"] = prov.get("model")
                    result["has_key"] = True
                    result["fallback"] = False
                    result["inferred_from"] = "user_settings"
                    return result

        for provider_id in self.provider_order:
            if provider_id not in self.providers:
                continue
            prov = self.providers[provider_id]
            if not prov.get("enabled"):
                continue
            keys = prov.get("keys", [])
            valid = [k for k in keys if _sanitize_api_key(k)]
            if valid:
                result["provider"] = provider_id
                result["model"] = prov.get("model")
                result["has_key"] = True
                result["fallback"] = bool(preferred_provider)
                result["inferred_from"] = "env"
                return result

        first = self.provider_order[0] if self.provider_order else "gemini"
        result["provider"] = first
        fallback_prov = self.providers.get(first)
        result["model"] = fallback_prov.get("model") if fallback_prov else None
        result["has_key"] = False
        result["fallback"] = bool(preferred_provider)
        result["inferred_from"] = "env"
        return result


# Instância global
llm_manager = LLMManager()


# Funções auxiliares
async def get_provider_status() -> Dict[str, Any]:
    """Obtém status dos providers"""
    return await llm_manager.get_provider_status()


async def stream_generate(
    prompt: str, expert: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Gera resposta com streaming"""
    async for chunk in llm_manager.stream_generate(prompt, expert):
        yield chunk
