"""
Clientes LLM para diferentes providers
"""

import json
import aiohttp
from typing import Dict, Any, List, Optional, AsyncGenerator

from .utils import (
    normalize_model_name,
    normalize_gemini_base_url,
    alternate_gemini_base_urls,
)
from .providers import ProviderConfig


class LLMClient:
    """Base class para clientes LLM"""
    
    def __init__(self, provider: ProviderConfig):
        self.provider = provider
    
    async def test_connection(self) -> bool:
        """Testa conexão com o provider"""
        raise NotImplementedError
    
    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming"""
        raise NotImplementedError


class GeminiClient(LLMClient):
    """Cliente para Gemini API"""
    
    def __init__(self, provider: ProviderConfig):
        super().__init__(provider)
        self.models_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.model_pick_cache: Dict[str, str] = {}
    
    async def test_connection(self) -> bool:
        """Testa conexão com Gemini"""
        key = self.provider.get_next_key()
        if not key:
            return False
        
        url = f"{self.provider.base_url}/models"
        headers = {"x-goog-api-key": key}
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def list_models(self, base_url: str) -> List[Dict[str, Any]]:
        """Lista modelos disponíveis"""
        base_url = normalize_gemini_base_url(base_url)
        if base_url in self.models_cache:
            return self.models_cache[base_url]
        
        key = self.provider.get_next_key()
        if not key:
            return []
        
        url = f"{base_url}/models"
        headers = {"x-goog-api-key": key}
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        self.models_cache[base_url] = models
                        return models
        except Exception:
            pass
        
        return []
    
    async def pick_model(self, base_url: str) -> Optional[str]:
        """Escolhe melhor modelo disponível"""
        cache_key = normalize_gemini_base_url(base_url)
        if cache_key in self.model_pick_cache:
            return self.model_pick_cache[cache_key]
        
        models = await self.list_models(base_url)
        if not models:
            return None
        
        # Preferência por modelos mais recentes/capazes
        preferred_order = [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro",
        ]
        
        available_names = [m.get("name", "") for m in models]
        best = None
        
        for pref in preferred_order:
            for name in available_names:
                if pref in name:
                    best = name
                    break
            if best:
                break
        
        if not best and available_names:
            best = available_names[0]
        
        if best:
            self.model_pick_cache[cache_key] = best
        
        return best
    
    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming do Gemini"""
        key = self.provider.get_next_key()
        if not key:
            yield "Erro: Nenhuma chave API disponível para Gemini"
            return
        
        base_url = normalize_gemini_base_url(self.provider.base_url)
        model = await self.pick_model(base_url)
        
        if not model:
            yield "Erro: Nenhum modelo disponível para Gemini"
            return
        
        # Constrói prompt completo
        full_prompt = self._build_full_prompt(prompt, expert, user_context)
        
        # Tenta URLs alternativas
        last_err: Optional[Exception] = None
        for alt_url in alternate_gemini_base_urls(base_url):
            try:
                url = f"{alt_url}/models/{model}:streamGenerateContent"
                headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
                
                payload = {
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 8192,
                    },
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ],
                }
                
                timeout = aiohttp.ClientTimeout(total=60)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status != 200:
                            continue
                        
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if not line:
                                continue
                            
                            try:
                                if line.startswith('data: '):
                                    line = line[6:]
                                
                                data = json.loads(line)
                                candidates = data.get("candidates", [])
                                if candidates:
                                    content = candidates[0].get("content", {})
                                    parts = content.get("parts", [])
                                    if parts:
                                        text = parts[0].get("text", "")
                                        if text:
                                            yield text
                            except json.JSONDecodeError:
                                continue
                        
                        return  # Sucesso
            
            except Exception as e:
                last_err = e
                continue
        
        if last_err:
            yield f"Erro Gemini: {str(last_err)}"
        else:
            yield "Erro: Falha ao conectar com Gemini em todas as URLs"
    
    def _build_full_prompt(
        self, prompt: str, expert: Dict[str, Any], user_context: Optional[str]
    ) -> str:
        """Constrói prompt completo com contexto do expert"""
        expert_prompt = (expert or {}).get("prompt") or ""
        if expert_prompt:
            return f"{expert_prompt}\n\n{prompt}"
        return prompt


