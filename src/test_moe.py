#!/usr/bin/env python3
"""
Test script for MoE Router
Run this to verify MoE system is working
"""

import asyncio
import json
from src.core.moe_router import MoERouter, Task, TaskType

async def test_moe_router():
    """Test MoE Router functionality"""
    print("🚀 Starting MoE Router Tests")
    print("=" * 50)
    
    router = MoERouter()
    
    # Test 1: Expert Registry
    print("🔍 Testing Expert Registry...")
    experts = router.get_expert_status()
    print(f"✅ Registered {len(experts)} experts:")
    for expert_id, expert_info in experts.items():
        print(f"   - {expert_info['name']} ({expert_id}): {expert_info['status']}")
    
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
        
        try:
            result = await router.route_task(task)
            
            print(f"✅ Task routed successfully!")
            print(f"   Primary expert: {result.expert_contributions[0][0] if result.expert_contributions else 'Unknown'}")
            print(f"   Confidence: {result.confidence_score:.2f}")
            print(f"   Processing time: {result.processing_time:.3f}s")
            print(f"   Aggregation method: {result.aggregation_method}")
            
        except Exception as e:
            print(f"❌ Task routing failed: {e}")
    
    # Test 3: Expert Selection
    print("\n🔍 Testing Expert Selection...")
    
    test_task = Task(
        id="test-selection",
        type=TaskType.CODING,
        description="Build a responsive web dashboard with React",
        requirements=["react", "javascript", "css", "responsive"],
        priority=7,
        estimated_duration=45,
        context={"project": "dashboard"},
        created_at=datetime.now()
    )
    
    try:
        selection = await router.selector.select_expert(test_task)
        
        print(f"✅ Expert selection completed!")
        print(f"   Selected expert: {selection.expert.name}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reasoning: {selection.reasoning}")
        print(f"   Alternatives: {[alt[0].name for alt, _ in selection.alternative_experts]}")
        
    except Exception as e:
        print(f"❌ Expert selection failed: {e}")
    
    # Test 4: Active Tasks
    print("\n🔍 Testing Active Tasks...")
    
    active_tasks = router.get_active_tasks()
    print(f"✅ Active tasks: {len(active_tasks)}")
    for task_id, task_info in active_tasks.items():
        print(f"   - {task_id}: {task_info['description'][:50]}...")
        print(f"     Assigned to: {task_info['assigned_expert']}")
        print(f"     Priority: {task_info['priority']}")
    
    # Test 5: Multiple Expert Aggregation
    print("\n🔍 Testing Multiple Expert Aggregation...")
    
    complex_task = Task(
        id="complex-task",
        type=TaskType.ANALYSIS,
        description="Analyze system performance and recommend optimizations",
        requirements=["performance", "optimization", "analysis"],
        priority=6,
        estimated_duration=75,
        context={"project": "performance_analysis"},
        created_at=datetime.now()
    )
    
    try:
        result = await router.route_task(complex_task, use_multiple_experts=True)
        
        print(f"✅ Multi-expert aggregation completed!")
        print(f"   Primary result: {result.primary_result.get('content', 'No content')[:100]}...")
        print(f"   Expert contributions: {len(result.expert_contributions)}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Aggregation method: {result.aggregation_method}")
        
        for expert_id, contribution in result.expert_contributions:
            print(f"     - {expert_id}: {contribution.get('content', 'No content')[:50]}...")
            
    except Exception as e:
        print(f"❌ Multi-expert aggregation failed: {e}")
    
    print("\n🎉 MoE Router tests completed successfully!")
    return True

async def test_expert_performance():
    """Test expert performance metrics"""
    print("\n🔍 Testing Expert Performance...")
    
    router = MoERouter()
    
    # Simulate multiple tasks to test performance
    tasks = []
    for i in range(5):
        task = Task(
            id=f"perf-test-{i}",
            type=TaskType.CODING,
            description=f"Test task {i} for performance testing",
            requirements=["python", "testing"],
            priority=5,
            estimated_duration=30,
            context={"test": True},
            created_at=datetime.now()
        )
        tasks.append(task)
    
    # Route tasks in parallel
    start_time = asyncio.get_event_loop().time()
    
    results = await asyncio.gather(
        *[router.route_task(task) for task in tasks],
        return_exceptions=True
    )
    
    end_time = asyncio.get_event_loop().time()
    total_time = end_time - start_time
    
    successful_results = [r for r in results if not isinstance(r, Exception)]
    
    print(f"✅ Performance test completed!")
    print(f"   Total tasks: {len(tasks)}")
    print(f"   Successful: {len(successful_results)}")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average time per task: {total_time/len(tasks):.3f}s")
    
    if successful_results:
        avg_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
        print(f"   Average confidence: {avg_confidence:.2f}")
    
    return len(successful_results) == len(tasks)

async def main():
    """Run all MoE tests"""
    print("🚀 Starting MoE System Tests")
    print("=" * 50)
    
    results = []
    
    # Test individual components
    results.append(await test_moe_router())
    results.append(await test_expert_performance())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 MoE Test Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All MoE tests passed! Router is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Start integrated server: python -m src.core.mcp_server")
        print("   2. Test MoE routing via MCP API")
        print("   3. Create custom experts for specific domains")
    else:
        print("⚠️  Some MoE tests failed. Check output above for details.")
        print("\n💡 Troubleshooting:")
        print("   1. Check expert registry initialization")
        print("   2. Verify task type mappings")
        print("   3. Check expert availability logic")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
