"""
Registro de Skills e Expertises
"""

from typing import Dict, Any, List


class Skill:
    """Classe que representa uma skill/habilidade"""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        capabilities: List[str],
        expertise_level: float,
        category: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.expertise_level = expertise_level
        self.category = category
        self.tags = tags or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "expertise_level": self.expertise_level,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class SkillRegistry:
    """Registro central de skills disponíveis no sistema"""
    
    def __init__(self):
        self._skills = self._load_builtin_skills()
        self._categories = self._extract_categories()
    
    def _load_builtin_skills(self) -> Dict[str, Skill]:
        """Carrega skills built-in do sistema"""
        skills = {
            "systems-architect": Skill(
                id="systems-architect",
                name="Systems Architect",
                description="Designs complex systems and architectures",
                capabilities=["system_design", "architecture", "technical_analysis"],
                expertise_level=0.9,
                category="technical",
                tags=["design", "architecture", "planning"],
                metadata={"complexity": "high", "scope": "system"}
            ),
            "backend-dev": Skill(
                id="backend-dev",
                name="Backend Developer",
                description="Develops backend systems and APIs",
                capabilities=["api_design", "database", "backend_logic"],
                expertise_level=0.8,
                category="technical",
                tags=["api", "database", "server"],
                metadata={"complexity": "medium", "scope": "backend"}
            ),
            "frontend-dev": Skill(
                id="frontend-dev",
                name="Frontend Developer",
                description="Develops user interfaces and frontend applications",
                capabilities=["ui_design", "frontend_logic", "user_experience"],
                expertise_level=0.8,
                category="technical",
                tags=["ui", "ux", "frontend"],
                metadata={"complexity": "medium", "scope": "frontend"}
            ),
            "data-analyst": Skill(
                id="data-analyst",
                name="Data Analyst",
                description="Analyzes data and provides insights",
                capabilities=["data_analysis", "statistics", "visualization"],
                expertise_level=0.7,
                category="analytical",
                tags=["data", "statistics", "insights"],
                metadata={"complexity": "medium", "scope": "data"}
            ),
            "project-manager": Skill(
                id="project-manager",
                name="Project Manager",
                description="Manages projects and coordinates teams",
                capabilities=["planning", "coordination", "resource_management"],
                expertise_level=0.7,
                category="management",
                tags=["planning", "coordination", "management"],
                metadata={"complexity": "medium", "scope": "project"}
            ),
            "creative-writer": Skill(
                id="creative-writer",
                name="Creative Writer",
                description="Creates creative content and documentation",
                capabilities=["writing", "creativity", "documentation"],
                expertise_level=0.8,
                category="creative",
                tags=["writing", "content", "documentation"],
                metadata={"complexity": "low", "scope": "content"}
            ),
            "researcher": Skill(
                id="researcher",
                name="Researcher",
                description="Conducts research and gathers information",
                capabilities=["research", "information_gathering", "analysis"],
                expertise_level=0.7,
                category="research",
                tags=["research", "information", "analysis"],
                metadata={"complexity": "medium", "scope": "research"}
            ),
            "general": Skill(
                id="general",
                name="General Assistant",
                description="General purpose assistant for various tasks",
                capabilities=["general_knowledge", "problem_solving", "communication"],
                expertise_level=0.6,
                category="general",
                tags=["general", "versatile", "multi_domain"],
                metadata={"complexity": "low", "scope": "general"}
            ),
            "software-operator": Skill(
                id="software-operator",
                name="Software Operator",
                description="Executes software operations and commands",
                capabilities=["command_execution", "file_operations", "system_interaction"],
                expertise_level=0.7,
                category="operational",
                tags=["cli", "commands", "operations"],
                metadata={"complexity": "medium", "scope": "system"}
            ),
            "security-specialist": Skill(
                id="security-specialist",
                name="Security Specialist",
                description="Handles security analysis and implementation",
                capabilities=["security_analysis", "vulnerability_assessment", "secure_coding"],
                expertise_level=0.8,
                category="security",
                tags=["security", "vulnerability", "compliance"],
                metadata={"complexity": "high", "scope": "security"}
            ),
            "devops-engineer": Skill(
                id="devops-engineer",
                name="DevOps Engineer",
                description="Manages deployment, infrastructure and operations",
                capabilities=["deployment", "infrastructure", "monitoring", "automation"],
                expertise_level=0.8,
                category="operations",
                tags=["devops", "infrastructure", "automation"],
                metadata={"complexity": "high", "scope": "infrastructure"}
            ),
            "ui-ux-designer": Skill(
                id="ui-ux-designer",
                name="UI/UX Designer",
                description="Designs user interfaces and user experiences",
                capabilities=["ui_design", "ux_research", "prototyping", "user_testing"],
                expertise_level=0.8,
                category="design",
                tags=["design", "ux", "prototyping"],
                metadata={"complexity": "medium", "scope": "design"}
            ),
        }
        
        return skills
    
    def _extract_categories(self) -> List[str]:
        """Extrai categorias únicas das skills"""
        categories = set()
        for skill in self._skills.values():
            categories.add(skill.category)
        return sorted(list(categories))
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Obtém skill por ID"""
        return self._skills.get(skill_id)
    
    def get_all_skills(self) -> Dict[str, Skill]:
        """Obtém todas as skills"""
        return self._skills.copy()
    
    def get_skills_by_category(self, category: str) -> List[Skill]:
        """Obtém skills por categoria"""
        return [skill for skill in self._skills.values() if skill.category == category]
    
    def get_skills_by_tag(self, tag: str) -> List[Skill]:
        """Obtém skills por tag"""
        return [skill for skill in self._skills.values() if tag in skill.tags]
    
    def search_skills(self, query: str) -> List[Skill]:
        """Busca skills por texto em nome, descrição ou capabilities"""
        query_lower = query.lower()
        results = []
        
        for skill in self._skills.values():
            # Busca no nome
            if query_lower in skill.name.lower():
                results.append(skill)
                continue
            
            # Busca na descrição
            if query_lower in skill.description.lower():
                results.append(skill)
                continue
            
            # Busca nas capabilities
            for capability in skill.capabilities:
                if query_lower in capability.lower():
                    results.append(skill)
                    break
            
            # Busca nos tags
            for tag in skill.tags:
                if query_lower in tag.lower():
                    results.append(skill)
                    break
        
        return results
    
    def get_categories(self) -> List[str]:
        """Obtém todas as categorias"""
        return self._categories.copy()
    
    def add_skill(self, skill: Skill) -> None:
        """Adiciona nova skill ao registro"""
        self._skills[skill.id] = skill
        
        # Atualiza categorias se necessário
        if skill.category not in self._categories:
            self._categories.append(skill.category)
            self._categories.sort()
    
    def remove_skill(self, skill_id: str) -> bool:
        """Remove skill do registro"""
        if skill_id in self._skills:
            del self._skills[skill_id]
            # Recalcula categorias
            self._categories = self._extract_categories()
            return True
        return False
    
    def update_skill(self, skill_id: str, **kwargs) -> bool:
        """Atualiza skill existente"""
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        
        for key, value in kwargs.items():
            if hasattr(skill, key):
                setattr(skill, key, value)
        
        # Recalcula categorias se a categoria mudou
        if "category" in kwargs:
            self._categories = self._extract_categories()
        
        return True
    
    def get_skill_recommendations(
        self, 
        context: str = None, 
        category: str = None,
        limit: int = 5
    ) -> List[Skill]:
        """Obtém recomendações de skills baseadas em contexto ou categoria"""
        candidates = []
        
        if category:
            candidates = self.get_skills_by_category(category)
        elif context:
            candidates = self.search_skills(context)
        else:
            # Retorna skills com maior expertise_level
            candidates = sorted(
                self._skills.values(), 
                key=lambda s: s.expertise_level, 
                reverse=True
            )
        
        # Ordena por expertise_level e limita
        candidates.sort(key=lambda s: s.expertise_level, reverse=True)
        return candidates[:limit]


# Instância global do registro
skill_registry = SkillRegistry()
