"""
🤖 LLM MANAGER SIMPLES - Versão sem dependências externas
Gerenciamento de providers LLM (Gemini, Groq, Ollama)
Segundo WINDSURF_AGENT.md - Versão standalone
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

class LLMManager:
    """Gerenciador de LLMs - Versão Simplificada"""
    
    def __init__(self):
        self.providers = self._load_providers()
        self.provider_order = self._get_provider_order()
    
    def _load_providers(self) -> Dict[str, Dict[str, Any]]:
        """Carrega configurações dos providers do ambiente"""
        providers = {}
        
        # Gemini
        gemini_keys = os.getenv("GEMINI_API_KEYS", "").split(",")
        if gemini_keys and gemini_keys[0]:
            providers["gemini"] = {
                "name": "Gemini",
                "keys": [key.strip() for key in gemini_keys if key.strip()],
                "current_key_index": 0,
                "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "enabled": True
            }
        
        # Groq
        groq_keys = os.getenv("GROQ_API_KEYS", "").split(",")
        if groq_keys and groq_keys[0]:
            providers["groq"] = {
                "name": "Groq",
                "keys": [key.strip() for key in groq_keys if key.strip()],
                "current_key_index": 0,
                "model": os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
                "base_url": "https://api.groq.com/openai/v1",
                "enabled": True
            }
        
        # Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        if ollama_url:
            providers["ollama"] = {
                "name": "Ollama",
                "url": ollama_url,
                "model": ollama_model,
                "enabled": True
            }
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        if openai_key:
            providers["openai"] = {
                "name": "OpenAI",
                "key": openai_key,
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "enabled": True
            }
        
        return providers
    
    def _get_provider_order(self) -> List[str]:
        """Obtém ordem de fallback dos providers"""
        order = os.getenv("PROVIDER_ORDER", "gemini,groq,ollama,openai")
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
        key = keys[current_index]
        
        # Avançar para próxima chave
        provider["current_key_index"] = (current_index + 1) % len(keys)
        
        return key
    
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
            
        except Exception as e:
            print(f"[llm_manager] Erro ao testar {provider_id}: {e}")
            return False
        
        return False
    
    async def _test_gemini(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Gemini"""
        key = self._get_next_key("gemini")
        if not key:
            return False
        
        url = f"{provider['base_url']}/models"
        headers = {"x-goog-api-key": key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200
    
    async def _test_groq(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Groq"""
        key = self._get_next_key("groq")
        if not key:
            return False
        
        url = f"{provider['base_url']}/models"
        headers = {"Authorization": f"Bearer {key}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200
    
    async def _test_ollama(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com Ollama"""
        url = f"{provider['url']}/api/tags"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    
    async def _test_openai(self, provider: Dict[str, Any]) -> bool:
        """Testa conexão com OpenAI"""
        url = f"{provider['base_url']}/models"
        headers = {"Authorization": f"Bearer {provider['key']}"}
        
        async with aiohttp.ClientSession() as session:
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
                "keys_count": len(provider.get("keys", [])) if "keys" in provider else 1
            }
        
        return status
    
    async def stream_generate(self, prompt: str, expert: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Gera resposta com streaming usando fallback automático"""
        
        for provider_id in self.provider_order:
            if provider_id not in self.providers:
                continue
            
            provider = self.providers[provider_id]
            if not provider["enabled"]:
                continue
            
            try:
                print(f"[llm_manager] Tentando provider: {provider_id}")
                
                if provider_id == "gemini":
                    async for chunk in self._stream_gemini(prompt, expert, provider):
                        yield chunk
                    return
                elif provider_id == "groq":
                    async for chunk in self._stream_groq(prompt, expert, provider):
                        yield chunk
                    return
                elif provider_id == "ollama":
                    async for chunk in self._stream_ollama(prompt, expert, provider):
                        yield chunk
                    return
                elif provider_id == "openai":
                    async for chunk in self._stream_openai(prompt, expert, provider):
                        yield chunk
                    return
                    
            except Exception as e:
                print(f"[llm_manager] Erro no provider {provider_id}: {e}")
                continue
        
        # Se todos falharem, retornar mensagem de erro
        yield "❌ Todos os providers estão indisponíveis. Verifique suas configurações de API."
    
    async def _stream_gemini(self, prompt: str, expert: Dict[str, Any], provider: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Streaming com Gemini"""
        key = self._get_next_key("gemini")
        if not key:
            raise Exception("Sem chaves Gemini disponíveis")
        
        # Adicionar prompt do especialista
        full_prompt = f"{expert['prompt']}\n\nPergunta: {prompt}\n\nResposta:"
        
        url = f"{provider['base_url']}/models/{provider['model']}:streamGenerateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": key
        }
        
        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"Gemini API error: {response.status}")
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if "candidates" in data and data["candidates"]:
                                content = data["candidates"][0]["content"]["parts"][0]["text"]
                                yield content
                        except json.JSONDecodeError:
                            continue
    
    async def _stream_groq(self, prompt: str, expert: Dict[str, Any], provider: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Streaming com Groq"""
        key = self._get_next_key("groq")
        if not key:
            raise Exception("Sem chaves Groq disponíveis")
        
        # Adicionar prompt do especialista
        full_prompt = f"{expert['prompt']}\n\nPergunta: {prompt}\n\nResposta:"
        
        url = f"{provider['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        
        data = {
            "model": provider["model"],
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"Groq API error: {response.status}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and data["choices"]:
                                content = data["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
    
    async def _stream_ollama(self, prompt: str, expert: Dict[str, Any], provider: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Streaming com Ollama"""
        # Adicionar prompt do especialista
        full_prompt = f"{expert['prompt']}\n\nPergunta: {prompt}\n\nResposta:"
        
        url = f"{provider['url']}/api/generate"
        data = {
            "model": provider["model"],
            "prompt": full_prompt,
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                async for line in response.content:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
    
    async def _stream_openai(self, prompt: str, expert: Dict[str, Any], provider: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Streaming com OpenAI"""
        # Adicionar prompt do especialista
        full_prompt = f"{expert['prompt']}\n\nPergunta: {prompt}\n\nResposta:"
        
        url = f"{provider['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}"
        }
        
        data = {
            "model": provider["model"],
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API error: {response.status}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
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

async def stream_generate(prompt: str, expert: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Gera resposta com streaming"""
    async for chunk in llm_manager.stream_generate(prompt, expert):
        yield chunk
