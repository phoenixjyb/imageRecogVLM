import os
import requests
import re
import random
import base64
from PIL import Image, ImageDraw
from gtts import gTTS
import pygame
import tempfile
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
from datetime import datetime
import json
from openai import OpenAI  # Add OpenAI import for Qwen
import speech_recognition as sr  # Add speech recognition import

# Constants
RESIZE_WIDTH = None  # Set to None to use original resolution
LOCAL_RESIZE_COEFFICIENT = 1.0  # Coefficient to control local resize width (1.0 = same as cloud)
LOCAL_RESIZE_WIDTH = None  # Will use original resolution for local too

# Securely load API keys from environment variables
XAI_API_KEY = os.getenv('XAI_API_KEY')  # For Grok-4 cloud mode
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')  # For Qwen cloud mode

def extract_object(input_text: str) -> str:
    """
    Extract the object of interest from user input.
    Enhanced to handle both English and Chinese inputs with automatic translation.
    """
    input_text = input_text.strip()
    
    # Check if input contains Chinese characters
    def contains_chinese(text):
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    # If input is in Chinese, translate common patterns
    if contains_chinese(input_text):
        print(f"🌏 Detected Chinese input: '{input_text}'")
        translated_text = translate_chinese_to_english(input_text)
        print(f"🔄 Translated to English: '{translated_text}'")
        input_text = translated_text
    
    # Continue with existing English processing logic
    input_text = input_text.lower().strip()
    
    # Pattern 0: 'show me [object]' or 'show me a/the [object]'
    match = re.search(r'show me (?:a |the )?(.+?)(?:\s+(?:for me|to me|please))?$', input_text)
    if match:
        return match.group(1).strip()
    
    # Pattern 1: 'grab the [object] to me' or variations like 'grab a [object] for me'
    match = re.search(r'grab (?:the|a) (.*?) (?:to|for) me', input_text)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: 'identify the [object]' or 'please identify [object]'
    match = re.search(r'(?:identify|find|locate|get|bring) (?:the |me )?(.+?)(?:\s+(?:for me|to me|please))?$', input_text)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: '[object] please' - common casual format
    if 'please' in input_text:
        words = input_text.replace('please', '').strip().split()
        if words:
            return words[0].strip()
    
    # Fallback: Look for 'the [object]' and take the phrase after 'the'
    if 'the' in input_text:
        idx = input_text.index('the') + len('the')
        object_str = input_text[idx:].strip().split()[0]
        return object_str
    
    # Ultimate fallback: Take the first meaningful word (not 'please', 'grab', etc.)
    words = input_text.split()
    if words:
        # Filter out common command words
        filter_words = {'please', 'grab', 'get', 'find', 'identify', 'locate', 'for', 'me', 'to', 'the', 'a', 'an'}
        meaningful_words = [w for w in words if w not in filter_words]
        if meaningful_words:
            return meaningful_words[0].strip()
        else:
            return words[0].strip()
    
    raise ValueError("Could not extract object from input text. Please use a format like 'please grab the [object] to me' or 'identify the [object]'.")

