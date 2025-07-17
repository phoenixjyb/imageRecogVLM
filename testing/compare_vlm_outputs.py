#!/usr/bin/env python3
"""
Automated comparison script to test VLM outputs between original and modular implementations.
Compares raw VLM responses for the same input: 'pass me the phone' with Qwen model.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / "vlm_modular"))

def test_original_approach():
    """Test the original imageRecogVLM.py approach and capture raw VLM output."""
    print("=" * 60)
    print("TESTING ORIGINAL APPROACH (imageRecogVLM.py)")
    print("=" * 60)
    
    try:
        # Import from original script
        import imageRecogVLM
        
        # Set up test parameters
        image_path = str(parent_dir / "sampleImages" / "image_000777_rsz.jpg")
        query = "pass me the phone"
        
        print(f"Image: {image_path}")
        print(f"Query: '{query}'")
        print()
        
        # Get image dimensions and encode image
        base64_image, original_width, original_height, new_width, new_height = imageRecogVLM.encode_image(
            image_path, imageRecogVLM.LOCAL_RESIZE_WIDTH
        )
        
        print(f"Image dimensions: {new_width}x{new_height}")
        
        # Extract object name using original function
        object_name = imageRecogVLM.extract_object(query)
        print(f"Extracted object: '{object_name}'")
        
        # Build Qwen prompt using original function
        prompt = imageRecogVLM.build_qwen_prompt(object_name, new_width, new_height)
        print(f"Qwen prompt: {prompt[:200]}...")
        print()
        
        # Call Qwen API using original function
        print("Calling Qwen API...")
        raw_response = imageRecogVLM.call_qwen_api(prompt, image_path, imageRecogVLM.DASHSCOPE_API_KEY)
        
        print("RAW QWEN RESPONSE (Original):")
        print("-" * 40)
        print(raw_response)
        print("-" * 40)
        
        # Parse coordinates using original function
        coordinates, success = imageRecogVLM.parse_response(raw_response, object_name, original_width, original_height, new_width, new_height)
        
        print(f"Parsed coordinates: {coordinates}")
        
        return {
            "approach": "original",
            "image_dimensions": f"{new_width}x{new_height}",
            "extracted_object": object_name,
            "prompt": prompt,
            "raw_response": raw_response,
            "parsed_coordinates": coordinates,
            "success": True
        }
        
    except Exception as e:
        print(f"ERROR in original approach: {e}")
        import traceback
        traceback.print_exc()
        return {
            "approach": "original",
            "error": str(e),
            "success": False
        }

def test_modular_approach():
    """Test the modular vlm_modular/main.py approach and capture raw VLM output."""
    print()
    print("=" * 60)
    print("TESTING MODULAR APPROACH (vlm_modular/main.py)")
    print("=" * 60)
    
    try:
        # Add modular path for imports
        modular_path = current_dir / "vlm_modular"
        if str(modular_path) not in sys.path:
            sys.path.insert(0, str(modular_path))
        
        # Import from modular system
        from vlm_modular.config.settings import VLMSettings
        from vlm_modular.config.api_keys import APIKeys
        from vlm_modular.input.text_processor import TextProcessor
        from vlm_modular.vlm.factory import VLMFactory
        from vlm_modular.image.processor import ImageProcessor
        from vlm_modular.image.coordinate_parser import CoordinateParser
        
        # Set up test parameters
        image_path = str(parent_dir / "sampleImages" / "image_000777_rsz.jpg")
        query = "pass me the phone"
        
        print(f"Image: {image_path}")
        print(f"Query: '{query}'")
        print()
        
        # Initialize components
        settings = VLMSettings.load_from_env()
        api_keys = APIKeys()
        text_processor = TextProcessor(settings)
        vlm_factory = VLMFactory(api_keys, settings)
        image_processor = ImageProcessor(settings)
        coordinate_parser = CoordinateParser()
        
        # Process query
        processed_query = text_processor.process_user_query(query)
        object_name = text_processor.extract_object_name(query)
        print(f"Extracted object: '{object_name}'")
        
        # Process image
        image_result = image_processor.load_and_prepare_image(image_path)
        if not image_result:
            raise Exception("Failed to load image")
        
        image, base64_image = image_result
        print(f"Image dimensions: {settings.image_output_width}x{settings.image_output_height}")
        
        # Create VLM prompt
        prompt = text_processor.create_vlm_prompt(object_name, "qwen")
        print(f"Qwen prompt: {prompt[:200]}...")
        print()
        
        # Get VLM client and query
        vlm_client = vlm_factory.create_client("qwen")
        
        print("Calling Qwen API...")
        vlm_response = vlm_client.query_image(base64_image, prompt)
        
        # Extract the actual response text from the complex response structure
        raw_response_text = ""
        actual_qwen_response = ""
        if isinstance(vlm_response, dict):
            # Check the modular response structure - now it should have simple 'response' field
            if 'response' in vlm_response:
                actual_qwen_response = vlm_response['response']
            
            # For comparison, show the full response as raw_response_text
            raw_response_text = str(vlm_response)
        else:
            raw_response_text = str(vlm_response)
            actual_qwen_response = raw_response_text
        
        print("RAW QWEN RESPONSE (Modular - Full Structure):")
        print("-" * 40)
        print(raw_response_text[:500] + "..." if len(raw_response_text) > 500 else raw_response_text)
        print("-" * 40)
        print("ACTUAL QWEN TEXT RESPONSE:")
        print("-" * 40)
        print(actual_qwen_response)
        print("-" * 40)
        
        # Parse objects from VLM response
        objects = vlm_client.parse_response(vlm_response)
        print(f"VLM client parsed objects: {len(objects)}")
        
        # Additional coordinate parsing
        additional_objects = coordinate_parser.parse_coordinates(
            actual_qwen_response,  # Use the actual text response, not the full structure
            settings.image_output_width, 
            settings.image_output_height
        )
        print(f"Additional parsed objects: {len(additional_objects)}")
        
        all_objects = objects + additional_objects
        
        return {
            "approach": "modular",
            "image_dimensions": f"{settings.image_output_width}x{settings.image_output_height}",
            "extracted_object": object_name,
            "prompt": prompt,
            "raw_response": actual_qwen_response,  # Return just the actual text response for comparison
            "full_response": raw_response_text,    # Keep full response for debugging
            "vlm_parsed_objects": len(objects),
            "additional_parsed_objects": len(additional_objects),
            "total_objects": len(all_objects),
            "success": True
        }
        
    except Exception as e:
        print(f"ERROR in modular approach: {e}")
        import traceback
        traceback.print_exc()
        return {
            "approach": "modular",
            "error": str(e),
            "success": False
        }

def compare_results(original_result, modular_result):
    """Compare the results from both approaches."""
    print()
    print("=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)
    
    if not original_result.get('success') or not modular_result.get('success'):
        print("❌ One or both approaches failed - cannot compare")
        return
    
    print("✅ Both approaches completed successfully")
    print()
    
    # Compare extracted objects
    orig_obj = original_result.get('extracted_object', '')
    mod_obj = modular_result.get('extracted_object', '')
    print(f"Object Extraction:")
    print(f"  Original: '{orig_obj}'")
    print(f"  Modular:  '{mod_obj}'")
    print(f"  Match: {'✅' if orig_obj == mod_obj else '❌'}")
    print()
    
    # Compare image dimensions
    orig_dims = original_result.get('image_dimensions', '')
    mod_dims = modular_result.get('image_dimensions', '')
    print(f"Image Dimensions:")
    print(f"  Original: {orig_dims}")
    print(f"  Modular:  {mod_dims}")
    print(f"  Match: {'✅' if orig_dims == mod_dims else '❌'}")
    print()
    
    # Compare prompts
    orig_prompt = original_result.get('prompt', '')
    mod_prompt = modular_result.get('prompt', '')
    print(f"Prompts:")
    print(f"  Original: {orig_prompt[:100]}...")
    print(f"  Modular:  {mod_prompt[:100]}...")
    print(f"  Match: {'✅' if orig_prompt == mod_prompt else '❌'}")
    print()
    
    # Compare raw responses
    orig_response = original_result.get('raw_response', '')
    mod_response = modular_result.get('raw_response', '')
    print(f"Raw VLM Responses:")
    print(f"  Original length: {len(orig_response)} chars")
    print(f"  Modular length:  {len(mod_response)} chars")
    
    # Check if responses contain similar coordinate patterns
    orig_has_coords = '|' in orig_response and any(char.isdigit() for char in orig_response)
    mod_has_coords = '|' in mod_response and any(char.isdigit() for char in mod_response)
    print(f"  Both contain coordinates: {'✅' if orig_has_coords and mod_has_coords else '❌'}")
    
    if orig_response == mod_response:
        print(f"  Exact match: ✅")
    else:
        print(f"  Exact match: ❌ (Expected - VLM responses can vary)")
        print()
        print("Original response:")
        print(f"  {repr(orig_response[:200])}...")
        print("Modular response:")
        print(f"  {repr(mod_response[:200])}...")

def main():
    """Main test function."""
    print("VLM Output Comparison Test")
    print("Testing: 'pass me the phone' with Qwen model")
    print("Image: sampleImages/image_000777_rsz.jpg")
    print()
    
    # Test both approaches
    original_result = test_original_approach()
    modular_result = test_modular_approach()
    
    # Compare results
    compare_results(original_result, modular_result)
    
    # Save results to file
    results = {
        "test_query": "pass me the phone",
        "test_model": "qwen",
        "test_image": "sampleImages/image_000777_rsz.jpg",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "original": original_result,
        "modular": modular_result
    }
    
    with open('vlm_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("=" * 60)
    print("Test completed! Results saved to: vlm_comparison_results.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
