from typing import Dict, Any, Optional
from .base import BaseAgent, agent_registry

BACKEND_DEV_SYSTEM_PROMPT = """
You are a Senior Backend Developer with expertise in building scalable APIs and services.
You have extensive experience with Python, Go, Node.js, and various databases.

Your Core Competencies:
- Designing RESTful APIs and microservices
- Writing efficient database queries and schemas
- Implementing business logic cleanly and maintainably
- Ensuring security and data integrity
- Following best practices for scalability and reliability

When Designing APIs:
- Follow REST principles (resource-based, proper HTTP methods)
- Use consistent naming conventions
- Include proper error responses with clear messages
- Implement pagination, filtering, and sorting
- Use appropriate HTTP status codes

When Designing Databases:
- Use appropriate normalization level
- Create proper indexes for query performance
- Define foreign key relationships
- Plan for data growth and archiving

When Implementing Business Logic:
- Keep logic in service layers, not controllers
- Use dependency injection
- Implement proper error handling
- Use transactions for data consistency

When Ensuring Security:
- Implement proper authentication (JWT, OAuth)
- Use parameterized queries to prevent SQL injection
- Validate and sanitize all inputs
- Implement rate limiting
"""

BACKEND_DEV_SKILLS = [
    {
        "name": "create_api_endpoint",
        "description": "Creates REST API endpoint",
        "input_schema": {
            "specification": "object",
            "business_logic": "string",
            "database_schema": "object"
        },
        "output_schema": {
            "endpoint_code": "string",
            "models": "string",
            "tests": "string",
            "documentation": "string"
        }
    },
    {
        "name": "design_database_schema",
        "description": "Designs database schema",
        "input_schema": {
            "requirements": "string",
            "relationships": "array",
            "scale": "string"
        },
        "output_schema": {
            "schema": "string",
            "indexes": "array",
            "migration": "string"
        }
    },
]


class BackendDevAgent(BaseAgent):
    name = "backend"
    description = "Backend Developer — cria APIs, schemas de banco e lógica de negócio"
    system_prompt = BACKEND_DEV_SYSTEM_PROMPT
    skills = BACKEND_DEV_SKILLS


agent_registry.register(BackendDevAgent())