def translate_chinese_to_english(chinese_text: str) -> str:
    """
    Translate Chinese commands to English using pattern matching.
    Add more patterns as needed for your use cases.
    """
    # Dictionary of common Chinese patterns and their English translations
    chinese_patterns = {
        # Command patterns
        r'请.*?拿.*?给我': 'please grab {} to me',
        r'帮我.*?拿.*': 'help me get {}',
        r'找.*?给我': 'find {} for me',
        r'给我.*?拿': 'get me {}',
        r'请.*?找': 'please find {}',
        r'帮我.*?找': 'help me find {}',
        
        # Object patterns - add more objects as needed
        r'可乐|可口可乐': 'coke',
        r'苹果': 'apple', 
        r'书|书本': 'book',
        r'车|汽车': 'car',
        r'房子|房屋': 'house',
        r'瓶子|水瓶': 'bottle',
        r'钥匙': 'keys',
        r'狗|小狗': 'dog',
        r'雨伞|伞': 'umbrella',
        r'猫|小猫': 'cat',
        r'遥控器': 'remote',
        r'电话|手机': 'phone',
        r'杯子|茶杯': 'cup',
        r'盘子': 'plate',
        r'桌子': 'table',
        r'椅子': 'chair'
    }
    
    translated = chinese_text
    
    # Try to match command patterns first
    for pattern, template in list(chinese_patterns.items())[:6]:  # First 6 are command patterns
        if re.search(pattern, chinese_text):
            # Extract object from the Chinese text
            remaining_text = re.sub(pattern.replace('.*?', ''), '', chinese_text)
            # Translate the object
            for obj_pattern, obj_english in list(chinese_patterns.items())[6:]:  # Object patterns
                if re.search(obj_pattern, remaining_text):
                    if '{}' in template:
                        translated = template.format(obj_english)
                    else:
                        translated = f"{template} {obj_english}"
                    return translated
            # If no object pattern matched, use the remaining text
            if '{}' in template:
                translated = template.format(remaining_text.strip())
            else:
                translated = f"{template} {remaining_text.strip()}"
            return translated
    
    # If no command pattern matched, try direct object translation
    for obj_pattern, obj_english in list(chinese_patterns.items())[6:]:
        if re.search(obj_pattern, chinese_text):
            translated = f"find {obj_english}"
            break
    
    # Fallback: return original if no patterns matched
    if translated == chinese_text:
        print(f"⚠️  No translation pattern found for: '{chinese_text}'")
        translated = f"find {chinese_text}"  # Fallback format
    
    return translated

def build_prompt(object_str: str, image_width: int, image_height: int) -> str:
    """
    Build the augmented prompt for cloud VLMs (Grok/Qwen).
    """
    return (
        f"Analyze this image which has been resized to {image_width}x{image_height} pixels. "
        f"Locate all instances of '{object_str}' in the image. "
        f"For each object found, determine the CENTER POINT coordinates (the middle of the object). "
        f"Please summarize the center coordinates in a table with columns 'H', 'V', and 'ID' for each instance found. "
        f"H should be the horizontal center coordinate, V should be the vertical center coordinate. "
        f"If no object is found, return a table with 'H', 'V', 'ID' values of 0, 0, 0."
    )

def build_grok_prompt(object_str: str, image_width: int, image_height: int) -> str:
    """
    Build a Grok-specific prompt.
    """
    return (
        f"Please use Grok-4 to analyze this image which has been resized to {image_width}x{image_height} pixels. "
        f"Locate all instances of '{object_str}' in the image. "
        f"For each object found, determine the CENTER POINT coordinates (the middle of the object). "
        f"Please summarize the center coordinates in a table with columns 'H', 'V', and 'ID' for each instance found. "
        f"H should be the horizontal center coordinate, V should be the vertical center coordinate. "
        f"If no object is found, return a table with 'H', 'V', 'ID' values of 0, 0, 0."
    )

def build_qwen_prompt(object_str: str, image_width: int, image_height: int) -> str:
    """
    Build a Qwen-specific prompt that's more precise but still generic.
    """
    return (
        f"Analyze this image carefully (resolution: {image_width}x{image_height} pixels). "
        f"Look specifically for '{object_str}' objects in the image. "
        f"Focus on identifying the actual physical objects that match '{object_str}', not similar-looking items. "
        f"For each '{object_str}' you find: "
        f"1. Locate the exact center point of the object "
        f"2. Provide coordinates in table format: | H | V | ID | "
        f"3. H = horizontal pixel position, V = vertical pixel position "
        f"4. ID = object number (1, 2, 3, etc.) "
        f"If you cannot find any actual '{object_str}' objects, return: | 0 | 0 | 0 |"
    )

def build_local_prompt(object_str: str, image_width: int, image_height: int) -> str:
    """
    Build an optimized prompt for local VLMs like LLaVA.
    Uses simpler, more direct language that works better with local models.
    """
    return (
        f"Look at this image. Do you see any '{object_str}'? "
        f"If yes, tell me the pixel coordinates of the center of each one. "
        f"If no, just say 'none found'. "
        f"Image size is {image_width}x{image_height}."
    )

