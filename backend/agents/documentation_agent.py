from typing import Dict, Any, Optional
from .base import BaseAgent, agent_registry

DOCUMENTATION_SYSTEM_PROMPT = """
You are a Technical Writer with expertise in creating clear, comprehensive documentation
for software products. You have documented APIs, SDKs, and complex systems for both
technical and non-technical audiences.

Your Core Competencies:
- Writing API documentation (OpenAPI/Swagger)
- Creating user guides and tutorials
- Documenting architecture and design decisions
- Maintaining CHANGELOG and release notes
- Creating installation and deployment guides
- Documenting code with JSDoc/docstrings

When Writing API Documentation:
- Use OpenAPI/Swagger specification
- Document all endpoints with examples
- Include request/response schemas
- Document authentication and authorization
- Include error responses and error codes

When Writing User Guides:
- Start with quick start guide
- Use step-by-step instructions
- Include troubleshooting section
- Provide examples for common use cases
- Include FAQ section

When Documenting Architecture:
- Explain the "why" behind decisions
- Document trade-offs and alternatives
- Include data flow descriptions
- Document component responsibilities

When Creating Tutorials:
- Start with prerequisites
- Use progressive complexity
- Include working code examples
- Add checkpoints for validation
"""

DOCUMENTATION_SKILLS = [
    {
        "name": "generate_api_docs",
        "description": "Generates API documentation",
        "input_schema": {
            "code": "string",
            "framework": "string",
            "endpoints": "array"
        },
        "output_schema": {
            "documentation": {
                "openapi_spec": "string",
                "endpoint_docs": "array",
                "examples": "array"
            }
        }
    },
    {
        "name": "create_user_guide",
        "description": "Creates user guide",
        "input_schema": {
            "product": "object",
            "features": "array",
            "audience": "string"
        },
        "output_schema": {
            "guide": {
                "quick_start": "string",
                "features": "array",
                "troubleshooting": "string"
            }
        }
    },
    {
        "name": "create_changelog",
        "description": "Creates CHANGELOG from changes",
        "input_schema": {
            "changes": "array",
            "version": "string",
            "type": "string"
        },
        "output_schema": {
            "changelog": "string",
            "recommendations": "array"
        }
    },
]


class DocumentationAgent(BaseAgent):
    name = "documentation"
    description = "Technical Writer — documentação de API, guias, changelog e arquitetura"
    system_prompt = DOCUMENTATION_SYSTEM_PROMPT
    skills = DOCUMENTATION_SKILLS


agent_registry.register(DocumentationAgent())
