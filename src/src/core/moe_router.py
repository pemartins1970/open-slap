import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

class ExpertStatus(Enum):
    """Expert status"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

class TaskType(Enum):
    """Task types for expert selection"""
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
    """Expert agent definition"""
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
    specialization_score: float  # 0.0 to 1.0
    
    def update_activity(self):
        self.last_active = datetime.now()
    
    def is_available(self) -> bool:
        return (self.status == ExpertStatus.IDLE and 
                self.current_load < self.max_concurrent_tasks)
    
    def get_load_ratio(self) -> float:
        return self.current_load / self.max_concurrent_tasks

@dataclass
class Task:
    """Task definition"""
    id: str
    type: TaskType
    description: str
    requirements: List[str]
    priority: int  # 1-10
    estimated_duration: int  # minutes
    context: Dict[str, Any]
    created_at: datetime
    
    def get_keywords(self) -> List[str]:
        """Extract keywords from task description"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', self.description.lower())
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        return [word for word in words if word not in stop_words and len(word) > 2]

@dataclass
class ExpertSelection:
    """Expert selection result"""
    expert: Expert
    confidence: float
    reasoning: str
    alternative_experts: List[Tuple[Expert, float]]

@dataclass
class AggregatedResult:
    """Result from multiple experts"""
    primary_result: Dict[str, Any]
    expert_contributions: List[Tuple[str, Dict[str, Any]]]
    confidence_score: float
    aggregation_method: str
    processing_time: float

class ExpertRegistry:
    """Registry of available experts"""
    
    def __init__(self):
        self.experts: Dict[str, Expert] = {}
        self.task_type_mapping: Dict[TaskType, List[str]] = {}
        self._initialize_default_experts()
    
    def _initialize_default_experts(self):
        """Initialize default experts for the project"""
        default_experts = [
            Expert(
                id="architect",
                name="System Architect",
                description="Designs system architecture and makes strategic decisions",
                capabilities=["system_design", "architecture", "planning", "technical_leadership"],
                task_types=[TaskType.DESIGN, TaskType.PLANNING, TaskType.ANALYSIS],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.9, "speed": 0.8, "reliability": 0.95},
                current_load=0,
                max_concurrent_tasks=3,
                last_active=datetime.now(),
                specialization_score=0.85
            ),
            Expert(
                id="backend_dev",
                name="Backend Developer",
                description="Implements APIs, databases, and server-side logic",
                capabilities=["api_development", "database_design", "server_logic", "integration"],
                task_types=[TaskType.CODING, TaskType.DEPLOYMENT, TaskType.DEBUGGING],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.85, "speed": 0.9, "reliability": 0.88},
                current_load=0,
                max_concurrent_tasks=5,
                last_active=datetime.now(),
                specialization_score=0.8
            ),
            Expert(
                id="frontend_dev",
                name="Frontend Developer",
                description="Creates user interfaces and client-side applications",
                capabilities=["ui_development", "user_experience", "frontend_frameworks", "styling"],
                task_types=[TaskType.CODING, TaskType.DESIGN, TaskType.OPTIMIZATION],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.82, "speed": 0.85, "reliability": 0.86},
                current_load=0,
                max_concurrent_tasks=4,
                last_active=datetime.now(),
                specialization_score=0.75
            ),
            Expert(
                id="security_expert",
                name="Security Specialist",
                description="Ensures system security and performs security audits",
                capabilities=["security_analysis", "vulnerability_assessment", "compliance", "encryption"],
                task_types=[TaskType.SECURITY, TaskType.ANALYSIS, TaskType.TESTING],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.92, "speed": 0.7, "reliability": 0.94},
                current_load=0,
                max_concurrent_tasks=2,
                last_active=datetime.now(),
                specialization_score=0.9
            ),
            Expert(
                id="devops_engineer",
                name="DevOps Engineer",
                description="Manages deployment, infrastructure, and operations",
                capabilities=["deployment", "infrastructure", "monitoring", "automation"],
                task_types=[TaskType.DEPLOYMENT, TaskType.OPTIMIZATION, TaskType.PLANNING],
                status=ExpertStatus.IDLE,
                performance_metrics={"accuracy": 0.88, "speed": 0.82, "reliability": 0.9},
                current_load=0,
                max_concurrent_tasks=3,
                last_active=datetime.now(),
                specialization_score=0.78
            )
        ]
        
        for expert in default_experts:
            self.register_expert(expert)
    
    def register_expert(self, expert: Expert):
        """Register a new expert"""
        self.experts[expert.id] = expert
        
        # Update task type mapping
        for task_type in expert.task_types:
            if task_type not in self.task_type_mapping:
                self.task_type_mapping[task_type] = []
            self.task_type_mapping[task_type].append(expert.id)
        
        logger.info(f"Registered expert: {expert.name} ({expert.id})")
    
    def get_expert(self, expert_id: str) -> Optional[Expert]:
        """Get expert by ID"""
        return self.experts.get(expert_id)
    
    def get_experts_by_task_type(self, task_type: TaskType) -> List[Expert]:
        """Get experts that can handle a specific task type"""
        expert_ids = self.task_type_mapping.get(task_type, [])
        return [self.experts[eid] for eid in expert_ids if eid in self.experts]
    
    def get_available_experts(self) -> List[Expert]:
        """Get all available experts"""
        return [expert for expert in self.experts.values() if expert.is_available()]
    
    def update_expert_status(self, expert_id: str, status: ExpertStatus):
        """Update expert status"""
        if expert_id in self.experts:
            self.experts[expert_id].status = status
            self.experts[expert_id].update_activity()
    
    def update_expert_load(self, expert_id: str, load_change: int):
        """Update expert current load"""
        if expert_id in self.experts:
            expert = self.experts[expert_id]
            expert.current_load = max(0, expert.current_load + load_change)
            expert.update_activity()