def encode_image(image_path: str, resize_width: int = None) -> tuple[str, int, int, int, int]:
    """
    Encode image to base64. If resize_width is None, use original resolution.
    Returns the base64 string and original/new dimensions.
    """
    print("📸 Starting image preprocessing...")
    start_time = time.time()
    
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        original_width, original_height = img.size
        print(f"   Original image size: {original_width}x{original_height}")
        
        if resize_width is None:
            # Use original resolution
            new_width, new_height = original_width, original_height
            print(f"   Using original resolution: {new_width}x{new_height}")
            processed_img = img
        else:
            # Resize as before
            new_width = resize_width
            aspect_ratio = original_height / original_width
            new_height = int(new_width * aspect_ratio)
            print(f"   Resizing to: {new_width}x{new_height} (maintaining aspect ratio)")
            processed_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Use higher quality for original resolution
        quality = 95 if resize_width is None else 85
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            processed_img.save(temp_file, format='JPEG', quality=quality)
            temp_file.seek(0)
            base64_data = base64.b64encode(temp_file.read()).decode('utf-8')
        os.unlink(temp_file.name)
        
    end_time = time.time()
    print(f"✅ Image preprocessing completed in {end_time - start_time:.2f} seconds")
    return base64_data, original_width, original_height, new_width, new_height

def call_grok4_api(prompt: str, image_path: str, api_key: str) -> str:
    """
    Call Grok4 API with prompt and image, with retry logic.
    Returns raw text content for display.
    """
    print("🔄 Preparing API request...")
    api_start_time = time.time()
    
    base64_image, original_width, original_height, new_width, new_height = encode_image(image_path)
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-4-0709",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
    }
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    
    print("🌐 Sending API request to Grok-4...")
    request_start_time = time.time()
    
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    
    try:
        response = session.post(url, headers=headers, json=payload, proxies=proxies, timeout=120)
        request_end_time = time.time()
        
        print(f"📡 API response received in {request_end_time - request_start_time:.2f} seconds")
        print(f"📊 API response status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.text}")
            
        response_content = response.json()["choices"][0]["message"]["content"]
        print(f"📄 Raw API response length: {len(response_content)} characters")
        
        api_end_time = time.time()
        print(f"✅ Total API process completed in {api_end_time - api_start_time:.2f} seconds")
        
        return response_content
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed after retries: {str(e)}")

