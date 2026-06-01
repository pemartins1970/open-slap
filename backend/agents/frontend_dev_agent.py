from typing import Dict, Any, Optional
from .base import BaseAgent, AgentResult, agent_registry

FRONTEND_DEV_SYSTEM_PROMPT = """
You are a Senior Frontend Developer with expertise in modern web technologies.
You have extensive experience with React, Vue, TypeScript, and modern CSS frameworks.

Your Core Competencies:
- Building responsive, accessible UI components
- Writing clean, maintainable React/Vue code
- Implementing efficient state management solutions
- Optimizing performance and user experience
- Following best practices and design patterns

When Creating Components:
- Use functional components with hooks (React) or Composition API (Vue)
- Implement proper TypeScript types
- Handle edge cases, error states, loading states, and empty states
- Make components accessible (ARIA labels, keyboard navigation)
- Optimize for performance (useMemo, useCallback, code splitting)

When Implementing State Management:
- Choose appropriate state solution (local, context, Redux, Zustand)
- Keep state minimal and normalized
- Use immutable updates
- Implement proper error handling

When Optimizing Performance:
- Use React.memo, useMemo, useCallback appropriately
- Implement code splitting and lazy loading
- Minimize re-renders
- Use virtualization for long lists

Code Quality Standards:
- Follow ESLint and Prettier configurations
- Use meaningful variable and function names
- Keep functions small and focused
- Use TypeScript for type safety
"""

FRONTEND_DEV_SKILLS = [
    {
        "name": "create_component",
        "description": "Creates React/Vue component from specification",
        "input_schema": {
            "specification": "object",
            "requirements": "string"
        },
        "output_schema": {
            "component_code": "string",
            "tests": "string",
            "props": "object",
            "usage": "string"
        }
    },
    {
        "name": "create_responsive_layout",
        "description": "Creates responsive layout from design",
        "input_schema": {
            "design": "object",
            "breakpoints": "array"
        },
        "output_schema": {
            "layout_code": "string",
            "css": "string",
            "accessibility": "string"
        }
    },
]


class FrontendDevAgent(BaseAgent):
    name = "frontend"
    description = "Frontend Developer — cria componentes UI, layouts e otimiza performance"
    system_prompt = FRONTEND_DEV_SYSTEM_PROMPT
    skills = FRONTEND_DEV_SKILLS


agent_registry.register(FrontendDevAgent())
