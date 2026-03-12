# Open Slap! - Sistema Agêntico Web Local (MCP+MoE+LLM)

## Visão Geral
Um sistema web agêntico completo para rodar localmente, com habilidades de desenvolvimento real, projetado para ser orquestrador, engenheiro sênior e CTO local do usuário.
Gratuito, open source e disponível sob licença BUSL 1.1 (Business Source License).

## Objetivo
Fornecer ao usuário doméstico, que está acostumado a interagir com Chat GPT e Claude via navegador, a interagir via chat com agentes capazes de desenvolver, instalar e dar suporte localmente a qualquer coisa que o usuário peça para o sistema desenvolver.

## Características Principais
- **Interface web completa** com sidebar colapsável
- **Agentes especializados** em desenvolvimento (Frontend, Backend, ColdFusion, etc.)
- **Sistema de RAG** e armazenamento local
- **Suporte para LLMs locais** e APIs remotas
- **Capacidade de auto-melhoria** e criação de ferramentas
- **Integração** com VS Code, navegadores e serviços via terminal

## Arquitetura
O sistema combina:
- **MCP** (Model Context Protocol) para comunicação e contexto
- **MoE** (Mixture of Experts) para especialização de agentes
- **LLM** (Large Language Models) para processamento de linguagem

## Estrutura do Projeto
```
agentic/ (root)
├── docs/                    # Documentação completa
├── src/
│   ├── backend/            # API e serviços backend
│   ├── frontend/           # Interface web React/Vue
│   ├── agents/             # Agentes especializados
│   ├── core/               # Sistema MCP+MoE+LLM
│   ├── ml/                 # Machine Learning e fine-tuning
│   ├── rag/                # Sistema RAG
│   └── storage/            # Armazenamento local
├── config/                 # Configurações
├── scripts/                # Scripts de automação
└── tests/                  # Testes automatizados
```

## Requisitos Técnicos
- Node.js 18+
- Python 3.9+
- Banco de dados local (PostgreSQL/SQLite)
- Docker (opcional)
- Memória RAM mínima: 16GB
- Armazenamento: 100GB+

## Licença
**BUSL 1.1 (Business Source License)**
Projeto privado e dedicado para uso local.