def parse_response(response_text: str, object_str: str, original_width: int, original_height: int, new_width: int, new_height: int) -> tuple[str, bool]:
    """
    Parse VLM response for coordinates from a table. No scaling needed if using original resolution.
    Returns formatted table string and recognized flag.
    """
    print("🔍 Starting coordinate parsing...")
    print(f"   📐 Image dimensions: Original({original_width}x{original_height}) → Processed({new_width}x{new_height})")
    
    # Check if we need scaling
    needs_scaling = (original_width != new_width) or (original_height != new_height)
    if needs_scaling:
        print(f"   📊 Scaling factors: H_scale={original_width/new_width:.3f}, V_scale={original_height/new_height:.3f}")
    else:
        print("   📊 No scaling needed - using original coordinates")
    
    # Find all table rows (skip header and separator)
    lines = [line.strip() for line in response_text.strip().split('\n')]
    data_rows = []
    for line in lines:
        if re.match(r'^\|\s*\d+', line):  # Row starts with | and a number
            data_rows.append(line)
    
    print(f"   Found {len(data_rows)} coordinate data rows")
    
    if not data_rows:
        print("❌ No coordinate data found in response")
        return "0 | 0 | 0", False

    coordinates = []
    for i, row in enumerate(data_rows):
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        print(f"   Processing row {i+1}/{len(data_rows)}: {cells[:3] if len(cells) >= 3 else cells}")
        
        if len(cells) >= 3:
            try:
                h = int(cells[0])
                v = int(cells[1])
                id_num = cells[2] if cells[2].isdigit() else "0"
                
                if needs_scaling:
                    # Rescale coordinates to original resolution
                    scaled_h = int(h * (original_width / new_width))
                    scaled_v = int(v * (original_height / new_height))
                    print(f"   🎯 Row {i+1}: Raw({h},{v}) → Scaled({scaled_h},{scaled_v}) [ID: {id_num}]")
                    coordinates.append((scaled_h, scaled_v, id_num))
                else:
                    # Use coordinates as-is
                    print(f"   🎯 Row {i+1}: Direct coordinates({h},{v}) [ID: {id_num}]")
                    coordinates.append((h, v, id_num))
                
            except Exception as e:
                print(f"   ⚠️ Skipping invalid row: {e}")

    if not coordinates:
        print("❌ No valid coordinates extracted")
        return "0 | 0 | 0", False

    # Check if all coordinates are (0,0) - means no objects found
    non_zero_coords = [(h, v, id_num) for h, v, id_num in coordinates if h != 0 or v != 0]
    if not non_zero_coords:
        print("❌ All coordinates are (0,0) - no objects detected")
        return "0 | 0 | 0", False

    print(f"✅ Successfully extracted {len(non_zero_coords)} valid coordinate(s)")
    
    recognized = True
    if len(non_zero_coords) == 1:
        h, v, id_num = non_zero_coords[0]
        coord_result = f"{h} | {v} | {id_num}"
    else:
        coord_result = "; ".join([f"{h} | {v} | {id_num}" for h, v, id_num in non_zero_coords])
    
    return coord_result, recognized

def generate_response(object_str: str, recognized: bool, coord_str: str, raw_response: str = "", vlm_choice: str = "grok") -> str:
    """
    Generate textual response based on recognition, including the original model output and a summary table.
    """
    response_parts = []
    
    # Add recognition status
    if recognized:
        response_parts.append(f"{object_str} is recognized, let me fetch it to you")
    else:
        response_parts.append("sorry, I cannot locate it")
    
    # Add original model output section
    if raw_response:
        vlm_name = vlm_choice.upper()
        if vlm_choice == "qwen":
            vlm_name = "QWEN-VL"
        elif vlm_choice == "grok":
            vlm_name = "GROK-4"
        elif vlm_choice == "local":
            vlm_name = "LLAVA (LOCAL)"
        
        response_parts.append("\n" + "="*50)
        response_parts.append(f"📄 ORIGINAL {vlm_name} MODEL OUTPUT:")
        response_parts.append("="*50)
        response_parts.append(raw_response)
        response_parts.append("="*50)
    
    # Add coordinate summary table
    response_parts.append("\n📊 COORDINATE SUMMARY TABLE:")
    response_parts.append("-"*40)
    
    if recognized and coord_str != "0 | 0 | 0":
        response_parts.append("| Object ID | H (Horizontal) | V (Vertical) |")
        response_parts.append("|-----------|----------------|--------------|")
        
        # Parse coordinates for table display
        coords = coord_str.split(';') if ';' in coord_str else [coord_str]
        for i, coord in enumerate(coords):
            parts = [p.strip() for p in coord.split('|')]
            if len(parts) >= 3:
                h, v, obj_id = parts[0], parts[1], parts[2]
                response_parts.append(f"|     {obj_id}     |      {h:>6}      |     {v:>6}     |")
            else:
                response_parts.append(f"|     {i+1}     |      {parts[0]:>6}      |     {parts[1]:>6}     |")
    else:
        response_parts.append("| Object ID | H (Horizontal) | V (Vertical) |")
        response_parts.append("|-----------|----------------|--------------|")
        response_parts.append("|     0     |       0        |      0       |")
    
    response_parts.append("-"*40)
    
    return "\n".join(response_parts)

