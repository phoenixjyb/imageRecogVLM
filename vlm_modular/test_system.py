#!/usr/bin/env python3
"""
Test script for the VLM Object Recognition System
"""

import os
import sys
from main import VLMObjectRecognition

def test_system():
    """Test the VLM system components."""
    print("🧪 Testing VLM Object Recognition System")
    print("=" * 50)
    
    try:
        # Initialize system
        print("1. Initializing system...")
        vlm_system = VLMObjectRecognition()
        print("   ✅ System initialized successfully")
        
        # Check system status
        print("\n2. Checking system status...")
        status = vlm_system.get_system_status()
        
        print(f"   Available providers: {status['available_providers']}")
        print(f"   Voice input: {'✅' if status['voice_input_enabled'] else '❌'}")
        print(f"   TTS: {'✅' if status['tts_enabled'] else '❌'}")
        
        # Test individual components
        print("\n3. Testing individual components...")
        
        # Test TTS
        print("   Testing TTS...")
        if vlm_system.tts_handler.is_available():
            success = vlm_system.tts_handler.test_tts()
            print(f"   TTS test: {'✅' if success else '❌'}")
        else:
            print("   TTS test: ❌ (not available)")
        
        # Test voice handler
        print("   Testing voice handler...")
        mic_test = vlm_system.voice_handler.test_microphone()
        print(f"   Microphone test: {'✅' if mic_test else '❌'}")
        
        # Test text processor
        print("   Testing text processor...")
        test_query = vlm_system.text_processor.process_user_query("red car")
        print(f"   Text processing: {'✅' if test_query else '❌'}")
        
        # Test coordinate parser
        print("   Testing coordinate parser...")
        test_coords = vlm_system.coordinate_parser.parse_coordinates("[100, 50, 200, 150]")
        print(f"   Coordinate parsing: {'✅' if test_coords else '❌'}")
        
        print("\n🎉 All tests completed!")
        
        if status['available_providers']:
            print(f"\n💡 You can now run object detection with:")
            print(f"   python main.py")
            print(f"   Available providers: {', '.join(status['available_providers'])}")
        else:
            print(f"\n⚠️  No VLM providers available. Please set your API keys:")
            print(f"   export XAI_API_KEY='your_grok_key'")
            print(f"   export DASHSCOPE_API_KEY='your_qwen_key'")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_system()
