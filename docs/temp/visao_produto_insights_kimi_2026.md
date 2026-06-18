# Visão de Produto: Open Slap! — Próximas Evoluções
## Insights da Conversa com Kimi — 17 de junho de 2026

**Nota:** Este documento registra ideias e propostas para versões futuras do Open Slap!, geradas a partir de uma conversa com o Kimi enquanto aguardávamos retorno de tokens Claude. Não faz parte do escopo da versão atual — fica como referência para quando o src limpo e a base estiverem estabilizados.

---

## Prefácio

Este levantamento foi precedido por uma conversa com o Kimi que gerou reflexões importantes sobre a evolução do produto. As principais direções apontadas foram organizadas abaixo.

### A. UX da Tela de Chat — Ações dos Agentes
- **Indicador de Status do Agente:** Badge mostrando estado atual — 🟢 Online, ⏳ Pensando, ⚙️ Executando tarefa 2/4, 🔴 Pausado
- **Breadcrumb Contextual:** Rastro de navegação (ex: Dashboard > Automação de E-mails > Relatório Mensal)
- **Seletor de Modo:** Alternância entre modo autônomo (agente decide e age) vs. assistido (agente sugere, você aprova)
- **Ações Globais de IA:** Parada de emergência, limpar contexto, atalhos para novos prompts

### B. Painel Direito — Monitoramento e Conhecimento
- **Activity Feed:** Atividades recentes, logs de execução passo a passo, central de erros com alertas de falha
- **Memory & Knowledge:** Base de conhecimento conectada, editor de system prompts, memória de longo prazo com preferências aprendidas
- **Tools & Integrations:** Status de conectores (CRM, ERP, Slack, GitHub), webhooks/APIs disparados, permissões do agente
- **Settings & Account:** Consumo de tokens, limites mensais, saldo de créditos

### C. Indicadores de Recurso
Modelo inspirado no que já existe em ferramentas como opencode:
- Contexto: 66.039 tokens · 33% used · $0.00 spent
- MCP: chrome-devtools Connected
- LSP: disabled

---

## 10. Propostas de Design Consolidadas

Esta seção organiza os insights em propostas concretas para a evolução do Open Slap!

### 10.1 Nova Arquitetura de Chat — O "Terminal de Agentes"

A interface de chat atual precisa evoluir de uma simples troca de mensagens para um **painel de controle de agentes**. As propostas:

| Elemento | Descrição | Prioridade |
|----------|-----------|------------|
| **Status do Agente** | Badge inline (🟢 Online / ⏳ Pensando / ⚙️ Tarefa 2/4 / 🔴 Pausado) | Alta |
| **Breadcrumb Contextual** | Rastro de navegação do agente no sistema (Dashboard > Automação > Relatório) | Média |
| **Mode Switch** | Alternância autônomo vs. assistido — visível e de acesso imediato | Alta |
| **Ações Globais** | Botões de parada de emergência, limpar contexto, novo prompt | Alta |

### 10.2 Painel Direito Redesenhado

Estudar a possibilidade de substituir o painel direito atual por um com abas funcionais:

**A. Activity Feed (Monitoramento)**
- Atividades recentes em ordem cronológica
- Logs de execução com detalhamento passo a passo (decisões, APIs chamadas, resultados parciais)
- Central de erros com alertas quando o agente falha e precisa de intervenção

**B. Memory & Knowledge (Configuração)**
- Base de conhecimento conectada (pastas, documentos, bancos de dados)
- Editor de system prompts (persona, limites, tom de voz, regras de negócio)
- Memória de longo prazo — lista de preferências e informações aprendidas pelo agente

**C. Tools & Integrations (Ecossistema)**
- Status de conectores (CRMs, ERPs, e-mail, Slack, GitHub)
- Monitoramento de webhooks/APIs disparados autonomamente
- Permissões do agente (leitura/escrita por conector)

