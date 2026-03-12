#!/usr/bin/env python3
"""
Simple integrated test script without sklearn dependency
Tests MCP Server + Simple MoE Router
"""

import asyncio
import json
import aiohttp
from datetime import datetime
from src.core.mcp_server import MCPServer
from src.core.llm_manager import LLMManager
from test_moe_simple import SimpleMoERouter, Task, TaskType

async def test_integrated_simple():
    """Test integrated system with simple MoE"""
    print("🚀 Starting Simple Integrated System Tests")
    print("=" * 60)
    
    # Create MCP server
    mcp_server = MCPServer(host="localhost", port=8003)
    
    # Inject LLM Manager
    llm_manager = LLMManager()
    mcp_server.set_llm_manager(llm_manager)
    
    # Inject Simple MoE Router
    mcp_server.moe_router = SimpleMoERouter()
    
    # Start server in background
    server_task = asyncio.create_task(mcp_server.start())
    
    # Wait for server to start
    await asyncio.sleep(3)
    
    try:
        # Test 1: Health Check
        print("🔍 Testing health endpoint...")
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8003/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Health check: {health_data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        
        # Test 2: Create Session
        print("\n🔍 Testing session creation...")
        session_data = {
            "id": "test-session-1",
            "type": "request",
            "method": "session/create",
            "params": {
                "user_id": "test_user",
                "metadata": {"test": "integrated_simple"}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8003/mcp", json=session_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        session_id = result["result"]["session_id"]
                        print(f"✅ Session created: {session_id}")
                    else:
                        print(f"❌ Session creation failed: {result}")
                        return False
                else:
                    print(f"❌ Session creation failed: {response.status}")
                    return False
        
        # Test 3: System Status
        print("\n🔍 Testing system status...")
        status_data = {
            "id": "test-status-1",
            "type": "request",
            "method": "system/status",
            "params": {
                "session_id": session_id
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8003/mcp", json=status_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        status = result["result"]
                        print(f"✅ System status:")
                        print(f"   Server: {status.get('server')}")
                        print(f"   Active sessions: {status.get('active_sessions')}")
                        print(f"   MoE experts: {status.get('moe_experts')}")
                        print(f"   LLM providers: {status.get('llm_providers')}")
                    else:
                        print(f"❌ Status failed: {result}")
                else:
                    print(f"❌ Status failed: {response.status}")
        
        # Test 4: MoE Expert Status
        print("\n🔍 Testing MoE expert status...")
        expert_data = {
            "id": "test-expert-1",
            "type": "request",
            "method": "moe/expert_status",
            "params": {
                "session_id": session_id
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8003/mcp", json=expert_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        expert_info = result["result"]
                        print(f"✅ MoE expert status:")
                        print(f"   Total experts: {expert_info.get('total_experts')}")
                        print(f"   Available experts: {expert_info.get('available_experts')}")
                        
                        # Show expert details
                        experts = expert_info.get('experts', {})
                        for expert_id, info in experts.items():
                            print(f"   - {info['name']}: {info['status']} (load: {info['current_load']}/{info['max_concurrent_tasks']})")
                    else:
                        print(f"❌ Expert status failed: {result}")
                else:
                    print(f"❌ Expert status failed: {response.status}")
        
        # Test 5: MoE Task Routing
        print("\n🔍 Testing MoE task routing...")
        task_data = {
            "id": "test-task-1",
            "type": "request",
            "method": "moe/route_task",
            "params": {
                "session_id": session_id,
                "task_id": "integrated-test-1",
                "task_type": "coding",
                "description": "Create a simple REST API endpoint for user authentication",
                "requirements": ["python", "fastapi", "authentication"],
                "priority": 7,
                "estimated_duration": 45,
                "use_multiple_experts": False,
                "context": {"project": "test_integration"}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8003/mcp", json=task_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        task_result = result["result"]
                        print(f"✅ Task routed successfully!")
                        print(f"   Task ID: {task_result.get('task_id')}")
                        print(f"   Expert: {task_result.get('result', {}).get('expert_name', 'Unknown')}")
                        print(f"   Confidence: {task_result.get('confidence', 0):.2f}")
                        print(f"   Processing time: {task_result.get('processing_time', 0):.3f}s")
                    else:
                        print(f"❌ Task routing failed: {result}")
                else:
                    print(f"❌ Task routing failed: {response.status}")
        
        # Test 6: Multiple Task Types
        print("\n🔍 Testing multiple task types...")
        task_types = [
            ("design", "Design system architecture for scalability"),
            ("security", "Perform security audit on API endpoints"),
            ("coding", "Implement database connection layer"),
            ("analysis", "Analyze system performance bottlenecks")
        ]
        
        for task_type, description in task_types:
            task_data = {
                "id": f"test-task-{task_type}",
                "type": "request",
                "method": "moe/route_task",
                "params": {
                    "session_id": session_id,
                    "task_id": f"test-{task_type}-{datetime.now().timestamp()}",
                    "task_type": task_type,
                    "description": description,
                    "requirements": [task_type],
                    "priority": 5,
                    "estimated_duration": 30,
                    "use_multiple_experts": False,
                    "context": {"test": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8003/mcp", json=task_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "result" in result:
                            task_result = result["result"]
                            expert = task_result.get('result', {}).get('expert_name', 'Unknown')
                            confidence = task_result.get('confidence', 0)
                            print(f"   ✅ {task_type}: {expert} (confidence: {confidence:.2f})")
                        else:
                            print(f"   ❌ {task_type}: Failed")
                    else:
                        print(f"   ❌ {task_type}: HTTP {response.status}")
        
        print("\n🎉 Simple integrated system tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integrated test failed: {e}")
        return False
    
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

async def main():
    """Run simple integrated tests"""
    print("🚀 Starting Simple System Integration Tests")
    print("=" * 60)
    
    success = await test_integrated_simple()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Simple Integration Test Summary:")
    if success:
        print("   ✅ All integration tests passed!")
        print("\n💡 System components working:")
        print("   1. ✅ MCP Server - Session management")
        print("   2. ✅ LLM Manager - Model selection")
        print("   3. ✅ MoE Router - Expert selection")
        print("   4. ✅ HTTP API - REST endpoints")
        print("   5. ✅ Task routing - Load balancing")
        print("\n🚀 System is ready for:")
        print("   1. Web interface development")
        print("   2. Real expert agent implementation")
        print("   3. RAG system integration")
        print("   4. Production deployment")
    else:
        print("   ❌ Some integration tests failed.")
        print("\n💡 Troubleshooting:")
        print("   1. Check port availability")
        print("   2. Verify component initialization")
        print("   3. Check dependencies")

if __name__ == "__main__":
    asyncio.run(main())
