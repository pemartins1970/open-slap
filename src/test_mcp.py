#!/usr/bin/env python3
"""
Test script for MCP Server
Run this to verify the MCP system is working
"""

import asyncio
import json
import aiohttp
from src.core.mcp_server import MCPServer
from src.core.llm_manager import LLMManager

async def test_mcp_server():
    """Test MCP Server functionality"""
    print("🚀 Starting MCP Server Tests")
    print("=" * 50)
    
    # Create MCP server and LLM manager
    mcp_server = MCPServer(host="localhost", port=8001)  # Different port for testing
    llm_manager = LLMManager()
    mcp_server.set_llm_manager(llm_manager)
    
    # Start server in background
    server_task = asyncio.create_task(mcp_server.start())
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Health check: {health_data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        
        # Test MCP message via HTTP
        print("\n🔍 Testing MCP message handling...")
        
        # Create session
        session_data = {
            "id": "test-1",
            "type": "request",
            "method": "session/create",
            "params": {
                "user_id": "test_user",
                "metadata": {"test": True}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8001/mcp", json=session_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Session created: {result.get('session_id')}")
                    session_id = result.get('session_id')
                else:
                    print(f"❌ Session creation failed: {response.status}")
                    return False
        
        # Test message sending
        print("\n🔍 Testing message sending...")
        message_data = {
            "id": "test-2",
            "type": "request",
            "method": "message/send",
            "params": {
                "session_id": session_id,
                "message": "Hello! Please respond with a short greeting.",
                "provider": "ollama"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8001/mcp", json=message_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        print(f"✅ Message response: {result['result'].get('content', '')[:100]}...")
                    else:
                        print(f"❌ Message failed: {result}")
                else:
                    print(f"❌ Message sending failed: {response.status}")
                    return False
        
        # Test system status
        print("\n🔍 Testing system status...")
        status_data = {
            "id": "test-3",
            "type": "request",
            "method": "system/status",
            "params": {
                "session_id": session_id
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8001/mcp", json=status_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        status = result['result']
                        print(f"✅ System status: {status.get('server')}")
                        print(f"   Active sessions: {status.get('active_sessions')}")
                        print(f"   LLM providers: {status.get('llm_providers')}")
                    else:
                        print(f"❌ Status failed: {result}")
                else:
                    print(f"❌ Status check failed: {response.status}")
                    return False
        
        print("\n🎉 MCP Server tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        return False
    
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

async def test_websocket_connection():
    """Test WebSocket connection"""
    print("\n🔍 Testing WebSocket connection...")
    
    try:
        import websockets
        
        uri = "ws://localhost:8001/ws"
        async with websockets.connect(uri) as websocket:
            # Send session creation message
            session_msg = {
                "id": "ws-test-1",
                "type": "request",
                "method": "session/create",
                "params": {"user_id": "ws_user"}
            }
            
            await websocket.send(json.dumps(session_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            if "result" in result:
                print(f"✅ WebSocket session created: {result['result'].get('session_id')}")
                return True
            else:
                print(f"❌ WebSocket session failed: {result}")
                return False
                
    except ImportError:
        print("⚠️  websockets library not installed, skipping WebSocket test")
        return True
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

async def test_session_management():
    """Test session management functionality"""
    print("\n🔍 Testing session management...")
    
    from src.core.mcp_server import SessionManager
    
    manager = SessionManager()
    
    # Create session
    session = manager.create_session("test_user", {"test": True})
    print(f"✅ Session created: {session.id}")
    
    # Get session
    retrieved = manager.get_session(session.id)
    if retrieved and retrieved.id == session.id:
        print(f"✅ Session retrieved successfully")
    else:
        print(f"❌ Session retrieval failed")
        return False
    
    # Update session
    success = manager.update_session(session.id, metadata={"updated": True})
    if success:
        print(f"✅ Session updated successfully")
    else:
        print(f"❌ Session update failed")
        return False
    
    # Delete session
    success = manager.delete_session(session.id)
    if success:
        print(f"✅ Session deleted successfully")
    else:
        print(f"❌ Session deletion failed")
        return False
    
    return True

async def test_context_management():
    """Test context management functionality"""
    print("\n🔍 Testing context management...")
    
    from src.core.mcp_server import ContextManager
    
    manager = ContextManager("test_storage/contexts")
    
    # Create context
    context = manager.create_context("test_session", project_id="test_project")
    print(f"✅ Context created for session: {context.session_id}")
    
    # Update context
    success = manager.update_context(
        "test_session",
        working_directory="/test/path",
        environment_vars={"TEST": "value"}
    )
    if success:
        print(f"✅ Context updated successfully")
    else:
        print(f"❌ Context update failed")
        return False
    
    # Add to history
    manager.add_to_history("test_session", {
        "role": "user",
        "content": "Test message"
    })
    print(f"✅ Message added to history")
    
    # Get context
    retrieved = manager.get_context("test_session")
    if retrieved and len(retrieved.conversation_history) > 0:
        print(f"✅ Context retrieved with {len(retrieved.conversation_history)} messages")
    else:
        print(f"❌ Context retrieval failed")
        return False
    
    return True

async def main():
    """Run all MCP tests"""
    print("🚀 Starting MCP System Tests")
    print("=" * 50)
    
    results = []
    
    # Test individual components
    results.append(await test_session_management())
    results.append(await test_context_management())
    results.append(await test_mcp_server())
    results.append(await test_websocket_connection())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 MCP Test Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All MCP tests passed! Server is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Start MCP server: python -m src.core.mcp_server")
        print("   2. Connect via HTTP: http://localhost:8000/health")
        print("   3. Connect via WebSocket: ws://localhost:8000/ws")
    else:
        print("⚠️  Some MCP tests failed. Check the output above for details.")
        print("\n💡 Troubleshooting:")
        print("   1. Check if ports 8000/8001 are available")
        print("   2. Verify all dependencies are installed")
        print("   3. Check LLM Manager is working")

if __name__ == "__main__":
    asyncio.run(main())
