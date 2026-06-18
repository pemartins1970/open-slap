# SPEC-UI-PHASE2 — Model Selector

**Status:** Pronto para implementação  
**Dependências:** Phase 1 completo, B-03/B-04 fechados (165/165 passando)

---

## Objetivo

Adicionar um seletor de modelo/provider diretamente no chat input, permitindo troca contextual sem tocar nas settings. A escolha vale para a conversa atual (session-only). Settings permanecem intactas.

---

## Decisão de design

**Session-only via WebSocket override.** O payload do WebSocket passa a incluir `provider` + `model` opcionais. O backend usa esses campos como override sobre as settings do DB, sem modificá-las. "Save as default" é ação explícita futura — fora de escopo agora.

---

## Escopo

### IN
- Endpoint `GET /api/models/available` (novo)
- Leitura de `provider` + `model` no payload do WebSocket em `orchestrator.py`
- Componente `ModelSelector` no chat input
- Model registry: listas estáticas (Gemini, Groq, OpenAI, OpenRouter) + dinâmica (Ollama)
- Inicialização do seletor a partir do modelo ativo atual do usuário

### OUT
- Persistência automática no DB ao trocar modelo (fora de escopo — "Save as default" vem depois)
- Discovery dinâmica de OpenRouter (retorna milhares de modelos — problema de UX)
- Discovery dinâmica de Groq/OpenAI via `/v1/models` (static list é suficiente para MVP)
- Informações de custo, contexto ou capabilities dos modelos
- Favoritos ou modelos recentes
- Troca de model por mensagem individual (o override vale para toda a conversa/sessão)

---

## Backend — `GET /api/models/available`

### Endpoint

```
GET /api/models/available
Auth: Bearer token (usuário autenticado)
```

### Lógica

1. Ler `user_llm_settings` do usuário (provider configurado, API keys presentes)
2. Para cada provider, incluir na resposta **somente se tiver chave válida no DB** (ou for Ollama)
3. Ollama: chamar `GET {OLLAMA_URL}/api/tags` com timeout de **3 segundos**. Se timeout ou erro, retornar Ollama com `available: false`
4. Retornar JSON estruturado

### Response schema

```json
{
  "current": {
    "provider": "gemini",
    "model": "gemini-2.5-flash"
  },
  "providers": [
    {
      "id": "gemini",
      "name": "Gemini",
      "available": true,
      "models": [
        { "id": "gemini-2.5-flash",    "name": "Gemini 2.5 Flash" },
        { "id": "gemini-2.0-flash",    "name": "Gemini 2.0 Flash" },
        { "id": "gemini-2.0-flash-lite","name": "Gemini 2.0 Flash Lite" },
        { "id": "gemini-1.5-flash",    "name": "Gemini 1.5 Flash" },
        { "id": "gemini-1.5-pro",      "name": "Gemini 1.5 Pro" }
      ]
    },
    {
      "id": "groq",
      "name": "Groq",
      "available": true,
      "models": [
        { "id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B" },
        { "id": "llama-3.1-8b-instant",    "name": "Llama 3.1 8B" },
        { "id": "llama3-8b-8192",          "name": "Llama 3 8B" },
        { "id": "mixtral-8x7b-32768",      "name": "Mixtral 8x7B" },
        { "id": "gemma2-9b-it",            "name": "Gemma 2 9B" }
      ]
    },
    {
      "id": "openai",
      "name": "OpenAI",
      "available": false,
      "models": [
        { "id": "gpt-4o",      "name": "GPT-4o" },
        { "id": "gpt-4o-mini", "name": "GPT-4o Mini" },
        { "id": "gpt-3.5-turbo","name": "GPT-3.5 Turbo" }
      ]
    },
    {
      "id": "openrouter",
      "name": "OpenRouter",
      "available": true,
      "models": [
        { "id": "nvidia/nemotron-3-nano-30b-a3b:free", "name": "Nemotron 3 Nano (free)" },
        { "id": "qwen/qwen3-coder:free",               "name": "Qwen3 Coder (free)" },
        { "id": "meta-llama/llama-3.2-3b-instruct:free","name": "Llama 3.2 3B (free)" },
        { "id": "google/gemma-3-12b-it:free",          "name": "Gemma 3 12B (free)" }
      ]
    },
    {
      "id": "ollama",
      "name": "Ollama (Local)",
      "available": true,
      "models": [
        { "id": "llama3.2",  "name": "llama3.2" },
        { "id": "gemma3:4b", "name": "gemma3:4b" }
      ]
    }
  ]
}
```

