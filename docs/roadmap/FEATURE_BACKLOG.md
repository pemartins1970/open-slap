# Feature Backlog — Open Slap!

> **Organizado em**: 2026-06-08
> **Propósito**: Catálogo estruturado de todas as features, integrações e conceitos em avaliação.

---

## 1. Agentes Externos (External Agent Orchestration)

Integrar agentes CLI de terceiros ao ecossistema Open Slap!, exibindo-os na interface, compartilhando memória e recursos, e permitindo que a Sabrina os invoque conforme necessário.

### Conceito
- Painel de controle de operação de agentes externos (originalmente concebido, depois apropriado pelo Hermes)
- Ambiente local em containers (alternativa ao VMC), conversível em VPS se desejado
- Agentes externos usam estrutura de memória do Open Slap! (4 camadas JSON + SQLite)
- Histórico de chats exportável/importável entre agentes

### Candidatos Iniciais
| Agente | Prioridade | Notas |
|--------|-----------|-------|
| Open Claw | Alta | Integração nativa Windows em breve — acompanhar de perto |
| Hermes | Média | Apropriou o conceito original do painel |
| pi | Média | Avaliar viabilidade |
| kimi | Baixa | Avaliar viabilidade |

### Ação Imediata Recomendada
- Clonar repositórios localmente
- Analisar src em profundidade (oportunidades, insights, padrões)
- Fazer antes de avançar mudanças de frontend

### Agent Browser (Vercel)
- https://github.com/vercel-labs/agent-browser
- Promete ser superior ao Playwright para navegação headless
- Avaliar como alternativa ao software_operator para tasks de scraping/navegação

---

## 2. Messengers (Integração de Mensageria)

Alta demanda de usuários por integração nativa, intuitiva e simples de configurar na interface, permitindo ao agente enviar e receber mensagens.

### Prioritários
| Plataforma | Complexidade | Notas |
|-----------|-------------|-------|
| Telegram | Baixa | Mais simples de implementar |
| Slack | Média | API robusta, bem documentada |
| Discord | Média | Webhooks + bot API |

### Sequência
| Plataforma | Complexidade | Notas |
|-----------|-------------|-------|
| WhatsApp | Alta | Solução via QR Code + bibliotecas Python gratuitas (pywhatkit, sendwhatmsg_instantly). Alternativa: selenium/web automation |
| IRC | Baixa | Protocolo simples, baixa demanda |
| Microsoft Teams | Alta | Graph API, complexidade de auth |
| Signal | Alta | Criptografia, limitações de API |

---

## 3. Conectores (Integrações de Serviço)

| Conector | Funcionalidade | Prioridade |
|---------|---------------|-----------|
| Google (email, calendar, chat) | Acesso a serviços Google via API | Alta |
| SMS (Twilio) | Envio/recebimento de SMS | Média |
| Meu Navegador | Agente acessa navegador com credenciais logadas do usuário | Média |

---

## 4. MCP Servers para Open Slap!

Servidores MCP que podem ser integrados como ferramentas para os agentes.

| MCP | Fonte | Status |
|-----|-------|--------|
| Google Adsense | https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server | Em avaliação |
| AI Studio Bridge | `C:\Agent\mcp-servers\aistudio-mcp-bridge` (repo: eternnoir/aistudio-mcp-server) | Já gerado, configurar MCP_API_KEY |
| ColdFusion (BEN CFML) | https://github.com/pemartins1970/ben-cfml-mcp-system | Próprio, avaliar integração |

---

## 5. Yalms Nativos (Feature Flags / Projetos Internos)

Transformar integrações e conectores adicionais em "Yalms nativos" — projetos internos que o usuário pode ativar/desativar para personalizar o sistema.

### Conceito Original
- Usuário seleciona quais "projetos internos" deseja ativar
- Sistema se comporta como plataforma modular
- Exemplo: usuário que quer usar Remotion ou Canvas para criação de vídeos via Open Slap!
  - Remotion: https://github.com/remotion-dev/remotion

---

## 6. Sistemas de Notas

| Tipo | Descrição |
|------|-----------|
| Agent Notes | Notas geradas por agentes durante operação |
| User Notes | Notas criadas manualmente pelo usuário |
| Project Notes | Notas vinculadas a projetos específicos |
| Events | Derivados de cron jobs e eventos de calendário do usuário |

---

## 7. Modelos Locais

| Modelo | Tamanho | Uso Pretendido | Status |
|--------|---------|---------------|--------|
| Gemma 4 12B | 7.6 GB | Conversação, transcrição de áudios curtos (~30s) | ✅ Baixado, testar |
| Qwen 4B | 2.3 GB | Fallback geral | ✅ Já disponível |
| Llama 3.2 1B | 1.3 GB | Fallback leve | ✅ Já disponível |

---

## 8. UX / Core — Pendentes de Decisão

### B-06: Contexto de conversa não persiste entre mensagens
O `stream_generate` em `llm_manager_simple.py` envia apenas o prompt atual como mensagem única para o LLM (`contents: [{parts: [{text: full_prompt}]}]`). O histórico de mensagens da conversa (salvo no DB via `save_message`) nunca é carregado e incluído no payload da API.

**Efeito:** cada mensagem do usuário é tratada como se fosse a primeira. O agente não lembra do que foi dito antes na mesma conversa.

**Fix:** alterar `_handle_chat_message` (ou `stream_generate`) para carregar últimas N mensagens da `conversation_id` e montar array `contents` com histórico.

### B-07: Conversas não são renomeadas automaticamente
Todas as conversas ficam com nome padrão "Chat..." — o agente nunca atualiza o título baseado no conteúdo da primeira interação.

**Fix sugerido:** após a primeira resposta do LLM, usar o conteúdo para gerar um título curto via `create_conversation(..., title=<resumo>)` ou um endpoint separado.

### B-08: Layout de mensagens usa bolha em vez de largura total
Conforme decisão anterior, o espaço da conversa deve ocupar a largura horizontal disponível em vez do formato de bolha atual. Ainda não implementado.

---

## Priorização Sugerida (reconciliada em 2026-06-08)

1. **B-06: Contexto de conversa** — falha crítica de UX, agente não retém histórico entre mensagens
2. **B-07: Renomear conversas** — todas as sessões ficam como "Chat..."
3. **B-08: Layout largura total** — ocupar espaço horizontal disponível
4. **F-01: Barra de consumo de tokens no header** ✅ concluído
5. **P-02: Force-cancel de orquestração** ✅ concluído
6. **Análise de agentes externos** — src review (Open Claw, Hermes, pi, kimi)
7. **Gemma 4 12B** — testado: 1.78 tok/s, abaixo do threshold de 2 tok/s. Impraticável como fallback.
8. **Integração Telegram** — messenger mais simples, alta demanda
9. **Open Slap como MCP server (producer)** — expor tools via /api/mcp/rpc
10. **Chronicle — sistema de memória de sessão** estilo VSCode 1.123
11. **Layout três zonas** — sidebar colapsável, tabs VS Code, chat persistente
12. **Demais messengers e conectores** — conforme demanda