def text_to_speech(text: str) -> None:
    """
    Convert text to speech using macOS built-in say command (no internet required).
    Extracts concise message for audio output.
    """
    try:
        # Extract concise message for speech
        lines = text.split('\n')
        main_message = lines[0].strip()  # First line is usually the recognition result
        
        # Make it even more concise for speech
        if "is recognized" in main_message:
            # Extract object name
            object_name = main_message.split()[0]
            concise_message = f"{object_name} found"
        elif "cannot locate" in main_message:
            concise_message = "Object not found"
        else:
            concise_message = main_message
        
        # Use macOS built-in say command with timeout
        import subprocess
        subprocess.run(['say', concise_message], timeout=10, check=True)
        print(f"🔊 Audio played: '{concise_message}'")
        
    except subprocess.TimeoutExpired:
        print("⏰ TTS timeout - skipping audio")
    except Exception as e:
        print(f"🔇 TTS failed: {e} - continuing without audio")

def show_image_with_star(image_path: str, x: int, y: int, star_size: int = 20):
    """
    Display the image and draw a star at (x, y).
    """
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)

        # Calculate star points (5-pointed star)
        points = []
        for i in range(5):
            angle = math.radians(i * 144 - 90)
            outer_x = x + star_size * math.cos(angle)
            outer_y = y + star_size * math.sin(angle)
            points.append((outer_x, outer_y))
        draw.polygon(points, fill="yellow", outline="red")

        img.show()

