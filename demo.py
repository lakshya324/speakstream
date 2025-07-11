#!/usr/bin/env python3
"""
Demo script to test SpeakStream components
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_llm_handler():
    """Test LLM functionality"""
    try:
        print("🔧 Testing LLM Handler...")
        from models.llm_handler import LLMHandler
        
        llm = LLMHandler()
        await llm.initialize()
        
        print("📝 Generating test response...")
        response = await llm.generate_complete("Hello, how are you?", max_new_tokens=50)
        print(f"✅ LLM Response: {response[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ LLM Test failed: {e}")
        return False

async def test_tts_handler():
    """Test TTS functionality"""
    try:
        print("🔧 Testing TTS Handler...")
        from models.tts_handler import TTSHandler
        
        tts = TTSHandler()
        await tts.initialize()
        
        print("🔊 Generating test audio...")
        audio_data = await tts.synthesize_text("Hello, this is a test.")
        
        if audio_data:
            print(f"✅ TTS Response: {len(audio_data)} bytes base64 audio")
            return True
        else:
            print("❌ TTS returned empty audio")
            return False
            
    except Exception as e:
        print(f"❌ TTS Test failed: {e}")
        return False

async def test_integration():
    """Test integrated LLM + TTS"""
    try:
        print("🔧 Testing Integration...")
        from models.llm_handler import LLMHandler
        from models.tts_handler import TTSHandler
        
        llm = LLMHandler()
        tts = TTSHandler()
        
        await llm.initialize()
        await tts.initialize()
        
        print("🎭 Running integrated test...")
        
        # Generate text stream
        text_stream = llm.generate_stream("Tell me a joke.", max_new_tokens=50)
        
        # Process through TTS
        audio_stream = tts.synthesize_stream(text_stream)
        
        chunk_count = 0
        async for chunk in audio_stream:
            chunk_count += 1
            if chunk.get("type") == "text":
                print(f"📝 Text chunk {chunk_count}: {chunk.get('data', '')}", end="", flush=True)
            elif chunk.get("type") == "audio":
                print(f"\n🔊 Audio chunk {chunk_count}: {len(chunk.get('data', ''))} bytes")
        
        print(f"\n✅ Integration test completed with {chunk_count} chunks")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Main demo function"""
    print("🎉 SpeakStream Demo Test")
    print("=" * 50)
    
    tests = [
        ("LLM Handler", test_llm_handler),
        ("TTS Handler", test_tts_handler),
        ("Integration", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print(f"\n⏹️ Test {test_name} interrupted by user")
            break
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! SpeakStream is ready to use.")
        print("💡 Run: python backend/main.py to start the server")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\n💥 Demo crashed: {e}")
        sys.exit(1)