class ExpertSelector:
    """Selects the best expert for a given task"""
    
    def __init__(self, registry: ExpertRegistry):
        self.registry = registry
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._fit_vectorizer()
    
    def _fit_vectorizer(self):
        """Fit TF-IDF vectorizer on expert descriptions"""
        descriptions = []
        for expert in self.registry.experts.values():
            desc = f"{expert.description} {' '.join(expert.capabilities)}"
            descriptions.append(desc)
        
        if descriptions:
            self.vectorizer.fit(descriptions)
    
    async def select_expert(self, task: Task) -> ExpertSelection:
        """Select the best expert for a task"""
        # Get candidates by task type
        candidates = self.registry.get_experts_by_task_type(task.type)
        
        # Filter by availability
        available_candidates = [e for e in candidates if e.is_available()]
        
        if not available_candidates:
            # If no available experts, consider all candidates
            available_candidates = candidates
        
        if not available_candidates:
            raise ValueError("No experts available for this task type")
        
        # Calculate scores for each candidate
        scored_candidates = []
        for expert in available_candidates:
            score = await self._calculate_expert_score(expert, task)
            scored_candidates.append((expert, score))
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select best expert
        best_expert, best_score = scored_candidates[0]
        
        # Generate reasoning
        reasoning = await self._generate_reasoning(best_expert, task, best_score)
        
        # Get alternatives
        alternatives = [(e, s) for e, s in scored_candidates[1:4]]  # Top 3 alternatives
        
        return ExpertSelection(
            expert=best_expert,
            confidence=best_score,
            reasoning=reasoning,
            alternative_experts=alternatives
        )
    
    async def _calculate_expert_score(self, expert: Expert, task: Task) -> float:
        """Calculate expert score for a task"""
        scores = []
        
        # 1. Task type match (40% weight)
        task_match = 1.0 if task.type in expert.task_types else 0.3
        scores.append(("task_match", task_match, 0.4))
        
        # 2. Capability match (25% weight)
        capability_score = self._calculate_capability_match(expert, task)
        scores.append(("capability", capability_score, 0.25))
        
        # 3. Performance metrics (20% weight)
        performance_score = np.mean(list(expert.performance_metrics.values()))
        scores.append(("performance", performance_score, 0.2))
        
        # 4. Availability (10% weight)
        availability_score = 1.0 - expert.get_load_ratio()
        scores.append(("availability", availability_score, 0.1))
        
        # 5. Specialization (5% weight)
        specialization_score = expert.specialization_score
        scores.append(("specialization", specialization_score, 0.05))
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        
        logger.debug(f"Expert {expert.id} scores: {scores}, total: {total_score}")
        
        return total_score
    
    def _calculate_capability_match(self, expert: Expert, task: Task) -> float:
        """Calculate how well expert capabilities match task requirements"""
        task_keywords = set(task.get_keywords())
        expert_caps = set(cap.lower() for cap in expert.capabilities)
        
        if not task_keywords:
            return 0.5  # Default score if no keywords
        
        # Calculate intersection
        intersection = task_keywords.intersection(expert_caps)
        
        # Jaccard similarity
        union = task_keywords.union(expert_caps)
        jaccard = len(intersection) / len(union) if union else 0
        
        return jaccard
    
    async def _generate_reasoning(self, expert: Expert, task: Task, score: float) -> str:
        """Generate reasoning for expert selection"""
        reasons = []
        
        # Task type match
        if task.type in expert.task_types:
            reasons.append(f"Expert specializes in {task.type.value} tasks")
        
        # Capability match
        cap_match = self._calculate_capability_match(expert, task)
        if cap_match > 0.5:
            reasons.append(f"Strong capability match ({cap_match:.2f})")
        
        # Performance
        avg_performance = np.mean(list(expert.performance_metrics.values()))
        if avg_performance > 0.8:
            reasons.append(f"High performance rating ({avg_performance:.2f})")
        
        # Availability
        if expert.is_available():
            reasons.append("Expert is currently available")
        
        # Specialization
        if expert.specialization_score > 0.8:
            reasons.append(f"Highly specialized ({expert.specialization_score:.2f})")
        
        reasoning = f"Selected {expert.name} with confidence {score:.2f}. "
        if reasons:
            reasoning += "Reasons: " + "; ".join(reasons) + "."
        
        return reasoning