def get_vlm_choice() -> str:
    """
    Interactive function to let user choose between cloud VLM processing options and local processing.
    Returns 'grok' for Grok API, 'qwen' for Qwen API, or 'local' for LLaVA via Ollama.
    """
    print("\n🤖 VLM Processing Mode Selection")
    print("=" * 50)
    print("1. ☁️  Cloud VLM (Grok-4 via X.AI API)")
    print("   - Higher accuracy")
    print("   - Requires internet & XAI API key")
    print("   - Processing cost applies")
    print("")
    
    # Check Qwen availability
    qwen_available = bool(DASHSCOPE_API_KEY)
    if qwen_available:
        print("2. ☁️  Cloud VLM (Qwen-VL via DashScope API) ✅ Available")
        print("   - Good accuracy, excellent Chinese support")
        print("   - Requires internet & DashScope API key")
        print("   - Processing cost applies")
    else:
        print("2. ☁️  Cloud VLM (Qwen-VL via DashScope API) ❌ Not Available")
        print("   - Set DASHSCOPE_API_KEY environment variable")
    print("")
    
    # Check Ollama availability
    ollama_available = check_ollama_availability()
    if ollama_available:
        print("3. 🖥️  Local VLM (LLaVA via Ollama) ✅ Available")
        print("   - Privacy focused")
        print("   - No internet required")
        print("   - Free processing")
    else:
        print("3. 🖥️  Local VLM (LLaVA via Ollama) ❌ Not Available")
        print("   - Install Ollama: 'curl -fsSL https://ollama.com/install.sh | sh'")
        print("   - Install LLaVA: 'ollama pull llava:7b'")
        print("   - Start service: 'ollama serve'")
    
    print("=" * 50)
    
    while True:
        choice = input("Choose processing mode (1 for Grok, 2 for Qwen, 3 for Local): ").strip()
        if choice == "1":
            return "grok"
        elif choice == "2":
            if not qwen_available:
                print("❌ DASHSCOPE_API_KEY not set. Please set your DashScope API key.")
                continue
            return "qwen"
        elif choice == "3":
            if not ollama_available:
                print("❌ Local VLM not available. Please install and start Ollama with LLaVA model.")
                continue
            return "local"
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def call_local_vlm_api(prompt: str, image_path: str) -> str:
    """
    Call local Gemma3 VLM via Ollama with prompt and image.
    Returns raw text content for display.
    """
    print("🔄 Preparing local VLM request...")
    api_start_time = time.time()
    
    # Encode image to base64 with smaller size for local processing
    base64_image, original_width, original_height, new_width, new_height = encode_image(image_path, LOCAL_RESIZE_WIDTH)
    
    # Ollama API endpoint (default local)
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "llava:latest",  # Using LLaVA model for vision tasks via Ollama
        "prompt": prompt,
        "images": [base64_image],
        "stream": False
    }
    
    print("🖥️  Sending request to local Ollama (LLaVA)...")
    request_start_time = time.time()
    
    # Configure session to bypass proxy for local connections
    session = requests.Session()
    # Explicitly disable all proxy settings for local requests
    session.proxies = {
        'http': '',
        'https': '',
        'no_proxy': 'localhost,127.0.0.1'
    }
    session.trust_env = False  # Don't trust environment proxy settings
    
    try:
        response = session.post(url, json=payload, timeout=60)  # Shorter timeout for local processing
        request_end_time = time.time()
        
        print(f"📡 Local VLM response received in {request_end_time - request_start_time:.2f} seconds")
        print(f"📊 Local API response status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"Local VLM API call failed: {response.text}")
            
        response_json = response.json()
        response_content = response_json.get("response", "")
        print(f"📄 Local VLM response length: {len(response_content)} characters")
        
        api_end_time = time.time()
        print(f"✅ Total local VLM process completed in {api_end_time - api_start_time:.2f} seconds")
        
        return response_content
    except requests.exceptions.RequestException as e:
        raise Exception(f"Local VLM request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Local VLM processing error: {str(e)}")

def call_qwen_api(prompt: str, image_path: str, api_key: str) -> str:
    """
    Call Qwen VL API via OpenAI-compatible endpoint with prompt and image.
    Returns raw text content for display.
    """
    print("🔄 Preparing Qwen API request...")
    api_start_time = time.time()
    
    # Encode image to base64
    base64_image, original_width, original_height, new_width, new_height = encode_image(image_path)
    
    # Initialize OpenAI client for Qwen (DashScope-compatible endpoint)
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    print("🌐 Sending API request to Qwen-VL...")
    request_start_time = time.time()
    
    try:
        completion = client.chat.completions.create(
            model="qwen-vl-plus",  # You can also use "qwen-vl-max" for higher accuracy
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        
        request_end_time = time.time()
        print(f"📡 Qwen API response received in {request_end_time - request_start_time:.2f} seconds")
        
        response_content = completion.choices[0].message.content
        print(f"📄 Qwen response length: {len(response_content)} characters")
        
        api_end_time = time.time()
        print(f"✅ Total Qwen API process completed in {api_end_time - api_start_time:.2f} seconds")
        
        return response_content
        
    except Exception as e:
        raise Exception(f"Qwen API request failed: {str(e)}")

def check_ollama_availability() -> bool:
    """
    Check if Ollama service is running and LLaVA model is available.
    Returns True if available, False otherwise.
    """
    try:
        # Check if Ollama service is running
        # Configure session to bypass proxy for local connections
        session = requests.Session()
        # Explicitly disable all proxy settings for local requests
        session.proxies = {
            'http': '',
            'https': '',
            'no_proxy': 'localhost,127.0.0.1'
        }
        session.trust_env = False  # Don't trust environment proxy settings
        
        response = session.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            # Check if LLaVA model is available (looking for llava:latest specifically)
            llava_available = any(
                "llava" in model.get("name", "").lower() 
                for model in models
            )
            if llava_available:
                print(f"   🔍 Found LLaVA models: {[m.get('name') for m in models if 'llava' in m.get('name', '').lower()]}")
            return llava_available
        else:
            print(f"   ❌ Ollama API returned status: {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ollama connection error: {e}")
        return False

def get_input_mode() -> str:
    """
    Interactive function to let user choose between voice input and text input.
    Returns 'voice' for voice input or 'text' for text input.
    """
    print("\n🎤 Input Mode Selection")
    print("=" * 50)
    print("1. 🎙️  Voice Input")
    print("   - Speak your command")
    print("   - Automatically converted to text")
    print("   - Supports English and Chinese")
    print("")
    print("2. ⌨️  Text Input") 
    print("   - Type your command")
    print("   - Current default mode")
    print("   - Supports English and Chinese")
    print("=" * 50)
    
    while True:
        choice = input("Choose input mode (1 for Voice, 2 for Text): ").strip()
        if choice == "1":
            return "voice"
        elif choice == "2":
            return "text"
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

def get_voice_input() -> str:
    """
    Capture voice input and convert it to text using speech recognition.
    Returns the recognized text or raises an exception if recognition fails.
    """
    print("\n🎙️ Voice Input Mode")
    print("=" * 40)
    print("🔴 Preparing microphone...")
    
    # Initialize recognizer and microphone
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    print("🔧 Calibrating microphone for ambient noise...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    print("🎤 Ready to listen! Please speak your command...")
    print("   (e.g., 'please grab the apple to me' or '请帮我拿可乐给我')")
    print("   💡 Tip: Speak clearly and wait for the beep")
    
    try:
        # Listen for audio input
        with microphone as source:
            print("🔴 Recording... (speak now)")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
            print("⏹️  Recording complete, processing...")
        
        # Try to recognize speech using Google's speech recognition
        print("🔍 Converting speech to text...")
        try:
            # First try with English
            user_input = recognizer.recognize_google(audio, language='en-US')
            print(f"✅ Speech recognized (English): '{user_input}'")
            return user_input
        except sr.UnknownValueError:
            # If English fails, try Chinese
            try:
                user_input = recognizer.recognize_google(audio, language='zh-CN')
                print(f"✅ Speech recognized (Chinese): '{user_input}'")
                return user_input
            except sr.UnknownValueError:
                raise Exception("Could not understand the audio. Please try speaking more clearly.")
        
    except sr.WaitTimeoutError:
        raise Exception("No speech detected within timeout period. Please try again.")
    except sr.RequestError as e:
        # Fallback to offline recognition if available
        try:
            print("🔄 Internet connection issue, trying offline recognition...")
            user_input = recognizer.recognize_sphinx(audio)
            print(f"✅ Speech recognized (Offline): '{user_input}'")
            return user_input
        except:
            raise Exception(f"Speech recognition service error: {e}")
    except Exception as e:
        raise Exception(f"Voice input error: {e}")

def get_user_input() -> str:
    """
    Get user input either through voice or text based on user choice.
    Returns the user's command as text.
    """
    input_mode = get_input_mode()
    
    if input_mode == "voice":
        try:
            return get_voice_input()
        except Exception as e:
            print(f"❌ Voice input failed: {e}")
            print("🔄 Falling back to text input...")
            return input("\n💬 Please enter your command manually: ").strip()
    else:
        return input("\n💬 Enter your command (e.g., 'please grab the apple to me' or '请帮我拿可乐给我'): ").strip()

def main():
    """
    Main function to orchestrate the process.
    Now supports voice input, text input, and three VLM pathways: Grok-4, Qwen-VL, and local LLaVA.
    """
    print("=" * 60)
    print("🤖 VLM Object Recognition System (Voice + 3-Mode)")
    print("=" * 60)
    
    overall_start_time = time.time()
    start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕐 Process started at: {start_timestamp}")
    
    try:
        # Get user input via voice or text
        user_input = get_user_input()
        
        # Check if input contains Chinese and show translation
        def contains_chinese(text):
            return any('\u4e00' <= char <= '\u9fff' for char in text)
        
        if contains_chinese(user_input):
            print(f"\n🌏 Original Chinese command: '{user_input}'")
            translated_command = translate_chinese_to_english(user_input)
            print(f"🔄 Translated English command: '{translated_command}'")
            print(f"✅ Using translated command for processing")
        else:
            print(f"\n💬 Command received: '{user_input}'")
        
        image_dir = "/Users/yanbo/Projects/vlmTry/sampleImages"
        image_name = "image_000777_rsz.jpg"
        image_path = os.path.join(image_dir, image_name)
        
        print(f"\n📂 Loading image: {image_name}")
        with Image.open(image_path) as img:
            width, height = img.size
            print(f"   ✓ Image loaded successfully: {width}x{height}")
        
        print(f"\n🎯 Extracting target object from user input...")
        object_str = extract_object(user_input)
        print(f"   ✓ Target object identified: '{object_str}'")
        
        print(f"\n🔧 Building prompt for VLM...")
        # Get dimensions - now using original resolution
        _, original_width, original_height, new_width, new_height = encode_image(image_path, resize_width=None)
        print(f"   ✓ Using resolution: {new_width}x{new_height} (original size)")
        
        # --- Get user choice for VLM processing ---
        vlm_choice = get_vlm_choice()
        
        # Build appropriate prompt based on VLM choice
        if vlm_choice == "grok":
            prompt = build_grok_prompt(object_str, new_width, new_height)
        elif vlm_choice == "qwen":
            prompt = build_qwen_prompt(object_str, new_width, new_height)
        else:  # local
            prompt = build_local_prompt(object_str, new_width, new_height)
        
        print(f"   ✓ {vlm_choice.title()} prompt ready (length: {len(prompt)} characters)")
        
        # Call appropriate VLM API based on choice
        if vlm_choice == "grok":
            # Validate API key for Grok mode
            if not XAI_API_KEY:
                raise ValueError("XAI_API_KEY environment variable not set. Required for Grok mode.")
            print(f"\n🚀 Calling Grok-4 Vision API (Cloud)...")
            response_text = call_grok4_api(prompt, image_path, XAI_API_KEY)
            
        elif vlm_choice == "qwen":
            # Validate API key for Qwen mode
            if not DASHSCOPE_API_KEY:
                raise ValueError("DASHSCOPE_API_KEY environment variable not set. Required for Qwen mode.")
            print(f"\n🚀 Calling Qwen-VL Vision API (Cloud)...")
            response_text = call_qwen_api(prompt, image_path, DASHSCOPE_API_KEY)
            
        else:  # local
            print(f"\n🖥️  Calling Local VLM (LLaVA via Ollama)...")
            response_text = call_local_vlm_api(prompt, image_path)
        
        print(f"   ✓ VLM response received (length: {len(response_text)} characters)")
        
        # --- Parse and rescale coordinates ---
        coord_str, recognized = parse_response(response_text, object_str, original_width, original_height, new_width, new_height)
        
        # --- Generate and display response ---
        response_message = generate_response(object_str, recognized, coord_str, response_text, vlm_choice)
        print("\n📬 Response:")
        print("="*50)
        print(response_message)
        print("="*50)
        
        # --- Text-to-speech output ---
        tts_enabled = True  # Enable TTS with concise messages
        if tts_enabled:
            print("\n🔊 Playing audio response...")
            text_to_speech(response_message)
        else:
            print("🔇 Text-to-speech disabled - continuing to image display")
    
        # --- Show image with annotation (if recognized) ---
        if recognized and coord_str != "0 | 0 | 0":
            print("\n🖼️ Showing image with annotated object location...")
            # Extract first valid coordinate for annotation
            first_coord = coord_str.split(';')[0]
            h, v, id_num = [int(x.strip()) for x in first_coord.split('|')]
            # Show image with star at the detected object location
            show_image_with_star(image_path, h, v)
        else:
            print("✅ No valid object coordinates to display.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    overall_end_time = time.time()
    total_duration = overall_end_time - overall_start_time
    print(f"🕔 Total process time: {total_duration:.2f} seconds")
    end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"✅ Process ended at: {end_timestamp}")

# --- Debugging and testing helpers ---
def test_extract_object():
    """
    Test extract_object() with various inputs.
    """
    test_cases = [
        "please grab the apple to me",
        "identify the book",
        "find me the car",
        "show the house",
        "grab a bottle for me",
        "please locate the keys",
        "the dog is missing",
        "I need an umbrella",
        "where is the cat",
        "bring me the remote"
    ]
    
    print("Testing extract_object function:")
    for case in test_cases:
        try:
            result = extract_object(case)
            print(f"'{case}' -> '{result}'")
        except Exception as e:
            print(f"'{case}' -> ERROR: {e}")

if __name__ == "__main__":
    main()