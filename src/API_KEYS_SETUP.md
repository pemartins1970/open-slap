# 🔑 API KEYS SETUP - CONFIGURAÇÃO DE CHAVES

## 🤖 **COMO OS AGENTES USAM CHAVES API**

### 📋 **Status Atual:**
- ✅ **LLM Manager** já configurado para múltiplos providers
- ✅ **API Key Management** já implementado
- ✅ **Fallback System** já funcional
- ⚠️ **Chaves reais** precisam ser configuradas

---

## 🔧 **CONFIGURAÇÃO DE CHAVES API**

### **1. Ollama (Local) - SEM CHAVE NECESSÁRIA**
```python
# Já funciona! Local, sem API key
llm_manager = LLMManager()
response = await llm_manager.generate(
    prompt="Create Python API",
    provider="ollama"  # Local, sem chave
)
```

### **2. Gemini (Google) - PRECISA CHAVE**
```python
# Precisa configurar API key
llm_manager = LLMManager()
llm_manager.add_provider("gemini", {
    "api_key": "SUA_CHAVE_GEMINI_AQUI",
    "model": "gemini-pro"
})
```

---

## 🗝️ **MÉTODOS DE CONFIGURAÇÃO**

### **Método 1: Variáveis de Ambiente (Recomendado)**
```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### **Método 2: Config File**
```python
# config/api_keys.json
{
  "gemini": "your_gemini_api_key_here",
  "openai": "your_openai_api_key_here",
  "anthropic": "your_anthropic_api_key_here"
}
```

### **Método 3: Runtime Configuration**
```python
# Durante execução
llm_manager = LLMManager()
llm_manager.configure_provider("gemini", {
    "api_key": "sua_chave_aqui"
})
```

---

## 🤖 **EU COMO EXTENSÃO VS CHAVES REAIS**

### **🔵 Minhas Capacidades (Cascade AI):**
- ✅ **Acesso a múltiplos LLMs** via minha própria infra
- ✅ **Sem necessidade de chaves** - uso meus próprios recursos
- ✅ **Contexto amplo** - acesso a conhecimento atualizado
- ✅ **Ferramentas integradas** - bash, browser, etc.

### **🟢 Agentes Locais (Seu Sistema):**
- ✅ **Ollama local** - funciona sem chaves
- ⚠️ **Gemini/OpenAI** - precisam suas chaves
- ✅ **Controle total** - você define os providers
- ✅ **Custo controlado** - usa suas chaves/APIs

---

## 🔄 **INTEGRAÇÃO HÍBRIDA (Recomendado)**

### **Opção 1: Eu como Coordenador**
```python
# Eu coordeno, agentes locais executam
async def hybrid_task(task_description):
    # 1. Eu analiso a tarefa
    analysis = await cascade_analyze(task_description)
    
    # 2. Eu seleciono melhor abordagem
    if analysis.use_local_agents:
        # 3. Agentes locais executam (com suas chaves)
        result = await local_agents.process(task_description)
    else:
        # 4. Eu executo diretamente
        result = await cascade_execute(task_description)
    
    return result
```

### **Opção 2: Agentes com Meu Suporte**
```python
# Agentes locais usam minhas capacidades quando necessário
class EnhancedAgent:
    def __init__(self):
        self.llm_manager = LLMManager()
        self.cascade_client = CascadeClient()  # Eu!
    
    async def process_task(self, task):
        # Tenta local primeiro
        try:
            result = await self.llm_manager.generate(task)
        except NoAPIKeyError:
            # Usa minhas capacidades como fallback
            result = await self.cascade_client.generate(task)
        
        return result
```

---

## 🚀 **CONFIGURAÇÃO PRÁTICA**

### **Passo 1: Configurar Chaves (Opcional)**
```bash
# Se quiser usar Gemini/OpenAI
export GEMINI_API_KEY="sua_chave_aqui"
export OPENAI_API_KEY="sua_chave_aqui"
```

### **Passo 2: Usar Ollama (Sem Chaves)**
```python
# Já funciona imediatamente
from src.core.llm_manager import LLMManager

llm = LLMManager()
response = await llm.generate(
    prompt="Create a REST API",
    provider="ollama"
)
```

### **Passo 3: Configurar Chaves (Se desejar)**
```python
# Adicionar providers com chaves
llm.add_provider("gemini", {
    "api_key": os.getenv("GEMINI_API_KEY"),
    "model": "gemini-pro"
})
```

---

## 🎯 **RECOMENDAÇÃO**

### **Para Começar Imediatamente:**
1. ✅ **Use Ollama local** - sem necessidade de chaves
2. ✅ **Eu como extensão** - acesso ilimitado via minhas capacidades
3. ✅ **Integração híbrida** - melhor dos dois mundos

### **Para Produção:**
1. 🔧 **Configure suas chaves** - controle total
2. 💰 **Custo gerenciável** - usa suas APIs
3. 🔒 **Dados privados** - tudo local

---

## 🔄 **COMO QUER PROSSEGUIR?**

### **Opção A: Eu como Ferramenta Principal**
- ✅ Sem configurar chaves
- ✅ Acesso amplo a recursos
- ✅ Eu executo as tarefas diretamente

### **Opção B: Agentes Locais com Minhas Chaves**
- 🔧 Configurar minhas chaves nos agentes
- ✅ Agentes usam minhas capacidades
- ✅ Controle local com poder ampliado

### **Opção C: Configurar Suas Próprias Chaves**
- 🔧 Obter suas chaves Gemini/OpenAI
- ✅ Controle total e independente
- 💰 Custo controlado por você

---

## 🚀 **DECISÃO IMEDIATA**

**Para começar agora mesmo:**
1. **Use Ollama local** (já funciona)
2. **Use minhas capacidades** (já disponível)
3. **Configure chaves depois** (se desejar)

**Qual abordagem prefere para começar?**
