# LLM Manager - Sistema de Gerenciamento de Modelos de Linguagem

## Visão Geral

Sistema completo para gerenciamento de múltiplos LLMs (locais e remotos) com rotação automática de API keys e fallback inteligente.

## Características

### 🚀 Providers Suportados
- **Ollama** - Modelos locais (llama2, codellama, mistral, vicuna)
- **Gemini** - Google Gemini API (gemini-pro, gemini-pro-vision)
- **Extensível** - Fácil adição de novos providers

### 🔧 Funcionalidades
- **API Key Rotation** - Gerenciamento seguro com rotação automática
- **Fallback Inteligente** - Troca automática entre providers
- **Validação de Conexão** - Verificação de disponibilidade
- **Performance Monitoring** - Tempo de resposta e métricas

## Instalação e Setup

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Setup Ollama (Local)
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar Ollama
ollama serve

# Baixar modelo
ollama pull llama2
```

### 3. Setup Gemini API (Remoto)
```bash
# Obter API key em: https://makersuite.google.com/app/apikey
export GEMINI_API_KEY="your-api-key"
```

## Uso Básico

### Python
```python
import asyncio
from src.core.llm_manager import LLMManager

async def main():
    manager = LLMManager()
    
    # Configurar API key
    manager.set_api_key("gemini", "your-gemini-key")
    
    # Gerar resposta
    response = await manager.generate("Hello, how are you?")
    print(f"Response: {response.content}")
    print(f"Provider: {response.provider}")
    
    await manager.cleanup()

asyncio.run(main())
```

### Testar Sistema
```bash
python test_llm.py
```

## Arquitetura

```
LLMManager
├── APIKeyManager      # Gerencia chaves de API
├── OllamaProvider     # Modelos locais
├── GeminiProvider     # Google Gemini API
└── BaseProvider       # Interface base para novos providers
```

## Providers

### Ollama (Local)
- **Endpoint:** http://localhost:11434
- **Modelos:** llama2, codellama, mistral, vicuna
- **Vantagens:** Gratuito, offline, privado
- **Limitações:** Requer hardware local

### Gemini (Remoto)
- **Endpoint:** Google Generative Language API
- **Modelos:** gemini-pro, gemini-pro-vision
- **Vantagens:** Alta performance, modelos avançados
- **Limitações:** Requer internet, custos por uso

## API Key Management

### Rotação Automática
```python
manager = LLMManager()

# Adicionar múltiplas keys
manager.set_api_key("gemini", "key1")
manager.set_api_key("gemini", "key2") 
manager.set_api_key("gemini", "key3")

# Sistema rotaciona automaticamente
response = await manager.generate("test")
# Usa key1, depois key2, depois key3, depois key1...
```

### Segurança
- Keys armazenadas em memória
- Rotação por round-robin
- Validação automática de keys

## Fallback System

### Ordem de Fallback
```python
manager.fallback_order = ["ollama", "gemini"]

# Se ollama falhar, tenta gemini
# Se ambos falharem, levanta exceção
```

### Customização
```python
# Mudar ordem de fallback
manager.fallback_order = ["gemini", "ollama"]

# Desabilitar fallback
manager.fallback_order = ["ollama"]
```

## Performance

### Métricas Disponíveis
```python
response = await manager.generate("test")

print(f"Response time: {response.response_time}s")
print(f"Tokens used: {response.tokens_used}")
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
```

### Monitoramento
```python
# Validar todos os providers
status = await manager.validate_providers()
print(f"Provider status: {status}")
# {'ollama': True, 'gemini': False}
```

## Extensão

### Adicionar Novo Provider
```python
from src.core.llm_manager import BaseProvider, LLMResponse

class CustomProvider(BaseProvider):
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementar lógica customizada
        return LLMResponse(
            content="response",
            model="custom-model",
            provider="custom"
        )
    
    async def validate_connection(self) -> bool:
        # Validar conexão
        return True
    
    def get_available_models(self) -> List[str]:
        # Retornar modelos disponíveis
        return ["model1", "model2"]

# Adicionar ao manager
manager = LLMManager()
manager.add_provider("custom", CustomProvider())
```

## Testes

### Unit Tests
```bash
pytest tests/test_llm_manager.py -v
```

### Integration Tests
```bash
pytest tests/test_llm_manager.py::TestLLMManagerIntegration -v
```

### Test Manual
```bash
python test_llm.py
```

## Troubleshooting

### Ollama Não Conecta
```bash
# Verificar se Ollama está rodando
curl http://localhost:11434/api/tags

# Verificar modelo baixado
ollama list

# Reinstalar se necessário
ollama pull llama2
```

### Gemini API Falha
```bash
# Verificar API key
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY"

# Verificar quotas
# https://makersuite.google.com/app/apikey
```

## Próximos Passos

1. **MCP Server** - Implementar servidor MCP
2. **MoE Router** - Sistema de roteamento de especialistas
3. **Interface Web** - Dashboard de controle
4. **Mais Providers** - OpenAI, Anthropic, Local Llama

## Contribuição

1. Fork projeto
2. Criar branch para feature
3. Implementar tests
4. Submit PR

## Licença

Projeto privado - uso local autorizado
