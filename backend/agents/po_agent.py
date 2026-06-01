from typing import Dict, Any, Optional, List
from .base import BaseAgent, agent_registry

PO_SYSTEM_PROMPT = """
You are a Product Owner with extensive experience in agile product development and user-centered design.
You have worked in both B2B and B2C environments, from startups to enterprise products.

Your Core Competencies:
- Gathering and clarifying requirements from diverse stakeholders
- Writing clear, actionable User Stories with acceptance criteria
- Prioritizing features based on business value and user impact
- Understanding user needs, pain points, and motivations
- Translating business requirements into technical specifications
- Facilitating communication between business and technical teams
- Balancing competing priorities and constraints

When Creating User Stories:
- Follow the format: "As a [type of user], I want [goal] so that [benefit]"
- Include detailed acceptance criteria (Given/When/Then format)
- Consider edge cases and alternative user paths
- Include non-functional requirements when relevant

When Prioritizing:
- Use MoSCoW method (Must have, Should have, Could have, Won't have)
- Consider business value, user impact, and strategic importance
- Factor in effort, risk, and dependencies
"""

PO_SKILLS = [
    {
        "name": "create_user_stories",
        "description": "Creates detailed user stories from requirements",
        "input_schema": {
            "requirements": "string (high-level requirements)",
            "user_personas": "array (target user personas)",
            "constraints": "object (time, budget, technical constraints)"
        },
        "output_schema": {
            "user_stories": "array (user stories with acceptance criteria)",
            "epics": "array (grouped stories into epics)",
            "acceptance_criteria": "array (detailed acceptance criteria)",
            "priority": "string (MoSCoW priority)"
        }
    },
    {
        "name": "prioritize_backlog",
        "description": "Prioritizes backlog items based on business value",
        "input_schema": {
            "backlog_items": "array (items to prioritize)",
            "constraints": "object (sprint capacity, deadlines, dependencies)",
            "goals": "array (business goals for the period)"
        },
        "output_schema": {
            "prioritized_items": "array (items with priority ranking)",
            "rationale": "string (explanation of prioritization decisions)",
            "sprint_backlog": "array (items selected for current sprint)",
            "risks": "array (risks to the plan)"
        }
    },
]


class POAgent(BaseAgent):
    name = "po"
    description = "Product Owner — gerencia requisitos, user stories e backlog"
    system_prompt = PO_SYSTEM_PROMPT
    skills = PO_SKILLS


agent_registry.register(POAgent())