class ResultAggregator:
    """Aggregates results from multiple experts"""
    
    def __init__(self):
        self.aggregation_methods = {
            "best_confidence": self._best_confidence_aggregation,
            "weighted_average": self._weighted_average_aggregation,
            "majority_vote": self._majority_vote_aggregation,
            "consensus": self._consensus_aggregation
        }
    
    async def aggregate_results(self, expert_results, method: str = "best_confidence") -> AggregatedResult:
        """Aggregate results from multiple experts"""
        if method not in self.aggregation_methods:
            raise ValueError(f"Unknown aggregation method: {method}")
        
        start_time = asyncio.get_event_loop().time()
        
        # Apply aggregation method
        aggregation_func = self.aggregation_methods[method]
        primary_result, contributions = await aggregation_func(expert_results)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(expert_results, primary_result)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return AggregatedResult(
            primary_result=primary_result,
            expert_contributions=[(expert.id, result) for expert, result in expert_results],
            confidence_score=confidence,
            aggregation_method=method,
            processing_time=processing_time
        )
    
    async def _best_confidence_aggregation(self, expert_results):
        """Select result from expert with highest confidence"""
        if not expert_results:
            return {}, []
        
        # Sort by expert performance metrics
        sorted_results = sorted(expert_results, 
                             key=lambda x: np.mean(list(x[0].performance_metrics.values())), 
                             reverse=True)
        
        best_expert, best_result = sorted_results[0]
        contributions = [(expert.id, result) for expert, result in expert_results]
        
        return best_result, contributions
    
    async def _weighted_average_aggregation(self, expert_results):
        """Weighted average based on expert performance"""
        if not expert_results:
            return {}, []
        
        contributions = [(expert.id, result) for expert, result in expert_results]
        
        # For now, return the best result (complex aggregation would need result structure)
        best_expert, best_result = max(expert_results, 
                                     key=lambda x: np.mean(list(x[0].performance_metrics.values())))
        
        return best_result, contributions
    
    async def _majority_vote_aggregation(self, expert_results):
        """Majority vote aggregation (simplified)"""
        if not expert_results:
            return {}, []
        
        contributions = [(expert.id, result) for expert, result in expert_results]
        
        # For now, return the most common result type
        result_types = [result.get("type", "unknown") for _, result in expert_results]
        most_common = max(set(result_types), key=result_types.count)
        
        # Find result with most common type
        for expert, result in expert_results:
            if result.get("type") == most_common:
                return result, contributions
        
        # Fallback to first result
        return expert_results[0][1], contributions
    
    async def _consensus_aggregation(self, expert_results):
        """Consensus-based aggregation"""
        if not expert_results:
            return {}, []
        
        contributions = [(expert.id, result) for expert, result in expert_results]
        
        # For now, return result with highest expert consensus
        best_expert, best_result = max(expert_results, 
                                     key=lambda x: x[0].specialization_score)
        
        return best_result, contributions
    
    def _calculate_confidence(self, expert_results, primary_result):
        """Calculate confidence score for aggregated result"""
        if not expert_results:
            return 0.0
        
        # Average expert performance
        avg_performance = np.mean([np.mean(list(expert.performance_metrics.values())) 
                                 for expert, _ in expert_results])
        
        # Number of agreeing experts (simplified)
        agreement_ratio = len(expert_results) / max(len(expert_results), 1)
        
        # Combined confidence
        confidence = (avg_performance * 0.7) + (agreement_ratio * 0.3)
        
        return min(confidence, 1.0)