`available: false` — provider aparece no seletor mas seus modelos ficam visualmente desabilitados (sem chave configurada). Permite ao usuário saber que o provider existe sem precisar abrir settings para isso.

### Arquivo
`backend/routes/models.py` (novo) — registrar no router principal.

---

## Backend — WebSocket override

### Mudança no `ws/orchestrator.py`

Após ler o payload do WebSocket (linha atual ~157), adicionar:

```python
# Override session-only: provider + model do seletor do chat
ws_provider = data.get("provider")  # opcional
ws_model    = data.get("model")     # opcional

# Resolver llm_override normalmente a partir do DB
llm_settings = get_user_llm_settings(user_id)
llm_override = { ... }  # lógica existente

# Aplicar override do WebSocket se presentes (maior prioridade)
if ws_provider:
    llm_override["provider"] = ws_provider
if ws_model:
    llm_override["model"] = ws_model
```

Nenhuma alteração no fluxo downstream — `stream_generate` já recebe `llm_override` e o aplica.

---

## Frontend — Componente `ModelSelector`

### Localização

`frontend/src/components/ModelSelector.jsx` (novo)

### Placement no chat input

Inline no container do textarea, canto inferior esquerdo — mesmo padrão do Claude.ai.

```
┌──────────────────────────────────────────────────┐
│  Mensagem para a Sabrina...                      │
│                                                  │
│                                                  │
│  [ Gemini · gemini-2.5-flash ▾ ]   [ Enviar → ] │
└──────────────────────────────────────────────────┘
```

O seletor e o botão Enviar ficam na barra inferior dentro do container do input. O textarea ocupa toda a largura acima deles.

### Textarea auto-expand

O textarea atual tem scroll imediato. Com o seletor inline, aplicar auto-resize:

```javascript
// No handler onInput do textarea:
e.target.style.height = 'auto'
e.target.style.height = e.target.scrollHeight + 'px'
```

```css
textarea {
  resize: none;
  overflow: hidden;
  min-height: 48px;   /* altura de uma linha */
  max-height: 240px;  /* ~5 linhas — scroll só acima disso */
}
```

Scroll interno só aparece quando o conteúdo ultrapassa `max-height`. Abaixo disso, o container cresce com o texto.

### Dropdown — estrutura

```
┌──────────────────────────────────┐
│ ● Gemini                         │
│   ✓ Gemini 2.5 Flash   ← ativo  │
│     Gemini 2.0 Flash             │
│     Gemini 2.0 Flash Lite        │
│     Gemini 1.5 Flash             │
│     Gemini 1.5 Pro               │
├──────────────────────────────────┤
│ ● Groq                           │
│     Llama 3.1 70B                │
│     Llama 3.1 8B                 │
│     ...                          │
├──────────────────────────────────┤
│ ○ OpenAI  (sem chave)            │  ← desabilitado, não clicável
│     GPT-4o                       │  ← cinza
│     ...                          │
├──────────────────────────────────┤
│ ● Ollama (Local)                 │
│     llama3.2                     │
│     gemma3:4b                    │
├──────────────────────────────────┤
│ ● OpenRouter                     │
│     Nemotron 3 Nano (free)       │
│     ...                          │
└──────────────────────────────────┘
```

- `●` verde = provider disponível, `○` cinza = sem chave
- Modelo ativo marcado com `✓`
- Providers indisponíveis: header clicável mostra tooltip "Configure uma chave em Settings"

