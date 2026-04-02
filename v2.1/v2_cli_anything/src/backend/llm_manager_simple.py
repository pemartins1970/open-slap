"""
🤖 LLM MANAGER SIMPLES - Versão sem dependências externas
Gerenciamento de providers LLM (Gemini, Groq, Ollama)
"""

import os
import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple
import aiohttp
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
import itertools

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

HTTP_TIMEOUT_S = float(str(os.getenv("OPENSLAP_HTTP_TIMEOUT_S") or "6").strip() or "6")


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
                "model": _sanitize_text(os.getenv("GEMINI_MODEL", "gemini-1.5-flash")),
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
            providers["openrouter"] = {
                "name": "OpenRouter",
                "key": openrouter_key,
                "model": _sanitize_text(
                    os.getenv(
                        "OPENROUTER_MODEL",
                        "nvidia/nemotron-3-nano-30b-a3b:free",
                    )
                ),
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
        """Obtém status de todos os providers"""
        status = {}

        for provider_id in self.providers:
            provider = self.providers[provider_id]

            status[provider_id] = {
                "name": provider["name"],
                "enabled": provider["enabled"],
                "model": provider.get("model", "unknown"),
                "online": await self._test_provider(provider_id),
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
        self, prompt: str, expert: Dict[str, Any], user_context: Optional[str]
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
            return f"{base}\n\nPedido do usuário:\n{prompt}\n\nComando:".strip()
        calibration_rules = (
            "Regras de resposta:\n"
            "- Responda em português.\n"
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
        return f"{base}\n\nPergunta: {prompt}\n\nResposta:".strip()

    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        llm_override: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Gera resposta com streaming usando fallback automático"""
        override = llm_override or {}
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
            elif preferred_provider == "gemini":
                provider.setdefault(
                    "base_url", "https://generativelanguage.googleapis.com/v1"
                )
                provider.setdefault(
                    "model", os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
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

            try:
                if preferred_provider == "gemini":
                    agen = self._stream_gemini(
                        prompt,
                        expert,
                        provider,
                        user_context=user_context,
                        api_key_override=api_key_override,
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
                        prompt, expert, provider, user_context=user_context
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
                        prompt, expert, provider, user_context=user_context
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
                    agen = self._stream_openrouter(
                        prompt, expert, provider, user_context=user_context
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
                        prompt, expert, provider, user_context=user_context
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
                        prompt, expert, provider, user_context=user_context
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
                        prompt, expert, provider, user_context=user_context
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
                    agen = self._stream_openrouter(
                        prompt, expert, provider, user_context=user_context
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
                        prompt, expert, provider, user_context=user_context
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
    ) -> AsyncGenerator[str, None]:
        """Streaming com Gemini"""
        key = api_key_override or self._get_next_key("gemini")
        if not key:
            raise Exception("Sem chaves Gemini disponíveis")

        full_prompt = self._build_full_prompt(prompt, expert, user_context)

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

        async def list_models(base_url: str) -> List[Dict[str, Any]]:
            base_url = normalize_base_url(base_url)
            if base_url in self._gemini_models_cache:
                return self._gemini_models_cache[base_url]
            url = f"{base_url}/models"
            headers = {"x-goog-api-key": key}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        self._gemini_models_cache[base_url] = []
                        return []
                    data = await response.json()
                    models = data.get("models") or []
                    if not isinstance(models, list):
                        models = []
                    self._gemini_models_cache[base_url] = models
                    return models

        async def pick_model(base_url: str) -> Optional[str]:
            cache_key = f"{normalize_base_url(base_url)}"
            if cache_key in self._gemini_model_pick_cache:
                return self._gemini_model_pick_cache[cache_key]
            models = await list_models(base_url)
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

        async def post_and_parse(base_url: str, model: str) -> List[str]:
            base_url = normalize_base_url(base_url)
            model = normalize_model_name(model)
            url = f"{base_url}/models/{model}:streamGenerateContent"
            headers = {"Content-Type": "application/json", "x-goog-api-key": key}
            data = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    body = await response.text()
                    body_str = (body or "").strip()
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
        model = provider.get("model") or "gemini-1.5-flash"

        last_err: Optional[Exception] = None
        for base in alternate_base_urls(base_url):
            try:
                chunks = await post_and_parse(base, model)
                for c in chunks:
                    yield c
                return
            except Exception as e:
                last_err = e
                msg = str(e) or repr(e)
                lowered = msg.lower()
                if "models/" in lowered and "not found for api version" in lowered:
                    picked = await pick_model(base)
                    if picked and normalize_model_name(picked) != normalize_model_name(
                        model
                    ):
                        try:
                            chunks = await post_and_parse(base, picked)
                            provider["model"] = picked
                            for c in chunks:
                                yield c
                            return
                        except Exception as ee:
                            last_err = ee
                    continue
                if "404" in msg:
                    picked = await pick_model(base)
                    if picked and normalize_model_name(picked) != normalize_model_name(
                        model
                    ):
                        try:
                            chunks = await post_and_parse(base, picked)
                            provider["model"] = picked
                            for c in chunks:
                                yield c
                            return
                        except Exception as ee:
                            last_err = ee
                            continue
                break

        raise last_err or Exception("Gemini: falha desconhecida")

    async def _stream_groq(
        self,
        prompt: str,
        expert: Dict[str, Any],
        provider: Dict[str, Any],
        *,
        user_context: Optional[str] = None,
        api_key_override: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming com Groq"""
        keys_to_try: List[str] = []
        override_key = _sanitize_api_key(api_key_override) if api_key_override else ""
        if override_key:
            keys_to_try = [override_key]
        else:
            keys = provider.get("keys") or []
            tries = 1 if not isinstance(keys, list) else max(1, min(2, len(keys)))
            for _ in range(tries):
                k = self._get_next_key("groq")
                if k:
                    keys_to_try.append(k)
        keys_to_try = [k for k in keys_to_try if k]
        if not keys_to_try:
            raise Exception("Sem chaves Groq disponíveis")

        full_prompt = self._build_full_prompt(prompt, expert, user_context)

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
                    if response.status != 200:
                        body = ""
                        try:
                            body = (await response.text()) or ""
                        except Exception:
                            body = ""
                        body = body.strip()
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
    ) -> AsyncGenerator[str, None]:
        """Streaming com Ollama"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context)

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

        async with aiohttp.ClientSession() as session:
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
    ) -> AsyncGenerator[str, None]:
        """Streaming com OpenAI"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context)

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
    ) -> AsyncGenerator[str, None]:
        """Streaming com OpenRouter (OpenAI-compatible)"""
        full_prompt = self._build_full_prompt(prompt, expert, user_context)

        url = f"{provider['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}",
            "X-Title": "OpenSlap Local",
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
                    raise Exception(f"OpenRouter API error: {response.status}")

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
