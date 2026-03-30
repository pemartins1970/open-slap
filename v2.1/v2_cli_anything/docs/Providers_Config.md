# Providers Config (Open Slap!)
 
## Português (PT-BR)
 
### Onde configurar
 
- Este projeto lê variáveis de ambiente a partir do arquivo:
  - `src/.env`
- Use como base o exemplo:
  - `src/.env.example`
 
Regras do `.env`:
 
- Use `CHAVE=valor` (sem crases/backticks, sem aspas, sem espaços desnecessários).
- Pelo menos 1 provider precisa estar configurado para o backend conseguir chamar LLM.
- Providers com chave/URL vazios ou comentados são ignorados.
 
### Providers suportados (variáveis)
 
#### OpenRouter
 
```env
OPENROUTER_API_KEY=sk-xxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free
```
 
#### Gemini
 
```env
GEMINI_API_KEYS=sua_chave_aqui
GEMINI_MODEL=gemini-1.5-flash
```
 
#### Groq
 
```env
GROQ_API_KEYS=sua_chave_aqui
GROQ_MODEL=llama-3.3-70b-versatile
```
 
#### OpenAI (ou compatível)
 
```env
OPENAI_API_KEY=sua_chave_aqui
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```
 
#### Ollama (local)
 
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```
 
### Ordem de fallback (Provider Order)
 
Você pode controlar a ordem de tentativa dos providers com:
 
```env
PROVIDER_ORDER=openrouter,gemini,groq,ollama,openai
```
 
Recomendações:
 
- Coloque primeiro os providers que você realmente configurou.
- Se quiser forçar só um provider (por exemplo, só OpenRouter):
 
```env
PROVIDER_ORDER=openrouter
```
 
### Reiniciar após mudar o `.env`
 
Sempre reinicie o backend depois de editar o `.env`, para as variáveis serem recarregadas.
 
### Segurança
 
- Não faça commit do arquivo `.env`.
- Não coloque chaves em variáveis do frontend.
 
---
 
## English (EN)
 
### Where to configure
 
- This project loads environment variables from:
  - `src/.env`
- Use this example as a template:
  - `src/.env.example`
 
`.env` rules:
 
- Use `KEY=value` (no backticks, no quotes, no extra spaces).
- At least 1 provider must be configured for the backend to call an LLM.
- Providers with empty/commented keys are ignored.
 
### Supported providers (variables)
 
#### OpenRouter
 
```env
OPENROUTER_API_KEY=sk-xxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free
```
 
#### Gemini
 
```env
GEMINI_API_KEYS=your_key_here
GEMINI_MODEL=gemini-1.5-flash
```
 
#### Groq
 
```env
GROQ_API_KEYS=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
 
#### OpenAI (or compatible)
 
```env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```
 
#### Ollama (local)
 
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```
 
### Fallback order (Provider Order)
 
Control the provider try order with:
 
```env
PROVIDER_ORDER=openrouter,gemini,groq,ollama,openai
```
 
Recommendations:
 
- Put the providers you actually configured first.
- To force a single provider (e.g., OpenRouter only):
 
```env
PROVIDER_ORDER=openrouter
```
 
### Restart after editing `.env`
 
Restart the backend after changing `.env` so variables are reloaded.
 
### Security
 
- Do not commit `.env`.
- Do not ship API keys in frontend variables.
