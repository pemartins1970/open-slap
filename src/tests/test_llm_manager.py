import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.llm_manager import LLMManager, OllamaProvider, GeminiProvider, APIKeyManager, LLMResponse

class TestAPIKeyManager:
    def test_add_key(self):
        manager = APIKeyManager()
        manager.add_key("test_service", "key1")
        manager.add_key("test_service", "key2")
        
        assert len(manager.keys["test_service"]) == 2
        assert manager.rotation_index["test_service"] == 0
    
    def test_get_key_rotation(self):
        manager = APIKeyManager()
        manager.add_key("test_service", "key1")
        manager.add_key("test_service", "key2")
        
        # Should return keys in rotation
        assert manager.get_key("test_service") == "key1"
        assert manager.get_key("test_service") == "key2"
        assert manager.get_key("test_service") == "key1"  # Back to first
    
    def test_get_nonexistent_service(self):
        manager = APIKeyManager()
        assert manager.get_key("nonexistent") is None
    
    def test_remove_key(self):
        manager = APIKeyManager()
        manager.add_key("test_service", "key1")
        manager.add_key("test_service", "key2")
        
        manager.remove_key("test_service", "key1")
        assert len(manager.keys["test_service"]) == 1
        assert manager.keys["test_service"][0] == "key2"

class TestOllamaProvider:
    @pytest.fixture
    def provider(self):
        return OllamaProvider("http://localhost:11434")
    
    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        mock_response = {
            "response": "Test response from Ollama"
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_session = AsyncMock()
            mock_post.return_value.__aenter__.return_value = mock_session
            mock_session.json.return_value = mock_response
            
            response = await provider.generate("Test prompt")
            
            assert response.content == "Test response from Ollama"
            assert response.provider == "ollama"
            assert response.model == "llama2"
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, provider):
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_session = AsyncMock()
            mock_get.return_value.__aenter__.return_value = mock_session
            mock_session.status = 200
            
            result = await provider.validate_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, provider):
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await provider.validate_connection()
            assert result is False
    
    def test_get_available_models(self, provider):
        models = provider.get_available_models()
        assert isinstance(models, list)
        assert "llama2" in models
        assert "codellama" in models

class TestGeminiProvider:
    @pytest.fixture
    def provider(self):
        return GeminiProvider("test-api-key")
    
    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Test response from Gemini"}]
                }
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_session = AsyncMock()
            mock_post.return_value.__aenter__.return_value = mock_session
            mock_session.json.return_value = mock_response
            
            response = await provider.generate("Test prompt")
            
            assert response.content == "Test response from Gemini"
            assert response.provider == "gemini"
            assert response.model == "gemini-pro"
    
    @pytest.mark.asyncio
    async def test_generate_no_api_key(self):
        provider = GeminiProvider()  # No API key
        
        with pytest.raises(Exception, match="Gemini API key not provided"):
            await provider.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, provider):
        with patch.object(provider, 'generate', return_value=LLMResponse("test", "gemini-pro", "gemini")):
            result = await provider.validate_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_connection_no_api_key(self):
        provider = GeminiProvider()  # No API key
        result = await provider.validate_connection()
        assert result is False
    
    def test_get_available_models(self, provider):
        models = provider.get_available_models()
        assert isinstance(models, list)
        assert "gemini-pro" in models
        assert "gemini-pro-vision" in models

class TestLLMManager:
    @pytest.fixture
    def manager(self):
        return LLMManager()
    
    def test_initialization(self, manager):
        assert "ollama" in manager.providers
        assert isinstance(manager.providers["ollama"], OllamaProvider)
        assert manager.current_provider == "ollama"
    
    def test_add_provider(self, manager):
        mock_provider = MagicMock()
        manager.add_provider("test", mock_provider)
        
        assert "test" in manager.providers
        assert manager.providers["test"] == mock_provider
    
    def test_set_api_key(self, manager):
        manager.set_api_key("gemini", "test-key")
        
        assert manager.api_manager.get_key("gemini") == "test-key"
        assert "gemini" in manager.providers
        assert isinstance(manager.providers["gemini"], GeminiProvider)
    
    def test_set_primary_provider(self, manager):
        manager.set_primary_provider("ollama")
        assert manager.current_provider == "ollama"
        
        with pytest.raises(Exception, match="Provider 'nonexistent' not available"):
            manager.set_primary_provider("nonexistent")
    
    def test_get_available_providers(self, manager):
        providers = manager.get_available_providers()
        assert isinstance(providers, list)
        assert "ollama" in providers
    
    def test_get_provider_models(self, manager):
        models = manager.get_provider_models("ollama")
        assert isinstance(models, list)
        assert "llama2" in models
        
        # Non-existent provider
        models = manager.get_provider_models("nonexistent")
        assert models == []
    
    @pytest.mark.asyncio
    async def test_generate_success(self, manager):
        mock_response = LLMResponse("Test response", "llama2", "ollama")
        
        with patch.object(manager.providers["ollama"], 'generate', return_value=mock_response):
            response = await manager.generate("Test prompt")
            
            assert response.content == "Test response"
            assert response.provider == "ollama"
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback(self, manager):
        # Mock Ollama to fail, Gemini to succeed
        with patch.object(manager.providers["ollama"], 'generate', side_effect=Exception("Ollama failed")):
            # Add Gemini provider
            manager.set_api_key("gemini", "test-key")
            mock_response = LLMResponse("Fallback response", "gemini-pro", "gemini")
            
            with patch.object(manager.providers["gemini"], 'generate', return_value=mock_response):
                response = await manager.generate("Test prompt")
                
                assert response.content == "Fallback response"
                assert response.provider == "gemini"
    
    @pytest.mark.asyncio
    async def test_generate_all_providers_fail(self, manager):
        with patch.object(manager.providers["ollama"], 'generate', side_effect=Exception("Ollama failed")):
            with pytest.raises(Exception, match="All providers failed"):
                await manager.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_validate_providers(self, manager):
        with patch.object(manager.providers["ollama"], 'validate_connection', return_value=True):
            results = await manager.validate_providers()
            
            assert isinstance(results, dict)
            assert "ollama" in results
            assert results["ollama"] is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        # Add mock session to test cleanup
        mock_session = AsyncMock()
        manager.providers["ollama"].session = mock_session
        
        await manager.cleanup()
        
        mock_session.close.assert_called_once()

# Integration tests (require actual services)
@pytest.mark.integration
class TestLLMManagerIntegration:
    @pytest.mark.asyncio
    async def test_ollama_integration(self):
        """Test with actual Ollama instance if available"""
        provider = OllamaProvider()
        
        if await provider.validate_connection():
            response = await provider.generate("Hello", model="llama2")
            assert isinstance(response, LLMResponse)
            assert response.provider == "ollama"
            assert len(response.content) > 0
        else:
            pytest.skip("Ollama not available")
    
    @pytest.mark.asyncio
    async def test_gemini_integration(self):
        """Test with actual Gemini API if key is available"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("Gemini API key not available")
        
        provider = GeminiProvider(api_key)
        
        if await provider.validate_connection():
            response = await provider.generate("Hello", max_tokens=50)
            assert isinstance(response, LLMResponse)
            assert response.provider == "gemini"
            assert len(response.content) > 0
        else:
            pytest.skip("Gemini API validation failed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