class GroqClient(LLMClient):
    """Cliente para Groq API"""
    
    async def test_connection(self) -> bool:
        """Testa conexão com Groq"""
        key = self.provider.get_next_key()
        if not key:
            return False
        
        url = f"{self.provider.base_url}/models"
        headers = {"Authorization": f"Bearer {key}"}
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming do Groq"""
        key = self.provider.get_next_key()
        if not key:
            yield "Erro: Nenhuma chave API disponível para Groq"
            return
        
        base_url = self.provider.base_url
        model = self.provider.model
        
        # Constrói mensagens para API
        messages_list = []
        if expert and expert.get("prompt"):
            messages_list.append({"role": "system", "content": expert["prompt"]})
        if user_context:
            messages_list.append({"role": "system", "content": f"Contexto: {user_context}"})
        messages_list.append({"role": "user", "content": prompt})
        
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages_list,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        yield f"Erro: Status {response.status} da API Groq"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line or not line.startswith('data: '):
                            continue
                        
                        if line == 'data: [DONE]':
                            break
                        
                        try:
                            data = json.loads(line[6:])
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            yield f"Erro Groq: {str(e)}"


class OllamaClient(LLMClient):
    """Cliente para Ollama API"""
    
    async def test_connection(self) -> bool:
        """Testa conexão com Ollama"""
        url = f"{self.provider.url}/api/tags"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming do Ollama"""
        model = self.provider.model
        
        # Constrói prompt completo
        full_prompt = prompt
        if expert and expert.get("prompt"):
            full_prompt = f"{expert['prompt']}\n\n{prompt}"
        if user_context:
            full_prompt = f"Contexto: {user_context}\n\n{full_prompt}"
        
        url = f"{self.provider.url}/api/generate"
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048,
            },
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        yield f"Erro: Status {response.status} da API Ollama"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            content = data.get("response", "")
                            if content:
                                yield content
                            
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            yield f"Erro Ollama: {str(e)}"


class OpenAICompatibleClient(LLMClient):
    """Cliente para providers compatíveis com OpenAI"""
    
    async def test_connection(self) -> bool:
        """Testa conexão com provider"""
        key = self.provider.get_next_key()
        if not key:
            return False
        
        url = f"{self.provider.base_url}/models"
        headers = {"Authorization": f"Bearer {key}"}
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def stream_generate(
        self,
        prompt: str,
        expert: Dict[str, Any],
        user_context: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming do provider"""
        key = self.provider.get_next_key()
        if not key:
            yield f"Erro: Nenhuma chave API disponível para {self.provider.name}"
            return
        
        base_url = self.provider.base_url
        model = self.provider.model
        
        # Constrói mensagens para API
        messages_list = []
        if expert and expert.get("prompt"):
            messages_list.append({"role": "system", "content": expert["prompt"]})
        if user_context:
            messages_list.append({"role": "system", "content": f"Contexto: {user_context}"})
        messages_list.append({"role": "user", "content": prompt})
        
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages_list,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        yield f"Erro: Status {response.status} da API {self.provider.name}"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line or not line.startswith('data: '):
                            continue
                        
                        if line == 'data: [DONE]':
                            break
                        
                        try:
                            data = json.loads(line[6:])
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            yield f"Erro {self.provider.name}: {str(e)}"


def create_client(provider: ProviderConfig) -> LLMClient:
    """Factory function para criar cliente LLM"""
    client_map = {
        "gemini": GeminiClient,
        "groq": GroqClient,
        "ollama": OllamaClient,
        "openai": OpenAICompatibleClient,
        "openrouter": OpenAICompatibleClient,
    }
    
    client_class = client_map.get(provider.provider_id, OpenAICompatibleClient)
    return client_class(provider)
