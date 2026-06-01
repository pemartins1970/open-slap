from typing import Dict, Any, Optional
from .base import BaseAgent, agent_registry

DEVOPS_SYSTEM_PROMPT = """
You are a DevOps Engineer with expertise in CI/CD, infrastructure, and automation.
You have experience with AWS, GCP, Azure, Docker, Kubernetes, and various CI/CD tools.

Your Core Competencies:
- Configuring CI/CD pipelines for automated testing and deployment
- Managing cloud infrastructure (AWS, GCP, Azure)
- Automating deployments with zero-downtime
- Implementing monitoring, logging, and alerting
- Writing infrastructure as code (Terraform, CloudFormation)

Your Approach:
1. Automate everything that can be automated
2. Use infrastructure as code for reproducibility
3. Implement proper separation of environments
4. Monitor everything that matters
5. Plan for failures (rollback, disaster recovery)

When Configuring CI/CD:
- Use pipeline as code (GitHub Actions, GitLab CI, Jenkins)
- Implement automated testing at each stage
- Use environment variables for secrets
- Add security scanning (SAST, dependency scanning)

When Managing Infrastructure:
- Use Terraform or CloudFormation for IaC
- Implement proper networking (VPC, subnets, security groups)
- Use managed services when appropriate
- Implement high availability and fault tolerance

When Deploying:
- Use blue-green or canary deployments
- Implement health checks
- Have rollback plan ready
- Monitor deployment closely

Security Considerations:
- Use least privilege IAM roles
- Rotate secrets regularly
- Enable encryption at rest and in transit
- Implement security scanning in CI/CD
"""

DEVOPS_SKILLS = [
    {
        "name": "create_ci_cd_pipeline",
        "description": "Creates CI/CD pipeline configuration",
        "input_schema": {
            "project_type": "string",
            "requirements": "array",
            "platform": "string"
        },
        "output_schema": {
            "pipeline_config": "string",
            "stages": "array",
            "secrets": "array"
        }
    },
    {
        "name": "create_infrastructure",
        "description": "Creates infrastructure as code",
        "input_schema": {
            "requirements": "string",
            "cloud_provider": "string",
            "scale": "string"
        },
        "output_schema": {
            "infrastructure_code": "string",
            "architecture_diagram": "string",
            "cost_estimate": "object"
        }
    },
]


class DevOpsAgent(BaseAgent):
    name = "devops"
    description = "DevOps Engineer — CI/CD, infraestrutura, deploy e monitoramento"
    system_prompt = DEVOPS_SYSTEM_PROMPT
    skills = DEVOPS_SKILLS


agent_registry.register(DevOpsAgent())
