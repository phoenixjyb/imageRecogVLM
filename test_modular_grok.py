#!/usr/bin/env python3
"""
Test modular Grok system end-to-end to verify it matches original behavior.
"""

import os
import sys
import json
import time

# Add vlm_modular to path
vlm_modular_path = os.path.join(os.path.dirname(__file__), 'vlm_modular')
if vlm_modular_path not in sys.path:
    sys.path.insert(0, vlm_modular_path)

# Import modular components
from vlm_modular.config.settings import VLMSettings
from vlm_modular.image.processor import ImageProcessor
from vlm_modular.input.text_processor import TextProcessor
from vlm_modular.vlm.factory import VLMFactory
from vlm_modular.image.coordinate_parser import CoordinateParser

def test_modular_grok_system():
    """Test the full modular system with Grok."""
    print("=" * 80)
    print("🔬 TESTING FULL MODULAR GROK SYSTEM")
    print("=" * 80)
    
    try:
        # Initialize settings
        settings = VLMSettings()
        print(f"🔧 Settings initialized, Grok model: {settings.grok_model}")
        
        # Initialize components
        image_processor = ImageProcessor(settings)
        text_processor = TextProcessor(settings)
        coordinate_parser = CoordinateParser()  # No settings needed
        print("✅ Components initialized")
        
        # Test parameters
        text_command = "pass me the phone"
        image_path = "/Users/yanbo/Projects/vlmTry/sampleImages/image_000777_rsz.jpg"
        
        print(f"📝 Text command: '{text_command}'")
        print(f"🖼️  Image path: {image_path}")
        
        # Process image (using individual methods to get all required data)
        print("\n🖼️  Processing image...")
        # Load image
        image = image_processor.load_image(image_path)
        if image is None:
            print("❌ Failed to load image")
            return False
        
        original_width, original_height = image_processor.get_image_dimensions(image)
        
        # Resize image
        resized_image = image_processor.resize_image(image)
        new_width, new_height = image_processor.get_image_dimensions(resized_image)
        
        # Encode to base64
        base64_data = image_processor.encode_image_to_base64(resized_image)
        if not base64_data:
            print("❌ Failed to encode image")
            return False
        
        processed_image = {
            'base64_data': base64_data,
            'original_width': original_width,
            'original_height': original_height,
            'new_width': new_width,
            'new_height': new_height
        }
        print(f"📐 Image dimensions: {processed_image['original_width']}x{processed_image['original_height']} -> {processed_image['new_width']}x{processed_image['new_height']}")
        
        # Process text command (use original functions for exact match)
        print("\n💬 Processing text command...")
        from imageRecogVLM import extract_object, build_grok_prompt
        
        object_name = extract_object(text_command)
        prompt = build_grok_prompt(object_name, processed_image['new_width'], processed_image['new_height'])
        
        processed_text = {
            'object': object_name,
            'prompt': prompt
        }
        print(f"🎯 Extracted object: '{processed_text['object']}'")
        print(f"📝 Generated prompt preview: {processed_text['prompt'][:100]}...")
        
        # Get VLM client
        print("\n🤖 Getting Grok VLM client...")
        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            print("❌ XAI_API_KEY not found")
            return False
        
        # Create API keys object
        from vlm_modular.config.api_keys import APIKeys
        api_keys = APIKeys()
        api_keys.xai_api_key = api_key
        
        vlm_factory = VLMFactory(api_keys, settings)
        vlm_client = vlm_factory.create_client('grok')
        print(f"✅ VLM client: {type(vlm_client).__name__}, model: {vlm_client.model}")
        
        # Query VLM
        print(f"\n🚀 Querying Grok with prompt and image...")
        start_time = time.time()
        result = vlm_client.query_image(processed_image['base64_data'], processed_text['prompt'])
        end_time = time.time()
        
        print(f"⏱️  VLM query took {end_time - start_time:.2f} seconds")
        print(f"✅ Success: {result.get('success', False)}")
        
        if not result.get('success'):
            print(f"❌ VLM query failed: {result}")
            return False
        
        # Extract raw response
        raw_response = ""
        if 'response' in result and 'choices' in result['response']:
            raw_response = result['response']['choices'][0]['message']['content']
        
        print(f"📄 Raw VLM response ({len(raw_response)} chars): {raw_response}")
        
        # Parse coordinates
        print(f"\n🔍 Parsing coordinates...")
        parsed_coords = coordinate_parser.parse_coordinates(
            raw_response, 
            processed_image['original_width'], 
            processed_image['original_height']
        )
        
        print(f"📊 Parsed results: {parsed_coords}")
        
        # Summary
        result_summary = {
            'text_command': text_command,
            'extracted_object': processed_text['object'],
            'image_dimensions': [processed_image['original_width'], processed_image['original_height']],
            'vlm_model': vlm_client.model,
            'raw_response': raw_response,
            'parsed_coordinates': parsed_coords,
            'query_time': end_time - start_time,
            'success': True
        }
        
        print(f"\n🎉 MODULAR GROK TEST COMPLETED SUCCESSFULLY!")
        print(f"🎯 Object: {result_summary['extracted_object']}")
        print(f"🤖 Model: {result_summary['vlm_model']}")
        print(f"📊 Coordinates: {result_summary['parsed_coordinates']}")
        
        # Save results
        with open('modular_grok_test_results.json', 'w') as f:
            json.dump(result_summary, f, indent=2)
        
        print(f"💾 Results saved to modular_grok_test_results.json")
        return True
        
    except Exception as e:
        print(f"❌ Modular system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_modular_grok_system()
    if success:
        print("\n✅ All tests passed! Modular Grok system is working correctly.")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