### Estado local

```javascript
const [selectedProvider, setSelectedProvider] = useState(null)
const [selectedModel,    setSelectedModel]    = useState(null)
const [availableModels,  setAvailableModels]  = useState(null)
const [loading,          setLoading]          = useState(true)
```

**Inicialização (mount):**
1. `GET /api/models/available`
2. `setAvailableModels(response.providers)`
3. `setSelectedProvider(response.current.provider)`
4. `setSelectedModel(response.current.model)`
5. `setLoading(false)`

**Ollama loading state:** enquanto `/api/models/available` não retorna, exibir `"Carregando modelos..."` no seletor. Não bloquear o input.

### Integração com `useChatSocket` / envio de mensagem

Ao enviar mensagem, o payload passa a incluir:

```javascript
// App_auth.jsx — handleSendMessage (ou equivalente)
ws.send(JSON.stringify({
  type: "chat",
  content: message,
  provider: selectedProvider,  // novo
  model: selectedModel          // novo
}))
```

`selectedProvider` e `selectedModel` são passados como props ao componente de chat input, ou gerenciados no nível do App via estado elevado.

### Após resposta recebida

O evento `done` do WebSocket já retorna `{ provider, model }` (o que foi efetivamente usado). Se difere do selecionado (fallback aconteceu), **não atualizar o seletor** — o seletor reflete a intenção do usuário, o header reflete o que rodou de fato (comportamento B-04 já implementado).

---

## Arquivos Afetados

### Criar
| Arquivo | Conteúdo |
|---|---|
| `backend/routes/models.py` | Endpoint `/api/models/available` |
| `frontend/src/components/ModelSelector.jsx` | Componente seletor |

### Modificar
| Arquivo | Mudança |
|---|---|
| `backend/routes/__init__.py` ou router principal | Registrar `models.py` |
| `ws/orchestrator.py` | Ler `provider` + `model` do payload WS |
| `frontend/src/App_auth.jsx` | Incluir `ModelSelector`, elevar estado, passar `provider`+`model` no send |

---

## Acceptance Criteria

1. `GET /api/models/available` retorna apenas providers com chave configurada (ou Ollama se acessível)
2. Ollama: se não estiver rodando, `available: false` em ≤ 3 segundos (sem travar o chat)
3. Seletor aparece no canto inferior esquerdo do chat input, mostra provider+modelo ativos no primeiro render
4. Textarea auto-expande com o conteúdo (sem scroll imediato); scroll interno só acima de `max-height: 240px`
5. Dropdown agrupa por provider, desabilita providers sem chave com tooltip explicativo
6. Trocar modelo no seletor e enviar mensagem: backend usa o modelo selecionado (verificar via `runtimeLlmLabel` no header)
7. Settings permanecem inalteradas após troca via seletor
8. Recarregar a página: seletor volta ao modelo das settings (não persiste a escolha contextual)
9. Todos os testes passam — 165/165
10. Performance: `/api/models/available` responde em < 3s mesmo com Ollama offline

---

## Riscos

**Médio**
- Estado do seletor (`selectedProvider`, `selectedModel`) precisa ser elevado ao nível do componente que controla o envio de mensagem (`App_auth.jsx`). Dependendo de onde `handleSendMessage` vive, pode exigir prop drilling não-trivial no monolito.
- Ollama offline causando timeout de 3s em cada mount do seletor — mitigar com cache em memória: se já foi consultado na sessão, não consultar novamente.

**Baixo**
- Lista estática de modelos Groq/Gemini pode ficar desatualizada. Documentar em `backend/routes/models.py` que a lista deve ser revisada periodicamente. Não é problema de runtime.
- OpenRouter tem modelos `free` que podem sair do catálogo. Mesma mitigação: lista revisada manualmente, erro de modelo inválido já é tratado pelo fallback existente em `_stream_openrouter_fallback`.
