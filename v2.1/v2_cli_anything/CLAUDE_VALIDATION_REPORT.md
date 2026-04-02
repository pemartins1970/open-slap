# Open Slap — Validation Report (para revisão no Claude)

Data: 31/03/2026

## Objetivo

Este report resume o que mudou recentemente (refactor/modularização) e lista pendências e pontos de atenção para revisão.

## Mudanças recentes (principais)

- Refactor frontend para reduzir o tamanho do App_auth.jsx e separar responsabilidades.
- Skills padrão extraídas para arquivo dedicado (defaults).
- Settings (Sistema / LLM / Segurança) extraídas para componentes.
- WebSocket do chat extraído para hook dedicado com reducers puros para eventos.

## Arquivos-chave alterados/adicionados

- Frontend
  - [src/frontend/src/App_auth.jsx](src/frontend/src/App_auth.jsx)
  - [src/frontend/src/data/defaultSkills.js](src/frontend/src/data/defaultSkills.js)
  - [src/frontend/src/components/settings/SystemSettingsPanel.jsx](src/frontend/src/components/settings/SystemSettingsPanel.jsx)
  - [src/frontend/src/components/settings/LlmSettingsPanel.jsx](src/frontend/src/components/settings/LlmSettingsPanel.jsx)
  - [src/frontend/src/components/settings/SecuritySettingsPanel.jsx](src/frontend/src/components/settings/SecuritySettingsPanel.jsx)
  - [src/frontend/src/hooks/useChatSocket.js](src/frontend/src/hooks/useChatSocket.js)
  - [src/frontend/src/hooks/useChunkBuffer.js](src/frontend/src/hooks/useChunkBuffer.js)
  - [src/frontend/src/lib/chatSocketReducers.js](src/frontend/src/lib/chatSocketReducers.js)

## Pendências (conhecidas / registradas)

- UX TODOs (parser/evitar PLAN em pedidos pessoais/mostrar priority e due_at/persistência do estado de aprovação do PLAN).
- Orquestrador com aprovação por etapa (pause/resume).
- Google Drive: leitura de conteúdo com chunking controlado.
- Ajuda na navbar (para humanos): ícone que abre tela de ajuda e renderiza um Markdown (guideline).

## Pontos de atenção / “zona cinzenta” (produto vs prompt)

- Respostas de “o que é o Open Slap” podem soar pré-configuradas porque o prompt-base do expert geral (“Sabrina”) enfatiza produtividade/organização; sem uma fonte canônica injetada no contexto, o modelo tende a responder de forma genérica.

## Verificação executada

- Frontend: `npm run build` (Vite) — OK.

