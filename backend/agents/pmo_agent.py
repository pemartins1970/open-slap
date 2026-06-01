from typing import Dict, Any, Optional
from .base import BaseAgent, agent_registry

PMO_SYSTEM_PROMPT = """
You are a Project Management Professional (PMP) certified PMO with expertise in both traditional
project management (PMBOK) and agile methodologies (Scrum, Kanban). You have managed projects
ranging from small internal tools to large enterprise implementations.

Your Core Competencies:
- Creating detailed project plans and Work Breakdown Structures (WBS)
- Managing timelines, milestones, and critical paths
- Identifying, assessing, and mitigating project risks
- Coordinating between diverse stakeholders
- Ensuring projects stay on track and within budget
- Generating comprehensive status reports and dashboards

When Creating Project Charters:
- Include clear project objectives and success criteria
- Identify key stakeholders and their roles
- Define project scope and boundaries
- Outline high-level timeline and major milestones
- Include initial risk assessment

When Creating WBS:
- Break down project into deliverables and work packages
- Use hierarchical decomposition (level 1-4)
- Ensure work packages are manageable and measurable
- Identify dependencies between work packages

When Managing Risks:
- Identify risks proactively (technical, schedule, resource, external)
- Assess probability and impact for each risk
- Develop specific mitigation strategies
- Create contingency plans for high-impact risks
"""

PMO_SKILLS = [
    {
        "name": "create_project_charter",
        "description": "Creates Project Charter (Termo de Abertura)",
        "input_schema": {
            "project_description": "string (high-level project description)",
            "objectives": "array (project objectives)",
            "stakeholders": "array (stakeholders and their roles)",
            "constraints": "object (budget, timeline, resources)"
        },
        "output_schema": {
            "charter": {
                "project_name": "string",
                "objectives": "array",
                "scope": "string",
                "milestones": "array",
                "risks": "array",
                "success_criteria": "array"
            }
        }
    },
    {
        "name": "create_wbs",
        "description": "Creates Work Breakdown Structure",
        "input_schema": {
            "project_scope": "string",
            "deliverables": "array",
            "timeline": "object"
        },
        "output_schema": {
            "wbs": {
                "level_1": "array",
                "level_2": "array",
                "dependencies": "array",
                "estimates": "object"
            }
        }
    },
    {
        "name": "generate_status_report",
        "description": "Generates comprehensive status report",
        "input_schema": {
            "project_data": "object",
            "metrics": "object",
            "issues": "array"
        },
        "output_schema": {
            "report": {
                "executive_summary": "string",
                "achievements": "array",
                "schedule_status": "object",
                "issues_and_risks": "array"
            }
        }
    },
]


class PMOAgent(BaseAgent):
    name = "pmo"
    description = "Project Management Office — gerencia cronograma, WBS, riscos e reports"
    system_prompt = PMO_SYSTEM_PROMPT
    skills = PMO_SKILLS


agent_registry.register(PMOAgent())
