from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class ToolSpec:
    name: str
    description: str

@dataclass
class SkillSpec:
    name: str
    description: str
    tools: List[str]

@dataclass
class ModeSpec:
    name: str
    description: str
    system_prompt: str
    skills: List[str]

class TraeAgent:
    def __init__(self) -> None:
        self.tools: Dict[str, ToolSpec] = {}
        self.skills: Dict[str, SkillSpec] = {}
        self.modes: Dict[str, ModeSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.tools = {
            "filesystem": ToolSpec(
                name="filesystem",
                description="Leitura e escrita em arquivos locais com segurança."
            ),
            "process": ToolSpec(
                name="process",
                description="Execução controlada de comandos locais."
            ),
            "lemon_core": ToolSpec(
                name="lemon_core",
                description="Integração com Lemon Core, Quality e WebSec via HTTP local."
            ),
        }

        self.skills = {
            "refactor": SkillSpec(
                name="refactor",
                description="Refatoração e modernização de código legado.",
                tools=["filesystem"]
            ),
            "deploy": SkillSpec(
                name="deploy",
                description="Planejamento e automação de deploy local.",
                tools=["process"]
            ),
            "quality_inspector": SkillSpec(
                name="quality_inspector",
                description="Análise de conteúdo e qualidade usando bancos locais.",
                tools=["lemon_core"]
            ),
        }

        base_cto_prompt = (
            "Você é o Trae, CTO local e guardião digital do ambiente Lemon. "
            "Nunca envia dados para serviços externos. "
            "Usa apenas ferramentas e APIs locais. "
            "Prioriza segurança, estabilidade e simplicidade."
        )

        self.modes = {
            "cto": ModeSpec(
                name="cto",
                description="Modo estratégico para decisões de arquitetura e roadmap.",
                system_prompt=base_cto_prompt,
                skills=["refactor", "deploy", "quality_inspector"],
            ),
            "coder": ModeSpec(
                name="coder",
                description="Modo focado em implementação de código e refactors.",
                system_prompt=base_cto_prompt,
                skills=["refactor"],
            ),
            "ops": ModeSpec(
                name="ops",
                description="Modo focado em infraestrutura, deploy e observabilidade.",
                system_prompt=base_cto_prompt,
                skills=["deploy"],
            ),
        }

    def describe(self) -> Dict[str, Any]:
        return {
            "tools": [vars(t) for t in self.tools.values()],
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "tools": s.tools,
                }
                for s in self.skills.values()
            ],
            "modes": [
                {
                    "name": m.name,
                    "description": m.description,
                    "skills": m.skills,
                }
                for m in self.modes.values()
            ],
        }

def main() -> None:
    agent = TraeAgent()
    description = agent.describe()
    import json
    print(json.dumps(description, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
