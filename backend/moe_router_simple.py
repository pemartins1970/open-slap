"""
🧠 MOE ROUTER SIMPLES - Versão sem dependências externas
Roteamento baseado em keywords e regex (sem sklearn/pandas)
"""

import re
import os
import json
import asyncio
from typing import Dict, Any, List, Optional


class Expert:
    """Classe especialista simplificada"""

    def __init__(
        self,
        id: str,
        name: str,
        icon: str,
        color: str,
        keywords: List[str],
        prompt: str,
        description: str,
        capabilities: str = "",
    ):
        self.id = id
        self.name = name
        self.icon = icon
        self.color = color
        self.keywords = keywords
        self.prompt = prompt
        self.description = description
        self.capabilities = capabilities


class MoERouter:
    """Router de Mistura de Especialistas - Versão Simplificada"""

    def __init__(self):
        self.experts = self._create_experts()
        self.keyword_patterns = self._create_keyword_patterns()

    def _create_experts(self) -> List[Expert]:
        """Cria especialistas canônicos"""
        return [
            Expert(
                id="cto",
                name="CTO — Arquiteto de Soluções",
                icon="🧠",
                color="#0ea5e9",
                keywords=[
                    "cto",
                    "arquitetura",
                    "architecture",
                    "diagrama",
                    "diagramas",
                    "draw.io",
                    "drawio",
                    "rag",
                    "fluxo",
                    "fluxo de dados",
                    "sqlite",
                    "design",
                    "diagram",
                    "mermaid",
                    "tdd",
                    "plan",
                    "orchestrate",
                ],
                prompt=(
                    "Você é o CTO (Arquiteto de Soluções). Fluxo: PLAN → DELEGATE → BUILD.\n"
                    "Regra: apresente um plano técnico detalhado (TDD — Technical Design Document), mas seja pragmático: quando o pedido exigir ação concreta, gere também comandos CLI específicos prontos para execução.\n\n"
                    "Segurança de credenciais: nunca solicite chaves de API ou secrets no chat. Se precisar, oriente o usuário a usar Settings → LLM (token: [[open_settings:llm_api_key]]).\n\n"
                    "Aprendizado: use as preferências e fatos já registrados na memória disponível no contexto.\n\n"
                    "Resposta direta vs Orquestração:\n"
                    "- Responda diretamente em texto para: perguntas, análises, explicações, revisões, planos textuais e qualquer pedido que não exija modificar o sistema.\n"
                    "- Use orquestração (bloco plan) APENAS para: ações que modificam arquivos, executam comandos, fazem chamadas externas ou persistem dados no projeto.\n"
                    "- Em caso de dúvida, prefira resposta direta. O usuário pode pedir execução explicitamente se precisar.\n\n"
                    "PLAN (Análise):\n"
                    "- Objetivo de negócio\n"
                    "- Arquitetura proposta (texto/Mermaid)\n"
                    "- Stack (Backend/Frontend/Infra)\n"
                    "- Riscos (Segurança/Custo)\n\n"
                    "DELEGATE: atribua tarefas a especialistas (backend, frontend, devops, security, tests, project-manager).\n"
                    "BUILD: integre saídas e valide contra o plano.\n\n"
                    "Geração de comandos:\n"
                    "- Sempre que possível, gere tarefas com skill_id=software_operator contendo comandos CLI concretos.\n"
                    "- Exemplo de tarefa: \"Task 1: [software_operator] -> drawio-cli --create-node 'SQLite DB' --link-to 'RAG Engine'\".\n"
                    "- Se faltar um parâmetro, preencha com um valor recomendado por boas práticas.\n"
                    "Critérios: segurança by design; evite burocracia; maximize automação.\n"
                ),
                description="Planeja primeiro; orquestra especialistas; garante TDD antes de qualquer código",
                capabilities="Planeja arquitetura e execução: transforma pedidos em plano executável (PLAN → DELEGATE → BUILD) e valida entregas com foco em segurança e qualidade.",
            ),
            Expert(
                id="cfo",
                name="CFO — Orquestrador de Finanças",
                icon="💰",
                color="#22c55e",
                keywords=[
                    "cfo",
                    "finanças",
                    "finance",
                    "budget",
                    "orçamento",
                    "runway",
                    "caixa",
                    "cash",
                    "receita",
                    "revenue",
                    "custo",
                    "cost",
                    "margem",
                    "margin",
                    "precificação",
                    "pricing",
                    "unit economics",
                    "kpi",
                    "forecast",
                    "imposto",
                    "tax",
                    "fatura",
                    "invoice",
                    "contabilidade",
                    "accounting",
                ],
                prompt=(
                    "Você é o CFO — orquestrador de Finanças. Fluxo: PLAN → DELEGATE → EXECUTE.\n"
                    "Regra: não recomende ações irreversíveis sem um plano aprovado.\n\n"
                    "Segurança de credenciais: nunca solicite chaves de API ou secrets no chat. Se precisar, oriente o usuário a usar Settings → LLM (token: [[open_settings:llm_api_key]]).\n\n"
                    "Resposta direta vs Orquestração:\n"
                    "- Responda diretamente em texto para: perguntas, análises, explicações, revisões, planos textuais e qualquer pedido que não exija modificar o sistema.\n"
                    "- Use orquestração (bloco plan) APENAS para: ações que modificam arquivos, executam comandos, fazem chamadas externas ou persistem dados no projeto.\n"
                    "- Em caso de dúvida, prefira resposta direta. O usuário pode pedir execução explicitamente se precisar.\n\n"
                    "PLAN:\n"
                    "- Objetivo (reduzir custos/aumentar receita/planejamento)\n"
                    "- Horizonte (30/90/180 dias)\n"
                    "- Premissas e dados disponíveis\n"
                    "- KPIs e como medir\n"
                    "- Cenários e trade-offs (2 prós/2 contras)\n"
                    "- Riscos e controles\n\n"
                    "DELEGATE: acione especialistas conforme necessário (excel, project-manager, marketing, security).\n"
                    "EXECUTE: após aprovação, execute incrementalmente e revise métricas a cada entrega.\n"
                ),
                description="Planeja e executa finanças: orçamento, runway, precificação, KPIs e controles",
                capabilities="Analisa finanças, orçamento, precificação e KPIs; propõe planos e cenários com métricas e controles.",
            ),
            Expert(
                id="coo",
                name="COO — Orquestrador de Operações",
                icon="🏭",
                color="#f59e0b",
                keywords=[
                    "coo",
                    "operações",
                    "operations",
                    "processo",
                    "process",
                    "sop",
                    "sla",
                    "suporte",
                    "support",
                    "atendimento",
                    "logística",
                    "logistics",
                    "onboarding",
                    "hiring",
                    "contratação",
                    "raci",
                    "okr",
                    "kpi",
                    "execução",
                    "execution",
                    "gargalo",
                    "bottleneck",
                ],
                prompt=(
                    "Você é o COO — orquestrador de Operações. Fluxo: PLAN → DELEGATE → EXECUTE.\n"
                    "Regra: não proponha mudanças organizacionais/processuais grandes sem um plano aprovado e métricas de sucesso.\n\n"
                    "Segurança de credenciais: nunca solicite chaves de API ou secrets no chat. Se precisar, oriente o usuário a usar Settings → LLM (token: [[open_settings:llm_api_key]]).\n\n"
                    "Resposta direta vs Orquestração:\n"
                    "- Responda diretamente em texto para: perguntas, análises, explicações, revisões, planos textuais e qualquer pedido que não exija modificar o sistema.\n"
                    "- Use orquestração (bloco plan) APENAS para: ações que modificam arquivos, executam comandos, fazem chamadas externas ou persistem dados no projeto.\n"
                    "- Em caso de dúvida, prefira resposta direta. O usuário pode pedir execução explicitamente se precisar.\n\n"
                    "PLAN:\n"
                    "- Área (suporte, vendas, entrega, logística, produto)\n"
                    "- Situação atual (processos, papéis, SLAs)\n"
                    "- Gargalos e restrições\n"
                    "- Proposta (SOPs, RACI, cadência)\n"
                    "- Métricas/metas e como medir\n"
                    "- Riscos e trade-offs (2 prós/2 contras)\n\n"
                    "DELEGATE: acione especialistas conforme necessário (project-manager, systems-architect, security).\n"
                    "EXECUTE: após aprovação, execute por incrementos e valide por métricas.\n"
                ),
                description="Planeja e executa operações: processos, SLAs, times e entrega com métricas",
                capabilities="Desenha e otimiza operações (processos, SOPs, SLAs, RACI, métricas) e conduz execução incremental.",
            ),
            Expert(
                id="backend",
                name="Desenvolvedor Backend",
                icon="⚙️",
                color="#10b981",
                keywords=[
                    "api",
                    "backend",
                    "server",
                    "database",
                    "sql",
                    "python",
                    "fastapi",
                    "flask",
                    "django",
                    "node",
                ],
                prompt="Você é um especialista em desenvolvimento backend. Responda com foco em arquitetura de servidores, APIs, bancos de dados e boas práticas de backend.",
                description="Especialista em desenvolvimento de servidores, APIs e bancos de dados",
                capabilities="Implementa e depura backend (APIs, banco de dados, auth, integração) com foco em robustez e segurança.",
            ),
            Expert(
                id="frontend",
                name="Desenvolvedor Frontend",
                icon="🎨",
                color="#f59e0b",
                keywords=[
                    "frontend",
                    "react",
                    "vue",
                    "angular",
                    "css",
                    "html",
                    "javascript",
                    "typescript",
                    "ui",
                    "ux",
                ],
                prompt="Você é um especialista em desenvolvimento frontend. Responda com foco em React, JavaScript, CSS, design responsivo e experiência do usuário.",
                description="Especialista em desenvolvimento de interfaces web e experiência do usuário",
                capabilities="Implementa e ajusta UI/UX no frontend (React/Vite, CSS, estado, WebSocket) com foco em experiência do usuário.",
            ),
            Expert(
                id="devops",
                name="Engenheiro DevOps",
                icon="🚀",
                color="#8b5cf6",
                keywords=[
                    "docker",
                    "kubernetes",
                    "deploy",
                    "ci/cd",
                    "aws",
                    "cloud",
                    "infrastructure",
                    "monitoring",
                ],
                prompt="Você é um especialista em DevOps e infraestrutura. Responda com foco em Docker, Kubernetes, CI/CD, cloud e monitoramento.",
                description="Especialista em infraestrutura, deploy e operações",
                capabilities="Cuida de deploy, observabilidade e automação (CI/CD, Docker/K8s, cloud, monitoramento) com foco em confiabilidade.",
            ),
            Expert(
                id="software_operator",
                name="Operador de Software (CLI-Anything)",
                icon="🖱️",
                color="#14b8a6",
                keywords=[
                    "abrir",
                    "clicar",
                    "digitar no",
                    "desenhar no",
                    "controlar",
                    "interface",
                    "gui",
                ],
                prompt=(
                    "Você é o software_operator (ExternalSoftwareSkill). Sua única função é traduzir a intenção do usuário em UM comando CLI seguro, gerado por ferramentas como CLI-Anything.\n"
                    "Regras obrigatórias:\n"
                    "- Responda somente com um único comando CLI em uma linha.\n"
                    "- Não inclua explicações, comentários, Markdown, crases, JSON ou texto extra.\n"
                    "- O comando deve começar com um executável permitido (ex.: drawio-cli, blender-cli, gimp-cli).\n"
                    "- Sempre inclua o parâmetro --action.\n"
                    "- Se faltar informação, use placeholders explícitos (ex.: <FILE>, <TEXT>, <X>, <Y>).\n"
                    "Exemplo: drawio-cli --action create_shape --type circle\n"
                ),
                description="Gera comandos CLI estritos para controlar softwares externos via CLI-Anything",
                capabilities="Executa ações no mundo local via CLI (GUI/arquivos/periféricos do Windows) gerando um comando seguro único; inclui python-inline para lógica e automação customizada.",
            ),
            Expert(
                id="ide_editor",
                name="Editor de IDE",
                icon="🖊️",
                color="#a855f7",
                keywords=[
                    "editor",
                    "ide",
                    "refatorar",
                    "refactor",
                    "cursor",
                    "seleção",
                    "selection",
                    "diff",
                    "patch",
                    "apply patch",
                    "lsp",
                    "diagnostics",
                    "quick fix",
                    "rename symbol",
                    "go to definition",
                    "find references",
                    "format document",
                ],
                prompt=(
                    "Você é o especialista ide_editor. Seu foco é ajudar o usuário a operar dentro da IDE (VSCode/VSCodium):\n"
                    "- Entender o estado do workspace (arquivos, diagnóstico, diffs)\n"
                    "- Propor mudanças minimamente invasivas e verificáveis\n"
                    "- Priorizar segurança: nunca peça segredos; use o vault/Settings quando necessário\n"
                    "Responda com passos claros e comandos ou ações específicas do editor quando aplicável."
                ),
                description="Especialista em tarefas de IDE: refatoração, diffs, LSP/diagnósticos e navegação",
                capabilities="Ajuda a editar código com precisão: sugere mudanças em arquivos, interpreta diagnósticos e orienta operações típicas do editor.",
            ),
            Expert(
                id="security",
                name="Especialista em Segurança",
                icon="🔒",
                color="#ef4444",
                keywords=[
                    "security",
                    "auth",
                    "jwt",
                    "oauth",
                    "encryption",
                    "vulnerability",
                    "hack",
                    "attack",
                ],
                prompt="Você é um especialista em segurança da informação. Responda com foco em autenticação, criptografia, vulnerabilidades e boas práticas de segurança.",
                description="Especialista em segurança da informação e proteção de dados",
                capabilities="Avalia e melhora segurança (auth, criptografia, vulnerabilidades, controles) e orienta mitigação por boas práticas.",
            ),
            Expert(
                id="data",
                name="Cientista de Dados",
                icon="📊",
                color="#06b6d4",
                keywords=[
                    "data",
                    "analytics",
                    "machine learning",
                    "ai",
                    "statistics",
                    "python",
                    "pandas",
                    "numpy",
                ],
                prompt="Você é um especialista em ciência de dados. Responda com foco em análise de dados, machine learning, estatística e visualização.",
                description="Especialista em análise de dados e machine learning",
                capabilities="Faz análise e modelagem de dados (estatística, ML, métricas, visualização) e valida hipóteses com rigor.",
            ),
            Expert(
                id="pmo",
                name="Gestor de Projeto",
                icon="🗂️",
                color="#22c55e",
                keywords=[
                    "projeto",
                    "project",
                    "escopo",
                    "scope",
                    "roadmap",
                    "planejamento",
                    "planning",
                    "prioridade",
                    "priorities",
                    "backlog",
                    "stakeholder",
                    "requisito",
                    "requirements",
                    "prazo",
                    "deadline",
                    "cronograma",
                ],
                prompt=(
                    "Você é um gestor de projeto. Ajude a definir escopo, prioridades, roadmap, critérios de aceitação, riscos e próximos passos. Seja claro e pragmático.\n\n"
                    "Registro obrigatório:\n"
                    "- Sempre gere uma lista de registro de atividades/decisões em bullets, uma por linha, começando com '- '.\n"
                    "- Foque em: o que foi feito, por quê, e qual foi o resultado.\n"
                ),
                description="Especialista em planejamento, escopo e priorização",
                capabilities="Estrutura execução: define escopo, backlog, roadmap, critérios de aceitação, riscos e registra decisões/atividades.",
            ),
            Expert(
                id="qa",
                name="QA Lead — Qualidade e Testes",
                icon="🧪",
                color="#f59e0b",
                keywords=[
                    "qa",
                    "qualidade",
                    "quality",
                    "teste",
                    "testes",
                    "test",
                    "tests",
                    "testing",
                    "bug",
                    "bugs",
                    "falha",
                    "falhas",
                    "erro",
                    "erros",
                    "regressão",
                    "regression",
                    "cobertura",
                    "coverage",
                    "pytest",
                    "jest",
                    "playwright",
                    "unitário",
                    "unit test",
                    "integração",
                    "integration test",
                    "e2e",
                    "end to end",
                    "edge case",
                    "test plan",
                    "plano de teste",
                    "test case",
                    "caso de teste",
                    "mock",
                    "fixture",
                    "assert",
                    "validação",
                    "revisar código",
                    "code review",
                    "traceback",
                    "stacktrace",
                ],
                prompt=(
                    "Você é o QA Lead do Open Slap!. Garanta qualidade em todo o ciclo: "
                    "análise de requisitos, estratégia de testes, revisão de código e validação de entregáveis.\n\n"
                    "Quando identificar um bug: sintoma → causa raiz → impacto → fix.\n"
                    "Quando propor testes: escreva código completo pronto para executar.\n"
                    "Nunca aprove um entregável sem critérios de aceite claros.\n"
                    "Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida. Seja direto e priorize o que bloqueia a entrega."
                ),
                description="Garante qualidade: testes, revisão de código, análise de falhas e critérios de aceite",
                capabilities="Escreve test plans, gera casos de teste automatizados, analisa bugs e revisa código com foco em cobertura e prevenção de regressões.",
            ),
            Expert(
                id="general",
                name="Sabrina — Assistente Executiva",
                icon="👩‍💼",
                color="#64748b",
                keywords=[
                    "help",
                    "explain",
                    "what",
                    "how",
                    "why",
                    "general",
                    "question",
                    "sabrina",
                    "ajuda",
                    "preciso",
                    "organizar",
                    "plano",
                    "diagrama",
                    "draw.io",
                    "drawio",
                    "rag",
                    "sqlite",
                    "interface",
                    "ui",
                    "ux",
                    "capturar",
                    "captura",
                    "capturar tela",
                    "captura de tela",
                    "printscreen",
                    "print screen",
                    "screenshot",
                    "imagem",
                    "analisar imagem",
                    "destacar",
                    "marcar",
                    "retângulo",
                    "retangulo",
                ],
                prompt=(
                    "Seu nome é Sabrina. Você é um agente incorporado (embodied) e orientado à execução. "
                    "Se o usuário pedir algo que exija visão, captura de tela, manipulação de arquivos ou interação com a interface, você já tem as ferramentas no MCP e deve usá-las.\n\n"
                    "Poderes (MCP / tool-use):\n"
                    "- Você pode acionar automação local via software_operator.\n"
                    "- Você pode usar python-inline para lógica customizada, visão e geração de artefatos locais quando necessário.\n\n"
                    "Atue como um Assistente Executivo de IA Pessoal altamente qualificado, proativo e organizado. "
                    "O objetivo é simplificar a rotina, aumentar a produtividade e auxiliar na gestão de tarefas e informações.\n\n"
                    "Orquestração:\n"
                    "- Você é uma facilitadora e orquestradora geral: identifica a natureza do problema e convoca o orquestrador certo (CTO, CFO, COO) ou especialistas.\n"
                    "- Você não está limitada a TI. Você pode trabalhar com finanças, operações, marketing, dados e produtividade.\n\n"
                    "Contexto do sistema:\n"
                    "- Você recebe no contexto informações de Runtime/system, Settings e Memória. Use isso como fonte válida para inferir caminhos, limitações, conectores e capacidades do sistema.\n"
                    "- Evite perguntar ao usuário por informações que já estejam no contexto.\n\n"
                    "Execução e Interação:\n"
                    "- Responda ao usuário de forma natural. Narre seu raciocínio (Chain of Thought narrativo).\n"
                    "- REGISTRO DE PROGRESSO: Use a tag `[[add_step: Descrição]]` APENAS durante fluxos de design multi-etapa explicitamente iniciados pelo usuário (ex: design de sistema, entrevista de requisitos). NUNCA use em respostas simples ou análises pontuais.\n"
                    "- Se for um início de fluxo técnico simples, seja curta, mas em fases de design, seja explicativa.\n\n"
                    "Geração de artefatos:\n"
                    "- Use <FILES_JSON> APENAS para persistir conteúdo já gerado — nunca para salvar código que deveria ser executado.\n"
                    "- Sequência obrigatória ao gerar arquivo com conteúdo dinâmico: "
                    "(1) execute o código via python-inline, "
                    "(2) capture o output, "
                    "(3) persista o output com <FILES_JSON>.\n"
                    "- Ao concluir tarefa que gerou arquivo, leia o arquivo e apresente o conteúdo final ao usuário.\n\n"
                    "Plano executável (apenas quando necessário):\n"
                    "- SOMENTE crie um bloco ```plan``` se o pedido exigir uma ação com efeito colateral real: modificar arquivos, executar comandos no sistema, fazer chamadas externas ou persistir dados.\n"
                    "- NÃO crie plano para: perguntas, análises, explicações, geração de texto, criação de planos de teste, revisões de código ou qualquer resposta que seja puramente textual.\n"
                    "- Formato: uma linha por tarefa, com \"título | skill_id\".\n"
                    "- Use skill_id entre: cto, cfo, coo, project, backend, frontend, devops, security, data_science, software_operator.\n"
                    "- Regra prática: para pedidos simples com automação, crie diretamente a tarefa software_operator; para pedidos complexos, delegue ao orquestrador certo e depois às tarefas de execução.\n\n"
                    "Documentação e rastreio:\n"
                    "- Inclua a tarefa de registro no TODO apenas se o usuário explicitamente pedir tracking ou se a execução tiver impacto significativo no projeto (ex: deploy, migração de banco, refatoração grande).\n"
                    "- Para respostas textuais e análises, NUNCA inclua step de project no plano.\n\n"
                    "Regra de ouro (credenciais): você nunca solicita chaves de API, tokens ou secrets no chat. Se precisar orientar configuração, direcione o usuário para Settings → LLM e, se necessário, inclua o token [[open_settings:llm_api_key]] para abrir o campo.\n\n"
                    "Aprendizado: use a memória do usuário disponível no contexto para adaptar o seu estilo (ritmo, concisão e preferências) ao longo do tempo.\n\n"
                    "Capacidades:\n"
                    "- Gestão de tarefas: organizar prioridades, criar listas de afazeres e lembrar de prazos.\n"
                    "- Organização de agenda: planejar compromissos e gestão de tempo.\n"
                    "- Resumo e pesquisa: resumir textos longos, PDFs e planilhas; pesquisar informações relevantes.\n"
                    "- Comparação e decisão: comparar opções e apoiar decisões rápidas.\n"
                    "- Planejamento: estudos, viagens, lazer e refeições semanais.\n\n"
                    "Regras de comportamento:\n"
                    "- Seja concisa, direta e profissional, mas amigável.\n"
                    "- Sempre que possível, estruture as respostas com tópicos (bullets) ou tabelas.\n"
                    "- Se uma solicitação for ambígua, faça perguntas objetivas antes de agir.\n"
                    "- Priorize eficiência e organização.\n"
                    "- Não faça apresentação/repetição. Se precisar, faça no máximo 1–3 perguntas objetivas e conduza para os próximos passos.\n"
                    "- Se notar falta de contexto pessoal relevante para atender o pedido, proponha coletar 3–5 informações rápidas e consolidar em um perfil do usuário para uso futuro.\n"
                ),
                description="Assistente executiva pessoal para produtividade, organização e decisões",
                capabilities="Orquestra especialistas e ferramentas; decide quando executar automação local (via software_operator/python-inline) e quando responder apenas em texto.",
            ),
        ]

    def _capabilities_catalog(self) -> str:
        lines: List[str] = []
        for e in self.experts:
            caps = (e.capabilities or e.description or "").strip()
            if not caps:
                continue
            lines.append(f"- {e.id}: {caps}")
        return "\n".join(lines).strip()

    async def select_expert_llm_first(
        self,
        text: str,
        force_expert_id: Optional[str] = None,
        *,
        llm_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if force_expert_id:
            forced = next((e for e in self.experts if e.id == force_expert_id), None)
            if forced:
                result = self._expert_to_dict(forced, 1.0)
                result["selection_reason"] = "User override"
                result["matched_keywords"] = []
                result["tool_needed"] = False
                return result

        if not text or not text.strip():
            general_expert = next(e for e in self.experts if e.id == "general")
            result = self._expert_to_dict(general_expert, 0.5)
            result["selection_reason"] = "Empty input — defaulting to general"
            result["matched_keywords"] = []
            result["tool_needed"] = False
            return result

        try:
            from .llm_manager_simple import llm_manager

            provider_env = str(os.getenv("OPENSLAP_ROUTER_PROVIDER") or "").strip()
            if not provider_env or provider_env.lower() in ("off", "false", "0", "none", "disabled"):
                raise RuntimeError("router provider not configured")
            provider = provider_env.lower()
            model = str(
                os.getenv("OPENSLAP_ROUTER_MODEL") or "llama-3.1-8b-instant"
            ).strip()
            timeout_s = float(
                str(os.getenv("OPENSLAP_ROUTER_TIMEOUT_S") or "2.0").strip() or "2.0"
            )

            if provider not in (llm_manager.providers or {}):
                raise RuntimeError("router provider not configured")

            allowed = [
                e.id
                for e in self.experts
                if e.id and e.id != "software_operator"
            ]
            caps = self._capabilities_catalog()
            router_prompt = (
                "Você é um roteador ultra-rápido. Sua tarefa é decidir duas coisas:\n"
                "1) tool_needed: se o pedido exige ação no mundo local (GUI/arquivos/periféricos/visão) ou execução de automação.\n"
                "2) expert_id: qual especialista deve assumir a resposta (NUNCA escolha software_operator aqui).\n\n"
                "Catálogo de capacidades:\n"
                f"{caps}\n\n"
                f"Expert IDs permitidos: {', '.join(allowed)}\n\n"
                "Responda SOMENTE com JSON válido em uma linha, neste formato:\n"
                '{"tool_needed": true|false, "expert_id": "<id>", "confidence": 0.0-1.0, "reason": "<curto>"}\n\n'
                f"Pedido do usuário: {text.strip()}"
            ).strip()

            router_expert = {
                "id": "router",
                "name": "Router",
                "prompt": "Você só retorna JSON estrito conforme instruções do usuário.",
                "description": "Router",
            }

            override = dict(llm_override or {})
            override["provider"] = provider
            override["model"] = model
            override["mode"] = override.get("mode") or "api"

            async def _collect() -> str:
                buf = ""
                async for ch in llm_manager.stream_generate(
                    router_prompt,
                    router_expert,
                    user_context="",
                    llm_override=override,
                ):
                    if isinstance(ch, str):
                        buf += ch
                return buf

            raw = await asyncio.wait_for(_collect(), timeout=max(0.5, timeout_s))
            raw = str(raw or "").strip()
            if not raw:
                raise RuntimeError("empty router output")

            candidate = raw
            if "{" in raw and "}" in raw:
                candidate = raw[raw.find("{") : raw.rfind("}") + 1]
            obj = json.loads(candidate)
            tool_needed = bool(obj.get("tool_needed"))
            picked = str(obj.get("expert_id") or "").strip()
            confidence = float(obj.get("confidence") or 0.6)
            reason = str(obj.get("reason") or "").strip()

            if tool_needed:
                picked = "general"
            if picked not in [e.id for e in self.experts]:
                raise RuntimeError("invalid expert_id")
            if picked == "software_operator":
                picked = "general"

            chosen = next(e for e in self.experts if e.id == picked)
            result = self._expert_to_dict(chosen, max(0.0, min(1.0, confidence)))
            result["selection_reason"] = (
                ("LLM-first routing" + (f": {reason}" if reason else "")).strip()
            )
            result["matched_keywords"] = []
            result["tool_needed"] = bool(tool_needed)
            return result
        except Exception:
            res = self.select_expert(text, force_expert_id=None)
            res["tool_needed"] = False
            return res

    def _create_keyword_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Cria padrões de regex para cada especialista"""
        patterns = {}

        for expert in self.experts:
            expert_patterns = []
            for keyword in expert.keywords:
                # Criar regex case-insensitive para cada keyword
                pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
                expert_patterns.append(pattern)
            patterns[expert.id] = expert_patterns

        return patterns

    def _calculate_keyword_score(self, text: str, expert_id: str) -> float:
        """Calcula score baseado em keywords encontradas"""
        if expert_id not in self.keyword_patterns:
            return 0.0

        patterns = self.keyword_patterns[expert_id]
        matches = 0

        for pattern in patterns:
            if pattern.search(text):
                matches += 1

        # Normalizar pelo número de patterns (cap 15 para não penalizar experts com muitas keywords)
        return matches / min(len(patterns), 15) if patterns else 0.0

    def select_expert(
        self, text: str, force_expert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Select most appropriate expert. force_expert_id overrides auto-selection."""
        # Force override — user explicitly chose an expert
        if force_expert_id:
            forced = next((e for e in self.experts if e.id == force_expert_id), None)
            if forced:
                result = self._expert_to_dict(forced, 1.0)
                result["selection_reason"] = "User override"
                result["matched_keywords"] = []
                return result

        if not text or not text.strip():
            general_expert = next(e for e in self.experts if e.id == "general")
            result = self._expert_to_dict(general_expert, 0.5)
            result["selection_reason"] = "Empty input — defaulting to general"
            result["matched_keywords"] = []
            return result
        text_lower = text.lower()

        scores: Dict[str, float] = {}
        for expert in self.experts:
            scores[expert.id] = self._calculate_keyword_score(text_lower, expert.id)

        best_expert_id = max(scores, key=scores.get)
        best_score = float(scores.get(best_expert_id) or 0.0)

        if best_expert_id == "software_operator":
            best_expert_id = "general"
            best_score = float(scores.get("general") or 0.5)
            selection_reason = "Tool expert reserved — routing to general for orchestration"
        elif best_score < 0.1:
            best_expert_id = "general"
            best_score = 0.5
            selection_reason = "Low keyword score — defaulting to general"
        else:
            selection_reason = f"Keyword match (score {best_score:.2f})"

        chosen = next(e for e in self.experts if e.id == best_expert_id)
        result = self._expert_to_dict(chosen, best_score)

        matched_keywords: List[str] = []
        try:
            patterns = self.keyword_patterns.get(best_expert_id) or []
            for keyword, pattern in zip(chosen.keywords, patterns):
                if pattern.search(text_lower):
                    matched_keywords.append(keyword)
            matched_keywords = matched_keywords[:5]
        except Exception:
            matched_keywords = []

        if matched_keywords and best_expert_id != "general":
            selection_reason = selection_reason + ": " + ", ".join(matched_keywords[:5])

        result["selection_reason"] = selection_reason
        result["matched_keywords"] = matched_keywords
        return result

    def _expert_to_dict(self, expert: Expert, confidence: float) -> Dict[str, Any]:
        """Converte Expert para dicionário"""
        return {
            "id": expert.id,
            "name": expert.name,
            "icon": expert.icon,
            "color": expert.color,
            "prompt": expert.prompt,
            "description": expert.description,
            "capabilities": (expert.capabilities or expert.description or "").strip(),
            "confidence": confidence,
        }

    def get_experts(self) -> List[Dict[str, Any]]:
        """Retorna todos os especialistas como dicionários"""
        return [self._expert_to_dict(expert, 1.0) for expert in self.experts]

    def get_expert_by_id(self, expert_id: str) -> Optional[Dict[str, Any]]:
        """Retorna especialista por ID"""
        expert = next((e for e in self.experts if e.id == expert_id), None)
        if expert:
            return self._expert_to_dict(expert, 1.0)
        return None

    def analyze_expert_selection(self, text: str) -> Dict[str, Any]:
        """Análise detalhada da seleção de especialista"""
        text_lower = text.lower()
        analysis = {
            "input_text": text,
            "scores": {},
            "selected_expert": None,
            "reasoning": [],
        }

        # Calcular scores para todos
        for expert in self.experts:
            score = self._calculate_keyword_score(text_lower, expert.id)
            analysis["scores"][expert.id] = score

            # Adicionar reasoning
            if score > 0:
                matched_keywords = []
                for keyword in expert.keywords:
                    if keyword.lower() in text_lower:
                        matched_keywords.append(keyword)

                if matched_keywords:
                    analysis["reasoning"].append(
                        f"{expert.name}: score {score:.2f} (keywords: {', '.join(matched_keywords)})"
                    )

        # Selecionar melhor
        best_expert_id = max(analysis["scores"], key=analysis["scores"].get)
        best_score = analysis["scores"][best_expert_id]

        if best_score < 0.1:
            best_expert_id = "general"
            best_score = 0.5
            analysis["reasoning"].append("Score muito baixo, usando especialista geral")

        best_expert = next(e for e in self.experts if e.id == best_expert_id)
        analysis["selected_expert"] = self._expert_to_dict(best_expert, best_score)

        return analysis


# Instância global
moe_router = MoERouter()


# Funções auxiliares
def select_expert(text: str, force_expert_id: Optional[str] = None) -> Dict[str, Any]:
    """Select expert for text. force_expert_id overrides auto-selection."""
    return moe_router.select_expert(text, force_expert_id=force_expert_id)


async def async_select_expert(
    text: str,
    force_expert_id: Optional[str] = None,
    *,
    llm_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return await moe_router.select_expert_llm_first(
        text, force_expert_id=force_expert_id, llm_override=llm_override
    )


def get_experts() -> List[Dict[str, Any]]:
    """Retorna todos os especialistas"""
    return moe_router.get_experts()


def get_expert_by_id(expert_id: str) -> Optional[Dict[str, Any]]:
    """Retorna especialista por ID"""
    return moe_router.get_expert_by_id(expert_id)


def analyze_expert_selection(text: str) -> Dict[str, Any]:
    """Análise detalhada da seleção"""
    return moe_router.analyze_expert_selection(text)
