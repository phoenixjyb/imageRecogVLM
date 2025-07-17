#!/usr/bin/env python3
"""
Compare Grok outputs between original and modular approaches.
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Add paths for imports
parent_dir = os.path.dirname(os.path.dirname(__file__))
vlm_modular_path = os.path.join(parent_dir, 'vlm_modular')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if vlm_modular_path not in sys.path:
    sys.path.insert(0, vlm_modular_path)

# Import original functions
from imageRecogVLM import (
    call_grok4_api, 
    build_grok_prompt,
    encode_image,
    extract_object
)

# Import modular approach
from vlm_modular.vlm.factory import VLMFactory
from vlm_modular.vlm.grok_client import GrokClient
from vlm_modular.image.processor import ImageProcessor

def test_grok_original_approach(text_command: str, image_path: str):
    """Test the original Grok approach."""
    print("=" * 60)
    print("🔍 TESTING ORIGINAL GROK APPROACH")
    print("=" * 60)
    
    try:
        # Extract object
        object_str = extract_object(text_command)
        print(f"📝 Extracted object: '{object_str}'")
        
        # Get image dimensions
        _, original_width, original_height, new_width, new_height = encode_image(image_path)
        print(f"📐 Image dimensions: {original_width}x{original_height} -> {new_width}x{new_height}")
        
        # Build prompt
        prompt = build_grok_prompt(object_str, new_width, new_height)
        print(f"💬 Prompt: {prompt[:100]}...")
        
        # Get API key
        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            print("❌ XAI_API_KEY not found")
            return None
        
        # Call API
        print("\n🚀 Calling original Grok API...")
        start_time = time.time()
        raw_response = call_grok4_api(prompt, image_path, api_key)
        end_time = time.time()
        
        print(f"⏱️  API call took {end_time - start_time:.2f} seconds")
        print(f"📄 Raw response length: {len(raw_response)} characters")
        print(f"📄 Raw response preview:\n{raw_response[:500]}...")
        
        return {
            'object': object_str,
            'prompt': prompt,
            'raw_response': raw_response,
            'api_time': end_time - start_time,
            'image_dimensions': {
                'original': [original_width, original_height],
                'processed': [new_width, new_height]
            }
        }
        
    except Exception as e:
        print(f"❌ Original approach failed: {e}")
        return None

def test_grok_modular_approach(text_command: str, image_path: str):
    """Test the modular Grok approach."""
    print("=" * 60)
    print("🔍 TESTING MODULAR GROK APPROACH")
    print("=" * 60)
    
    try:
        # Process image
        image_processor = ImageProcessor()
        processed_image = image_processor.process_image(image_path)
        print(f"📐 Image processed: {processed_image['original_width']}x{processed_image['original_height']} -> {processed_image['new_width']}x{processed_image['new_height']}")
        
        # Get VLM client
        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            print("❌ XAI_API_KEY not found")
            return None
            
        vlm_factory = VLMFactory()
        vlm_client = vlm_factory.get_client('grok', api_key)
        print(f"🤖 VLM client: {type(vlm_client).__name__}")
        
        # Build prompt (using the same function as original)
        object_str = extract_object(text_command)
        prompt = build_grok_prompt(object_str, processed_image['new_width'], processed_image['new_height'])
        print(f"📝 Extracted object: '{object_str}'")
        print(f"💬 Prompt: {prompt[:100]}...")
        
        # Query VLM
        print("\n🚀 Calling modular Grok API...")
        start_time = time.time()
        result = vlm_client.query_image(processed_image['base64_data'], prompt)
        end_time = time.time()
        
        print(f"⏱️  API call took {end_time - start_time:.2f} seconds")
        print(f"✅ Success: {result.get('success', False)}")
        
        # Extract raw response
        raw_response = ""
        if result.get('success') and 'response' in result:
            response_data = result['response']
            if 'choices' in response_data and response_data['choices']:
                raw_response = response_data['choices'][0].get('message', {}).get('content', '')
        
        print(f"📄 Raw response length: {len(raw_response)} characters")
        print(f"📄 Raw response preview:\n{raw_response[:500]}...")
        
        return {
            'object': object_str,
            'prompt': prompt,
            'raw_response': raw_response,
            'api_time': end_time - start_time,
            'result': result,
            'image_dimensions': {
                'original': [processed_image['original_width'], processed_image['original_height']],
                'processed': [processed_image['new_width'], processed_image['new_height']]
            }
        }
        
    except Exception as e:
        print(f"❌ Modular approach failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_grok_outputs(text_command: str, image_path: str):
    """Compare Grok outputs from both approaches."""
    print("\n" + "=" * 80)
    print("🔬 GROK COMPARISON TEST")
    print("=" * 80)
    print(f"📝 Text command: '{text_command}'")
    print(f"🖼️  Image path: {image_path}")
    
    # Test original approach
    original_result = test_grok_original_approach(text_command, image_path)
    
    print("\n")
    
    # Test modular approach
    modular_result = test_grok_modular_approach(text_command, image_path)
    
    # Compare results
    print("\n" + "=" * 60)
    print("📊 COMPARISON RESULTS")
    print("=" * 60)
    
    if original_result is None or modular_result is None:
        print("❌ Cannot compare - one or both approaches failed")
        return
    
    # Compare prompts
    print(f"🔍 Prompts match: {original_result['prompt'] == modular_result['prompt']}")
    if original_result['prompt'] != modular_result['prompt']:
        print("   ⚠️  Prompt differences detected!")
        print(f"   Original: {original_result['prompt'][:100]}...")
        print(f"   Modular:  {modular_result['prompt'][:100]}...")
    
    # Compare objects
    print(f"🎯 Objects match: {original_result['object'] == modular_result['object']}")
    
    # Compare image dimensions
    orig_dims = original_result['image_dimensions']
    mod_dims = modular_result['image_dimensions']
    print(f"📐 Image dimensions match: {orig_dims == mod_dims}")
    
    # Compare response lengths
    orig_len = len(original_result['raw_response'])
    mod_len = len(modular_result['raw_response'])
    print(f"📄 Response lengths: Original={orig_len}, Modular={mod_len}")
    
    # Compare response content similarity
    if orig_len > 0 and mod_len > 0:
        orig_resp = original_result['raw_response']
        mod_resp = modular_result['raw_response']
        
        # Simple comparison
        responses_identical = orig_resp == mod_resp
        print(f"📋 Responses identical: {responses_identical}")
        
        if not responses_identical:
            print("\n🔍 Response Differences:")
            print("📋 Original response:")
            print(orig_resp[:300] + "..." if len(orig_resp) > 300 else orig_resp)
            print("\n📋 Modular response:")
            print(mod_resp[:300] + "..." if len(mod_resp) > 300 else mod_resp)
    
    # Save comparison results
    comparison_data = {
        'test_info': {
            'text_command': text_command,
            'image_path': image_path,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'original': original_result,
        'modular': modular_result,
        'comparison': {
            'prompts_match': original_result['prompt'] == modular_result['prompt'],
            'objects_match': original_result['object'] == modular_result['object'],
            'dimensions_match': orig_dims == mod_dims,
            'responses_identical': original_result['raw_response'] == modular_result['raw_response']
        }
    }
    
    output_file = 'grok_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    print(f"\n💾 Comparison results saved to {output_file}")

if __name__ == "__main__":
    # Test with the same inputs as before
    text_command = "pass me the phone"
    image_path = os.path.join(parent_dir, "sampleImages", "image_000777_rsz.jpg")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        exit(1)
    
    compare_grok_outputs(text_command, image_path)
