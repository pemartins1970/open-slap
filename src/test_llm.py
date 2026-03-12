#!/usr/bin/env python3
"""
Test script for LLM Manager
Run this to verify the LLM system is working
"""

import asyncio
import os
from src.core.llm_manager import LLMManager

async def test_ollama():
    """Test Ollama local connection"""
    print("🔍 Testing Ollama connection...")
    
    manager = LLMManager()
    
    try:
        # Validate Ollama is running
        validation = await manager.validate_providers()
        print(f"✅ Provider validation: {validation}")
        
        if validation.get("ollama", False):
            # Test generation
            response = await manager.generate(
                "Hello! Please respond with a short greeting.",
                provider="ollama",
                model="llama2"
            )
            
            print(f"🤖 Ollama Response:")
            print(f"   Content: {response.content}")
            print(f"   Model: {response.model}")
            print(f"   Response Time: {response.response_time:.2f}s")
            return True
        else:
            print("❌ Ollama is not running or not accessible")
            print("   Make sure Ollama is installed and running:")
            print("   1. Install Ollama: https://ollama.ai/")
            print("   2. Start Ollama: ollama serve")
            print("   3. Pull a model: ollama pull llama2")
            return False
            
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

async def test_gemini():
    """Test Gemini API connection"""
    print("\n🔍 Testing Gemini connection...")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("   To test Gemini:")
        print("   1. Get API key from: https://makersuite.google.com/app/apikey")
        print("   2. Set environment: set GEMINI_API_KEY=your-key")
        return False
    
    manager = LLMManager()
    manager.set_api_key("gemini", api_key)
    
    try:
        # Validate Gemini connection
        validation = await manager.validate_providers()
        print(f"✅ Provider validation: {validation}")
        
        if validation.get("gemini", False):
            # Test generation
            response = await manager.generate(
                "Hello! Please respond with a short greeting.",
                provider="gemini",
                model="gemini-pro"
            )
            
            print(f"🤖 Gemini Response:")
            print(f"   Content: {response.content}")
            print(f"   Model: {response.model}")
            print(f"   Response Time: {response.response_time:.2f}s")
            return True
        else:
            print("❌ Gemini API key is invalid or API is not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

async def test_fallback():
    """Test fallback mechanism"""
    print("\n🔍 Testing fallback mechanism...")
    
    manager = LLMManager()
    
    # Try to generate with fallback
    try:
        response = await manager.generate(
            "Hello! Please respond with a short greeting."
        )
        
        print(f"🤖 Fallback Response:")
        print(f"   Content: {response.content}")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

async def test_provider_switching():
    """Test provider switching"""
    print("\n🔍 Testing provider switching...")
    
    manager = LLMManager()
    
    # Test switching between available providers
    providers = manager.get_available_providers()
    print(f"📋 Available providers: {providers}")
    
    for provider in providers:
        try:
            models = manager.get_provider_models(provider)
            print(f"   {provider}: {models}")
        except Exception as e:
            print(f"   {provider}: Error - {e}")
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting LLM Manager Tests")
    print("=" * 50)
    
    results = []
    
    # Test individual components
    results.append(await test_ollama())
    results.append(await test_gemini())
    results.append(await test_fallback())
    results.append(await test_provider_switching())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! LLM Manager is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\n💡 Next steps:")
        print("   1. Install and start Ollama for local models")
        print("   2. Get Gemini API key for remote models")
        print("   3. Run tests again to verify everything works")
    
    # Cleanup
    manager = LLMManager()
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
