import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, AsyncGenerator


@dataclass
class AgentResult:
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent:
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    skills: List[Dict[str, Any]] = []

    async def stream_execute(self, intent: str, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        from backend.llm_manager_simple import llm_manager

        expert_raw = context.get("expert", self.name) if isinstance(context, dict) else self.name
        expert_name = expert_raw if isinstance(expert_raw, dict) else {"id": str(expert_raw), "name": str(expert_raw)}
        user_context = context.get("combined_context", "") if context else ""

        skills_block = ""
        if self.skills:
            parts = ["\n\n## Available Skills"]
            for s in self.skills:
                parts.append(f"\n### {s['name']}")
                parts.append(s["description"])
                parts.append(f"Input: {json.dumps(s.get('input_schema', {}))}")
                parts.append(f"Output: {json.dumps(s.get('output_schema', {}))}")
            skills_block = "\n".join(parts)

        system_block = f"{self.system_prompt}{skills_block}"
        if user_context:
            system_block += f"\n\n---\nUser context:\n{user_context}"
        prompt = f"[{self.name.upper()} intent]\n{intent}"

        async for chunk in llm_manager.stream_generate(prompt=prompt, expert=expert_name, user_context=system_block):
            if isinstance(chunk, str):
                yield chunk

    async def execute(self, intent: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        try:
            chunks = []
            async for chunk in self.stream_execute(intent, context):
                chunks.append(chunk)
            return AgentResult(status="success", data={"response": "".join(chunks), "agent": self.name})
        except Exception as e:
            return AgentResult(status="error", error=f"Agent '{self.name}' execution failed: {str(e)}")

    def get_manifest(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt[:200] + "...",
            "skills": [s["name"] for s in self.skills],
        }


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        return [a.get_manifest() for a in self._agents.values()]

    async def execute_on_agent(self, name: str, intent: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        agent = self.get(name)
        if not agent:
            return AgentResult(status="error", error=f"Agent '{name}' not found")
        return await agent.execute(intent, context)

agent_registry = AgentRegistry()