class MoERouter:
    """Main Mixture of Experts Router"""
    
    def __init__(self):
        self.registry = ExpertRegistry()
        self.selector = ExpertSelector(self.registry)
        self.aggregator = ResultAggregator()
        self.active_tasks: Dict[str, Task] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> expert_id
    
    async def route_task(self, task: Task, use_multiple_experts: bool = False) -> AggregatedResult:
        """Route a task to appropriate expert(s)"""
        logger.info(f"Routing task {task.id} of type {task.type.value}")
        
        # Select primary expert
        selection = await self.selector.select_expert(task)
        
        logger.info(f"Selected expert: {selection.expert.name} (confidence: {selection.confidence:.2f})")
        logger.info(f"Reasoning: {selection.reasoning}")
        
        # Update expert load
        self.registry.update_expert_load(selection.expert.id, 1)
        self.registry.update_expert_status(selection.expert.id, ExpertStatus.BUSY)
        
        # Store task assignment
        self.task_assignments[task.id] = selection.expert.id
        self.active_tasks[task.id] = task
        
        try:
            # Execute task (this would be implemented by actual expert agents)
            if use_multiple_experts and selection.confidence < 0.8:
                # Use multiple experts for low confidence
                expert_results = await self._execute_with_multiple_experts(task, selection)
            else:
                # Use single expert
                result = await self._execute_single_expert(task, selection.expert)
                expert_results = [(selection.expert, result)]
            
            # Aggregate results
            aggregated = await self.aggregator.aggregate_results(expert_results)
            
            logger.info(f"Task {task.id} completed with confidence {aggregated.confidence_score:.2f}")
            
            return aggregated
            
        finally:
            # Update expert load and status
            self.registry.update_expert_load(selection.expert.id, -1)
            self.registry.update_expert_status(selection.expert.id, ExpertStatus.IDLE)
            
            # Clean up task assignment
            if task.id in self.task_assignments:
                del self.task_assignments[task.id]
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
    
    async def _execute_single_expert(self, task: Task, expert: Expert) -> Dict[str, Any]:
        """Execute task with a single expert"""
        # This would be implemented by actual expert agents
        # For now, simulate execution
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "type": "expert_result",
            "expert_id": expert.id,
            "task_id": task.id,
            "content": f"Task {task.id} processed by {expert.name}",
            "confidence": 0.8,
            "processing_time": 0.1
        }
    
    async def _execute_with_multiple_experts(self, task: Task, selection: ExpertSelection):
        """Execute task with multiple experts"""
        experts = [selection.expert] + [expert for expert, _ in selection.alternative_experts[:2]]
        
        # Execute tasks in parallel
        tasks = [self._execute_single_expert(task, expert) for expert in experts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [(expert, result) for expert, result in zip(experts, results) 
                       if not isinstance(result, Exception)]
        
        return valid_results
    
    def get_expert_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all experts"""
        status = {}
        for expert_id, expert in self.registry.experts.items():
            status[expert_id] = {
                "name": expert.name,
                "status": expert.status.value,
                "current_load": expert.current_load,
                "max_concurrent_tasks": expert.max_concurrent_tasks,
                "specialization_score": expert.specialization_score,
                "performance_metrics": expert.performance_metrics,
                "last_active": expert.last_active.isoformat()
            }
        return status
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active tasks"""
        active = {}
        for task_id, task in self.active_tasks.items():
            expert_id = self.task_assignments.get(task_id)
            expert = self.registry.get_expert(expert_id) if expert_id else None
            
            active[task_id] = {
                "type": task.type.value,
                "description": task.description,
                "priority": task.priority,
                "assigned_expert": expert.name if expert else None,
                "created_at": task.created_at.isoformat()
            }
        
        return active

# Usage example
async def main():
    """Test MoE Router"""
    router = MoERouter()
    
    # Create a test task
    task = Task(
        id="task-1",
        type=TaskType.CODING,
        description="Create a REST API for user management",
        requirements=["python", "fastapi", "database"],
        priority=8,
        estimated_duration=60,
        context={"project": "user_management"},
        created_at=datetime.now()
    )
    
    # Route task
    result = await router.route_task(task)
    
    print(f"Task completed: {result.primary_result}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Processing time: {result.processing_time}")
    
    # Get expert status
    status = router.get_expert_status()
    print(f"Expert status: {json.dumps(status, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())