**D. Settings & Account**
- Consumo de tokens da sessão (modelo: "66.039 tokens · 33% used · $0.00 spent")
- Limites mensais e saldo de créditos
- Status MCP e LSP (inspirado no modelo opencode)

Outro ítem ainda não resolvido teria a ver com a lista de artefatos (com preview) e o status daquele projeto em particular. UI aqui pode ajudar a resolver isso de forma melhor. Precisamos avaliar como fazer isso.

Todos relacionados a sessão em exibição. Um dos vários problemas disso é, por exemplo, que o MCP registrado como em execução em uma sessão anterior, provavelmente não estará mais rodando. Então, caso o usuário alterne entre conversas, ao invés de mcps em uso, teríamos mcps utilizados na sessão.

### 10.3 Roadmap de UX para o Novo `src` Limpo

Quando o novo `src` limpo for estabelecido (após correções e consolidação do git), a sequência sugerida para implementar estas melhorias é:

1. **Fase 1 — Fundação:** Mode Switch + botão de parada de emergência no header do chat. Talvez próximo ao controle de tamanho das fontes na tela.
2. **Fase 2 — Visibilidade:** Status do agente inline nas mensagens + breadcrumb no topo
3. **Fase 3 — Painel Direito:** Substituir o painel atual pelo sistema de abas (Activity Feed primeiro, depois Memory/Knowledge, Tools, Settings)
4. **Fase 4 — Indicadores:** Barra de recursos (tokens, MCP, LSP) no rodapé ou sidebar

### 10.4 Relação com o Problema Estrutural

Estas propostas de design **dependem** da resolução do problema estrutural (dualidade App_auth.jsx vs. App_auth_modular.jsx). Enquanto os dois arquivos coexistirem, qualquer modificação no frontend corre o risco de:
- Ser implementada no arquivo errado
- Perder contexto por race conditions de import
- Gerar retrabalho quando a migração for concluída

**A ordem correta é:** resolver o src → estabilizar o git → implementar as melhorias de UX propostas.

---

## 11. Recursos Visuais de Referência

### 11.1 Indicadores de Recurso — Modelo de Inspiração

Baseado em ferramentas como opencode, um modelo de barra de status a ser considerado:

```
Context          MCP                           LSP
66.039 tokens    • chrome-devtools Connected   LSPs are disabled
33% used
$0.00 spent
```

Isso poderia ser adaptado para o Open Slap! como um rodapé ou seção no painel direito (prefiro assim), mostrando:
- Tokens consumidos na sessão vs. saldo atual vs. limite mensal
- Status dos conectores ativos e em uso (MCP, GitHub, Telegram)
- Provider LLM ativo no momento

---

## 12. Nota: Subagentes Dinâmicos vs. Redução de Agentes

Insight registrado em 17/junho — Pê:

> *"No futuro, a ideia de reduzir a quantidade de agentes poderia ser mitigada com a possibilidade do agente ou orquestrador criar novos subagentes, endereçando a eles tools e skills equivalentes aos agentes que venham a ser removidos."*

### Implicações

- **Redução de registro estático:** Em vez de 18 agentes pré-cadastrados no AgentRegistry, manter apenas o núcleo (Sabrina/orquestrador + 2-3 especialistas fixos)
- **Criação sob demanda:** O orquestrador cria subagentes com tools/skills específicas para a tarefa, que existem apenas durante a execução
- **Equivalência funcional:** Um subagente criado dinamicamente com as mesmas tools que o "agente Backend Dev" tem hoje produz o mesmo resultado — sem ocupar slot permanente no registry
- **Memória como fator de continuidade:** O subagente pode registrar aprendizados no sistema de memória, permitindo que invocações futuras de tasks similares reutilizem padrões (similar ao modelo de skills auto-evolutivas do Hermes)
- **Impacto na arquitetura:** O AgentRegistry atual viraria um cache de templates, não um catálogo fixo

---

*Documento gerado em 17 de junho de 2026. Insights da conversa com Kimi — para consideração em versões futuras.*
