"""
🧠 MOE ROUTER SIMPLES - Versão sem dependências externas
Roteamento baseado em keywords e regex (sem sklearn/pandas)
Segundo WINDSURF_AGENT.md - Versão standalone
"""

import re
from typing import Dict, Any, List, Optional

class Expert:
    """Classe especialista simplificada"""
    
    def __init__(self, id: str, name: str, icon: str, color: str, 
                 keywords: List[str], prompt: str, description: str):
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
        """Cria especialistas baseado no WINDSURF_AGENT.md"""
        return [
            Expert(
                id="backend",
                name="Desenvolvedor Backend",
                icon="⚙️",
                color="#10b981",
                keywords=["api", "backend", "server", "database", "sql", "python", "fastapi", "flask", "django", "node"],
                prompt="Você é um especialista em desenvolvimento backend. Responda com foco em arquitetura de servidores, APIs, bancos de dados e boas práticas de backend.",
                description="Especialista em desenvolvimento de servidores, APIs e bancos de dados"
            ),
            Expert(
                id="frontend",
                name="Desenvolvedor Frontend",
                icon="🎨",
                color="#f59e0b",
                keywords=["frontend", "react", "vue", "angular", "css", "html", "javascript", "typescript", "ui", "ux"],
                prompt="Você é um especialista em desenvolvimento frontend. Responda com foco em React, JavaScript, CSS, design responsivo e experiência do usuário.",
                description="Especialista em desenvolvimento de interfaces web e experiência do usuário"
            ),
            Expert(
                id="devops",
                name="Engenheiro DevOps",
                icon="🚀",
                color="#8b5cf6",
                keywords=["docker", "kubernetes", "deploy", "ci/cd", "aws", "cloud", "infrastructure", "monitoring"],
                prompt="Você é um especialista em DevOps e infraestrutura. Responda com foco em Docker, Kubernetes, CI/CD, cloud e monitoramento.",
                description="Especialista em infraestrutura, deploy e operações"
            ),
            Expert(
                id="security",
                name="Especialista em Segurança",
                icon="🔒",
                color="#ef4444",
                keywords=["security", "auth", "jwt", "oauth", "encryption", "vulnerability", "hack", "attack"],
                prompt="Você é um especialista em segurança da informação. Responda com foco em autenticação, criptografia, vulnerabilidades e boas práticas de segurança.",
                description="Especialista em segurança da informação e proteção de dados"
            ),
            Expert(
                id="data",
                name="Cientista de Dados",
                icon="📊",
                color="#06b6d4",
                keywords=["data", "analytics", "machine learning", "ai", "statistics", "python", "pandas", "numpy"],
                prompt="Você é um especialista em ciência de dados. Responda com foco em análise de dados, machine learning, estatística e visualização.",
                description="Especialista em análise de dados e machine learning"
            ),
            Expert(
                id="general",
                name="Assistente Geral",
                icon="🤖",
                color="#6b7280",
                keywords=["help", "explain", "what", "how", "why", "general", "question"],
                prompt="Você é um assistente geral. Responda de forma clara, útil e abrangente sobre qualquer tópico.",
                description="Assistente geral para perguntas diversas"
            )
        ]
    
    def _create_keyword_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Cria padrões de regex para cada especialista"""
        patterns = {}
        
        for expert in self.experts:
            expert_patterns = []
            for keyword in expert.keywords:
                # Criar regex case-insensitive para cada keyword
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
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
    
    def select_expert(self, text: str) -> Dict[str, Any]:
        """Seleciona o especialista mais apropriado para o texto"""
        if not text or not text.strip():
            # Retornar especialista geral para texto vazio
            general_expert = next(e for e in self.experts if e.id == "general")
            return self._expert_to_dict(general_expert, 0.5)
        
        text_lower = text.lower()
        scores = {}
        
        # Calcular scores para cada especialista
        for expert in self.experts:
            score = self._calculate_keyword_score(text_lower, expert.id)
            scores[expert.id] = score
        
        # Encontrar o especialista com maior score
        best_expert_id = max(scores, key=scores.get)
        best_score = scores[best_expert_id]
        
        # Se o score for muito baixo, usar especialista geral
        if best_score < 0.1:
            best_expert_id = "general"
            best_score = 0.5
        
        best_expert = next(e for e in self.experts if e.id == best_expert_id)
        
        return self._expert_to_dict(best_expert, best_score)
    
    def _expert_to_dict(self, expert: Expert, confidence: float) -> Dict[str, Any]:
        """Converte Expert para dicionário"""
        return {
            "id": expert.id,
            "name": expert.name,
            "icon": expert.icon,
            "color": expert.color,
            "prompt": expert.prompt,
            "description": expert.description,
            "confidence": confidence
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
            "reasoning": []
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
def select_expert(text: str) -> Dict[str, Any]:
    """Seleciona especialista para o texto"""
    return moe_router.select_expert(text)

def get_experts() -> List[Dict[str, Any]]:
    """Retorna todos os especialistas"""
    return moe_router.get_experts()

def get_expert_by_id(expert_id: str) -> Optional[Dict[str, Any]]:
    """Retorna especialista por ID"""
    return moe_router.get_expert_by_id(expert_id)

def analyze_expert_selection(text: str) -> Dict[str, Any]:
    """Análise detalhada da seleção"""
    return moe_router.analyze_expert_selection(text)
