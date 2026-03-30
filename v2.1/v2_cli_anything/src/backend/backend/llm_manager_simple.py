"""
🤖 LLM MANAGER SIMPLES - Versão sem dependências externas
Gerenciamento de providers LLM (Gemini, Groq, Ollama)
"""

import os
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

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

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
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

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def _test_ollama(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Ollama"""
        url = f"{_normalize_ollama_url(provider.get('url'))}/api/tags"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
            async with session.get(url) as response:
                return response.status == 200

    async def _test_openai(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com OpenAI"""
        url = (
            f"{_normalize_openai_compatible_base_url(provider.get('base_url'))}/models"
        )
        headers = {"Authorization": f"Bearer {_sanitize_api_key(provider.get('key'))}"}

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
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
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
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

    def _build_full_prompt(
        self, prompt: str, expert: Dict[str, Any], user_context: Optional[str]
    ) -> str:
        expert_prompt = (expert or {}).get("prompt") or ""
        base = expert_prompt.strip()
        ctx = (user_context or "").strip()
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

        async with aiohttp.ClientSession() as session:
            async with session.post(url_generate, json=data_generate) as response:
                if response.status == 404:
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

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
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

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)) as session:
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
