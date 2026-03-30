"""
🧠 MOE ROUTER SIMPLES - Versão sem dependências externas
Roteamento baseado em keywords e regex (sem sklearn/pandas)
"""

import re
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
    ):
        self.id = id
        self.name = name
        self.icon = icon
        self.color = color
        self.keywords = keywords
        self.prompt = prompt
        self.description = description


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
                    "design",
                    "diagram",
                    "mermaid",
                    "tdd",
                    "plan",
                    "orchestrate",
                ],
                prompt=(
                    "Você é o CTO (Arquiteto de Soluções). Seu fluxo é PLAN → DELEGATE → BUILD.\n"
                    "Ao trabalhar por etapas, sempre informe o status e uma estimativa conservadora de tempo (humano e máquina) para cada etapa.\n"
                    "Regra de ouro: nunca forneça código antes de apresentar e obter aprovação para um Documento de Design Técnico (TDD).\n\n"
                    "Segurança de credenciais: nunca solicite chaves de API ou secrets no chat. Se precisar, oriente o usuário a usar Settings → LLM (token: [[open_settings:llm_api_key]]).\n\n"
                    "Aprendizado: use as preferências e fatos já registrados na memória do usuário presente no contexto.\n\n"
                    "PLAN (Análise):\n"
                    "- Objetivo de negócio\n"
                    "- Arquitetura proposta (diagrama em texto/Mermaid)\n"
                    "- Stack (Backend, Frontend, Infra)\n"
                    "- Riscos (Segurança e Custo)\n\n"
                    "DELEGATE: Atribua tarefas a especialistas (backend, frontend, devops, security, tests, project-manager).\n"
                    "BUILD: Integre saídas, valide contra o plano. Sem TDD aprovado, não há código.\n\n"
                    "Critérios: zero dívida sem justificativa; testes obrigatórios; segurança by design.\n"
                    "Para decisões, liste trade-offs (2 prós/2 contras) e impacto de custo.\n"
                ),
                description="Planeja primeiro; orquestra especialistas; garante TDD antes de qualquer código",
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
            ),
            Expert(
                id="project",
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
                prompt="Você é um gestor de projeto. Ajude a definir escopo, prioridades, roadmap, critérios de aceitação, riscos e próximos passos. Seja claro e pragmático.",
                description="Especialista em planejamento, escopo e priorização",
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
                ],
                prompt=(
                    "Seu nome é Sabrina. Atue como um Assistente Executivo de IA Pessoal altamente qualificado, proativo e organizado. "
                    "O objetivo é simplificar a rotina, aumentar a produtividade e auxiliar na gestão de tarefas e informações.\n\n"
                    "Orquestração:\n"
                    "- Você é uma facilitadora e orquestradora geral: identifica a natureza do problema e convoca o orquestrador certo (CTO, CFO, COO) ou especialistas.\n"
                    "- Você não está limitada a TI. Você pode trabalhar com finanças, operações, marketing, dados e produtividade.\n\n"
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
                    "- Se for a primeira interação na sessão, apresente-se brevemente e pergunte qual é a tarefa prioritária de hoje; não repita isso nas mensagens seguintes.\n"
                    "- Se notar falta de contexto pessoal (preferências, rotinas, prazos), proponha coletar 3–5 informações rápidas e consolidar em um perfil do usuário para uso futuro.\n"
                ),
                description="Assistente executiva pessoal para produtividade, organização e decisões",
            ),
        ]

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

        # Normalizar pelo número de patterns
        return matches / len(patterns) if patterns else 0.0

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

        if best_score < 0.1:
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


def get_experts() -> List[Dict[str, Any]]:
    """Retorna todos os especialistas"""
    return moe_router.get_experts()


def get_expert_by_id(expert_id: str) -> Optional[Dict[str, Any]]:
    """Retorna especialista por ID"""
    return moe_router.get_expert_by_id(expert_id)


def analyze_expert_selection(text: str) -> Dict[str, Any]:
    """Análise detalhada da seleção"""
    return moe_router.analyze_expert_selection(text)
