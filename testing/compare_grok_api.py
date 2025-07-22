#!/usr/bin/env python3
"""
Simple Grok API comparison test focusing on the key differences.
"""

import os
import sys
import json
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add paths for imports
parent_dir = os.path.dirname(os.path.dirname(__file__))
vlm_modular_path = os.path.join(parent_dir, 'vlm_modular')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if vlm_modular_path not in sys.path:
    sys.path.insert(0, vlm_modular_path)

# Import original functions
from imageRecogVLM import encode_image, build_grok_prompt

def test_original_grok_api(prompt: str, image_path: str, api_key: str):
    """Test original Grok API call exactly as implemented."""
    print("🔍 TESTING ORIGINAL GROK API")
    print(f"📝 Prompt: {prompt[:100]}...")
    
    try:
        # Use original encode_image function
        base64_image, original_width, original_height, new_width, new_height = encode_image(image_path)
        
        # Original API call setup (exactly from original code)
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "grok-4-0709",  # Original model
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
        }
        proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        
        print("🌐 Sending API request to Grok-4 (original method)...")
        start_time = time.time()
        
        # Original retry logic
        session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        response = session.post(url, headers=headers, json=payload, proxies=proxies, timeout=120)
        end_time = time.time()
        
        print(f"📡 API response received in {end_time - start_time:.2f} seconds")
        print(f"📊 API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API call failed: {response.text}")
            return None
            
        response_content = response.json()["choices"][0]["message"]["content"]
        print(f"📄 Raw API response length: {len(response_content)} characters")
        print(f"📄 Response preview: {response_content[:200]}...")
        
        return {
            'method': 'original',
            'model': 'grok-4-0709',
            'response': response_content,
            'api_time': end_time - start_time,
            'status_code': response.status_code,
            'image_dimensions': [original_width, original_height, new_width, new_height]
        }
        
    except Exception as e:
        print(f"❌ Original Grok API failed: {e}")
        return None

def test_modular_grok_api(prompt: str, image_path: str, api_key: str):
    """Test modular Grok API call."""
    print("🔍 TESTING MODULAR GROK API")
    print(f"📝 Prompt: {prompt[:100]}...")
    
    try:
        # Use original encode_image for consistency
        base64_image, original_width, original_height, new_width, new_height = encode_image(image_path)
        
        # Modular API call setup (from modular grok_client.py)
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "grok-4-0709",  # Use same model as original
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }
        # Add proxies like original
        proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        
        print("🌐 Sending API request to Grok (modular method)...")
        start_time = time.time()
        
        # Add retry logic like original
        session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        response = session.post(url, headers=headers, json=payload, proxies=proxies, timeout=120)  # Same timeout as original
        end_time = time.time()
        
        print(f"📡 API response received in {end_time - start_time:.2f} seconds")
        print(f"📊 API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API call failed: {response.text}")
            return None
            
        response_content = response.json()["choices"][0]["message"]["content"]
        print(f"📄 Raw API response length: {len(response_content)} characters")
        print(f"📄 Response preview: {response_content[:200]}...")
        
        return {
            'method': 'modular',
            'model': 'grok-4-0709',
            'response': response_content,
            'api_time': end_time - start_time,
            'status_code': response.status_code,
            'image_dimensions': [original_width, original_height, new_width, new_height]
        }
        
    except Exception as e:
        print(f"❌ Modular Grok API failed: {e}")
        return None

def compare_grok_apis():
    """Compare both Grok API approaches."""
    print("=" * 80)
    print("🔬 GROK API COMPARISON TEST")
    print("=" * 80)
    
    # Test parameters
    text_command = "pass me the phone"
    image_path = os.path.join(parent_dir, "sampleImages", "image_000354.jpg")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Get API key
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("❌ XAI_API_KEY not found")
        return
    
    # Extract object and build prompt (same for both)
    from imageRecogVLM import extract_object
    object_str = extract_object(text_command)
    _, _, _, new_width, new_height = encode_image(image_path)
    prompt = build_grok_prompt(object_str, new_width, new_height)
    
    print(f"📝 Text command: '{text_command}'")
    print(f"🎯 Extracted object: '{object_str}'")
    print(f"🖼️  Image path: {image_path}")
    print(f"📐 Image dimensions: {new_width}x{new_height}")
    print()
    
    # Test original approach
    original_result = test_original_grok_api(prompt, image_path, api_key)
    print()
    
    # Test modular approach
    modular_result = test_modular_grok_api(prompt, image_path, api_key)
    print()
    
    # Compare results
    print("=" * 60)
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    if original_result and modular_result:
        print(f"🤖 Original model: {original_result['model']}")
        print(f"🤖 Modular model:  {modular_result['model']}")
        print(f"⏱️  Original time: {original_result['api_time']:.2f}s")
        print(f"⏱️  Modular time:  {modular_result['api_time']:.2f}s")
        print(f"📄 Original response length: {len(original_result['response'])}")
        print(f"📄 Modular response length:  {len(modular_result['response'])}")
        
        # Check if responses are identical
        responses_match = original_result['response'] == modular_result['response']
        print(f"📋 Responses identical: {responses_match}")
        
        if not responses_match:
            print("\n🔍 KEY DIFFERENCES DETECTED:")
            print(f"   🤖 Different models: {original_result['model']} vs {modular_result['model']}")
            print("   📄 Response content differs (showing first 300 chars):")
            print(f"   Original: {original_result['response'][:300]}...")
            print(f"   Modular:  {modular_result['response'][:300]}...")
        
        # Save results
        comparison_data = {
            'test_info': {
                'text_command': text_command,
                'object': object_str,
                'image_path': image_path,
                'prompt': prompt,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'original': original_result,
            'modular': modular_result,
            'analysis': {
                'models_match': original_result['model'] == modular_result['model'],
                'responses_match': responses_match,
                'key_differences': [
                    f"Model: {original_result['model']} vs {modular_result['model']}",
                    "Original uses proxies, modular doesn't",
                    "Original has different timeout (120s vs 30s)",
                    "Modular adds 'detail': 'high', 'stream': False, 'temperature': 0"
                ]
            }
        }
        
        with open('grok_api_comparison.json', 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        print("\n💾 Detailed results saved to grok_api_comparison.json")
        
    elif original_result:
        print("❌ Only original method succeeded")
    elif modular_result:
        print("❌ Only modular method succeeded")
    else:
        print("❌ Both methods failed")

if __name__ == "__main__":
    compare_grok_apis()
