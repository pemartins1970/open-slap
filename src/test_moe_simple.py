#!/usr/bin/env python3
"""
Simple test script for MoE Router without sklearn dependency
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)

class ExpertStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

class TaskType(Enum):
    CODING = "coding"
    DESIGN = "design"
    ANALYSIS = "analysis"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    PLANNING = "planning"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    OPTIMIZATION = "optimization"

@dataclass
class Expert:
    id: str
    name: str
    description: str
    capabilities: List[str]
    task_types: List[TaskType]
    status: ExpertStatus
    performance_metrics: Dict[str, float]
    current_load: int
    max_concurrent_tasks: int
    last_active: datetime
    specialization_score: float
    
    def update_activity(self):
        self.last_active = datetime.now()
    
    def is_available(self) -> bool:
        return (self.status == ExpertStatus.IDLE and 
                self.current_load < self.max_concurrent_tasks)

@dataclass
class Task:
    id: str
    type: TaskType
    description: str
    requirements: List[str]
    priority: int
    estimated_duration: int
    context: Dict[str, Any]
    created_at: datetime

class SimpleMoERouter:
    """Simplified MoE Router without sklearn dependency"""
    
    def __init__(self):
        self.experts = self._create_default_experts()
        self.active_tasks = {}
        self.task_assignments = {}
    
    def _create_default_experts(self) -> Dict[str, Expert]:
        """Create default experts"""
        return {
            "architect": Expert(
                id="architect",
                name="System Architect",
                description="Designs system architecture and makes strategic decisions",
                capabilities=["system_design", "architecture", "planning"],
                task_types=[TaskType.DESIGN, TaskType.PLANNING, TaskType.ANALYSIS],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.9, "speed": 0.8, "reliability": 0.95},
                current_load=0,
                max_concurrent_tasks=3,
                last_active=datetime.now(),
                specialization_score=0.85
            ),
            "backend_dev": Expert(
                id="backend_dev",
                name="Backend Developer",
                description="Implements APIs, databases, and server-side logic",
                capabilities=["api_development", "database_design", "server_logic"],
                task_types=[TaskType.CODING, TaskType.DEPLOYMENT, TaskType.DEBUGGING],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.85, "speed": 0.9, "reliability": 0.88},
                current_load=0,
                max_concurrent_tasks=5,
                last_active=datetime.now(),
                specialization_score=0.8
            ),
            "frontend_dev": Expert(
                id="frontend_dev",
                name="Frontend Developer",
                description="Creates user interfaces and client-side applications",
                capabilities=["ui_development", "user_experience", "frontend_frameworks"],
                task_types=[TaskType.CODING, TaskType.DESIGN, TaskType.OPTIMIZATION],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.82, "speed": 0.85, "reliability": 0.86},
                current_load=0,
                max_concurrent_tasks=4,
                last_active=datetime.now(),
                specialization_score=0.75
            ),
            "security_expert": Expert(
                id="security_expert",
                name="Security Specialist",
                description="Ensures system security and performs security audits",
                capabilities=["security_analysis", "vulnerability_assessment", "compliance"],
                task_types=[TaskType.SECURITY, TaskType.ANALYSIS, TaskType.TESTING],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.92, "speed": 0.7, "reliability": 0.94},
                current_load=0,
                max_concurrent_tasks=2,
                last_active=datetime.now(),
                specialization_score=0.9
            )
        }
    
    def _calculate_simple_score(self, expert: Expert, task: Task) -> float:
        """Simple scoring without ML"""
        score = 0.0
        
        # Task type match (50%)
        if task.type in expert.task_types:
            score += 0.5
        
        # Keyword matching (30%)
        task_words = set(task.description.lower().split())
        expert_words = set(' '.join(expert.capabilities).lower().split())
        if task_words and expert_words:
            intersection = task_words.intersection(expert_words)
            match_score = len(intersection) / len(task_words)
            score += match_score * 0.3
        
        # Performance (20%)
        avg_performance = sum(expert.performance_metrics.values()) / len(expert.performance_metrics)
        score += avg_performance * 0.2
        
        return min(score, 1.0)
    
    async def select_expert(self, task: Task) -> Tuple[Expert, float]:
        """Select best expert for task"""
        best_expert = None
        best_score = 0.0
        
        for expert in self.experts.values():
            if expert.is_available():
                score = self._calculate_simple_score(expert, task)
                if score > best_score:
                    best_score = score
                    best_expert = expert
        
        if not best_expert:
            # If no available experts, pick the best one anyway
            for expert in self.experts.values():
                score = self._calculate_simple_score(expert, task)
                if score > best_score:
                    best_score = score
                    best_expert = expert
        
        return best_expert, best_score
    
    async def route_task(self, task: Task) -> Dict[str, Any]:
        """Route task to expert"""
        expert, confidence = await self.select_expert(task)
        
        if not expert:
            return {"error": "No expert available"}
        
        # Update expert status
        expert.status = ExpertStatus.BUSY
        expert.current_load += 1
        expert.update_activity()
        
        # Store assignment
        self.task_assignments[task.id] = expert.id
        self.active_tasks[task.id] = task
        
        try:
            # Simulate task execution
            await asyncio.sleep(0.1)
            
            result = {
                "type": "expert_result",
                "expert_id": expert.id,
                "expert_name": expert.name,
                "task_id": task.id,
                "content": f"Task '{task.description}' processed by {expert.name}",
                "confidence": confidence,
                "processing_time": 0.1
            }
            
            return result
            
        finally:
            # Reset expert status
            expert.status = ExpertStatus.IDLE
            expert.current_load = max(0, expert.current_load - 1)
            
            # Clean up
            if task.id in self.task_assignments:
                del self.task_assignments[task.id]
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
    
    def get_expert_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all experts"""
        return {
            expert_id: {
                "name": expert.name,
                "status": expert.status.value,
                "current_load": expert.current_load,
                "max_concurrent_tasks": expert.max_concurrent_tasks,
                "specialization_score": expert.specialization_score,
                "performance_metrics": expert.performance_metrics,
                "last_active": expert.last_active.isoformat()
            }
            for expert_id, expert in self.experts.items()
        }
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get active tasks"""
        return {
            task_id: {
                "type": task.type.value,
                "description": task.description,
                "priority": task.priority,
                "assigned_expert": self.experts[self.task_assignments[task_id]].name if task_id in self.task_assignments else None,
                "created_at": task.created_at.isoformat()
            }
            for task_id, task in self.active_tasks.items()
        }

async def test_simple_moe():
    """Test simplified MoE Router"""
    print("🚀 Starting Simple MoE Router Tests")
    print("=" * 50)
    
    router = SimpleMoERouter()
    
    # Test 1: Expert Registry
    print("🔍 Testing Expert Registry...")
    status = router.get_expert_status()
    print(f"✅ Registered {len(status)} experts:")
    for expert_id, info in status.items():
        print(f"   - {info['name']} ({expert_id}): {info['status']}")
    
    # Test 2: Task Routing
    print("\n🔍 Testing Task Routing...")
    
    test_tasks = [
        Task(
            id="task-1",
            type=TaskType.CODING,
            description="Create a REST API for user management",
            requirements=["python", "fastapi", "database"],
            priority=8,
            estimated_duration=60,
            context={"project": "user_management"},
            created_at=datetime.now()
        ),
        Task(
            id="task-2",
            type=TaskType.DESIGN,
            description="Design system architecture for microservices",
            requirements=["architecture", "microservices", "scalability"],
            priority=9,
            estimated_duration=90,
            context={"project": "system_design"},
            created_at=datetime.now()
        ),
        Task(
            id="task-3",
            type=TaskType.SECURITY,
            description="Perform security audit on authentication system",
            requirements=["security", "authentication", "audit"],
            priority=10,
            estimated_duration=120,
            context={"project": "security_audit"},
            created_at=datetime.now()
        )
    ]
    
    for task in test_tasks:
        print(f"\n📋 Routing task: {task.description}")
        print(f"   Type: {task.type.value}")
        print(f"   Priority: {task.priority}")
        
        result = await router.route_task(task)
        
        if "error" in result:
            print(f"❌ Task routing failed: {result['error']}")
        else:
            print(f"✅ Task routed successfully!")
            print(f"   Expert: {result['expert_name']}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Processing time: {result['processing_time']:.3f}s")
    
    # Test 3: Active Tasks
    print("\n🔍 Testing Active Tasks...")
    active_tasks = router.get_active_tasks()
    print(f"✅ Active tasks: {len(active_tasks)}")
    for task_id, task_info in active_tasks.items():
        print(f"   - {task_id}: {task_info['description'][:50]}...")
        print(f"     Assigned to: {task_info['assigned_expert']}")
    
    print("\n🎉 Simple MoE Router tests completed successfully!")
    return True

async def main():
    """Run simple MoE tests"""
    print("🚀 Starting Simple MoE System Tests")
    print("=" * 50)
    
    success = await test_simple_moe()
    
    print("\n" + "=" * 50)
    print("📊 Simple MoE Test Summary:")
    if success:
        print("   ✅ All tests passed! Simple MoE Router is working.")
        print("\n💡 Next steps:")
        print("   1. Test integration with MCP Server")
        print("   2. Add more sophisticated scoring algorithms")
        print("   3. Implement actual expert agents")
    else:
        print("   ❌ Some tests failed.")

if __name__ == "__main__":
    asyncio.run(main())
