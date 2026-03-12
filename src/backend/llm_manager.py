import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import aiohttp
import os

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None

class BaseProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        pass

class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, prompt: str, model: str = "llama2", **kwargs) -> LLMResponse:
        session = await self._get_session()
        start_time = asyncio.get_event_loop().time()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                data = await response.json()
                response_time = asyncio.get_event_loop().time() - start_time
                
                return LLMResponse(
                    content=data.get("response", ""),
                    model=model,
                    provider="ollama",
                    response_time=response_time
                )
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")
    
    async def validate_connection(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        return ["llama2", "codellama", "mistral", "vicuna"]

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, prompt: str, model: str = "gemini-pro", **kwargs) -> LLMResponse:
        if not self.api_key:
            raise Exception("Gemini API key not provided")
        
        session = await self._get_session()
        start_time = asyncio.get_event_loop().time()
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 1024)
            }
        }
        
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        try:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                response_time = asyncio.get_event_loop().time() - start_time
                
                content = ""
                if "candidates" in data and data["candidates"]:
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                
                return LLMResponse(
                    content=content,
                    model=model,
                    provider="gemini",
                    response_time=response_time
                )
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")
    
    async def validate_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            await self.generate("test", max_tokens=10)
            return True
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        return ["gemini-pro", "gemini-pro-vision"]

class APIKeyManager:
    def __init__(self):
        self.keys: Dict[str, str] = {}
        self.rotation_index: Dict[str, int] = {}
    
    def add_key(self, service: str, api_key: str):
        if service not in self.keys:
            self.keys[service] = []
            self.rotation_index[service] = 0
        self.keys[service].append(api_key)
    
    def get_key(self, service: str) -> Optional[str]:
        if service not in self.keys or not self.keys[service]:
            return None
        
        keys = self.keys[service]
        key = keys[self.rotation_index[service]]
        
        # Rotate to next key
        self.rotation_index[service] = (self.rotation_index[service] + 1) % len(keys)
        
        return key
    
    def remove_key(self, service: str, api_key: str):
        if service in self.keys:
            self.keys[service] = [k for k in self.keys[service] if k != api_key]
            if self.rotation_index[service] >= len(self.keys[service]):
                self.rotation_index[service] = 0

class LLMManager:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.api_manager = APIKeyManager()
        self.current_provider: str = "ollama"
        self.fallback_order: List[str] = ["ollama", "gemini"]
        
        # Initialize default providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        # Add Ollama (local)
        self.providers["ollama"] = OllamaProvider()
        
        # Add Gemini (remote) - requires API key
        gemini_key = self.api_manager.get_key("gemini")
        if gemini_key:
            self.providers["gemini"] = GeminiProvider(gemini_key)
    
    def add_provider(self, name: str, provider: BaseProvider):
        self.providers[name] = provider
    
    def set_api_key(self, service: str, api_key: str):
        self.api_manager.add_key(service, api_key)
        
        # Reinitialize provider if it's Gemini
        if service == "gemini":
            self.providers["gemini"] = GeminiProvider(api_key)
    
    async def generate(self, prompt: str, provider: str = None, model: str = None, **kwargs) -> LLMResponse:
        provider = provider or self.current_provider
        
        if provider not in self.providers:
            raise Exception(f"Provider '{provider}' not available")
        
        try:
            response = await self.providers[provider].generate(prompt, model=model or "default", **kwargs)
            return response
        except Exception as e:
            # Try fallback providers
            for fallback in self.fallback_order:
                if fallback != provider and fallback in self.providers:
                    try:
                        response = await self.providers[fallback].generate(prompt, model=model or "default", **kwargs)
                        return response
                    except:
                        continue
            raise Exception(f"All providers failed. Last error: {str(e)}")
    
    async def validate_providers(self) -> Dict[str, bool]:
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.validate_connection()
            except:
                results[name] = False
        return results
    
    def get_available_providers(self) -> List[str]:
        return list(self.providers.keys())
    
    def get_provider_models(self, provider: str) -> List[str]:
        if provider in self.providers:
            return self.providers[provider].get_available_models()
        return []
    
    def set_primary_provider(self, provider: str):
        if provider in self.providers:
            self.current_provider = provider
        else:
            raise Exception(f"Provider '{provider}' not available")
    
    async def cleanup(self):
        for provider in self.providers.values():
            if hasattr(provider, 'session') and provider.session:
                await provider.session.close()

# Usage example
async def main():
    manager = LLMManager()
    
    # Set API key for Gemini
    manager.set_api_key("gemini", "your-gemini-api-key")
    
    # Test providers
    validation = await manager.validate_providers()
    print("Provider validation:", validation)
    
    # Generate response
    try:
        response = await manager.generate("Hello, how are you?")
        print(f"Response from {response.provider}: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
