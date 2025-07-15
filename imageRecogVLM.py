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

# Constants
RESIZE_WIDTH = 256  # Width to resize images to before sending to VLM
LOCAL_RESIZE_COEFFICIENT = 1.0  # Coefficient to control local resize width (1.0 = same as cloud)
LOCAL_RESIZE_WIDTH = int(RESIZE_WIDTH * LOCAL_RESIZE_COEFFICIENT)  # Local VLM processing width

# Securely load API key from environment variable (optional for local mode)
API_KEY = os.getenv('XAI_API_KEY')  # Only required for cloud mode

def extract_object(input_text: str) -> str:
    """
    Extract the object of interest from user input.
    Improved to handle more flexible inputs: looks for patterns like 'grab the [object] to me', 'identify the [object]', or fallback to keywords.
    """
    input_text = input_text.lower().strip()
    
    # Pattern 1: 'grab the [object] to me' or variations like 'grab a [object] for me'
    match = re.search(r'grab (?:the|a) (.*?) (?:to|for) me', input_text)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: 'identify the [object]' or 'please identify [object]'
    match = re.search(r'(?:identify|find|locate) (?:the )?(.*?) (?:for me)?', input_text)
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

def build_prompt(object_str: str, image_width: int, image_height: int) -> str:
    """
    Build the augmented prompt for the VLM, including the resized image resolution, and request a table.
    """
    return (
        f"please use the vlm such as grok4 to read the image provided, which has been resized to a resolution of {image_width}x{image_height} pixels, "
        f"and locate the object of interest '{object_str}'. Please identify all instances of this object in the image. "
        f"For each object found, determine the CENTER POINT coordinates (the middle of the object). "
        f"Please summarize the center coordinates in a concise table with columns 'H', 'V', and 'ID' for each instance found. "
        f"H should be the horizontal center coordinate, V should be the vertical center coordinate. "
        f"If no object is found, return a table with 'H', 'V', 'ID' values of 0, 0, 0."
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

def encode_image(image_path: str, resize_width: int = RESIZE_WIDTH) -> tuple[str, int, int, int, int]:
    """
    Encode image to base64 after preprocessing to resize to specified width, maintaining aspect ratio.
    Returns the base64 string and original/new dimensions.
    """
    print("📸 Starting image preprocessing...")
    start_time = time.time()
    
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        original_width, original_height = img.size
        print(f"   Original image size: {original_width}x{original_height}")
        
        new_width = resize_width
        aspect_ratio = original_height / original_width
        new_height = int(new_width * aspect_ratio)
        print(f"   Resizing to: {new_width}x{new_height} (maintaining aspect ratio)")
        
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Use lower quality for local processing to speed up
        quality = 60 if resize_width == LOCAL_RESIZE_WIDTH else 85
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            resized_img.save(temp_file, format='JPEG', quality=quality)
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
    
    base64_image, original_width, original_height, new_width, new_height = encode_image(image_path, RESIZE_WIDTH)
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
    Parse VLM response for coordinates from a table, rescale to original resolution.
    Returns formatted table string and recognized flag.
    """
    print("🔍 Starting coordinate parsing and scaling...")
    parse_start_time = time.time()
    
    print(f"   Response text length: {len(response_text)} characters")
    
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
                
                # Rescale coordinates to original resolution
                scaled_h = int(h * (original_width / new_width))
                scaled_v = int(v * (original_height / new_height))
                coordinates.append((scaled_h, scaled_v, id_num))
                
                print(f"   ✓ Scaled coordinates: ({h},{v}) → ({scaled_h},{scaled_v}) [ID: {id_num}]")
            except Exception as e:
                print(f"   ⚠️ Skipping invalid row due to {e}: {row}")

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
    
    parse_end_time = time.time()
    print(f"✅ Coordinate parsing completed in {parse_end_time - parse_start_time:.2f} seconds")
    
    return coord_result, recognized

def generate_response(object_str: str, recognized: bool, coord_str: str, raw_response: str = "") -> str:
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
        response_parts.append("\n" + "="*50)
        response_parts.append("📄 ORIGINAL MODEL OUTPUT:")
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
    Convert text to speech and play it.
    Uses gTTS for synthesis and pygame for playback.
    """
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
            tts.save(temp_filename)
        
        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        os.remove(temp_filename)
    except Exception as e:
        print(f"TTS failed: {e}. Falling back to text output.")

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
    Interactive function to let user choose between cloud and local VLM processing.
    Returns 'cloud' for Grok API or 'local' for Gemma3 via Ollama.
    """
    print("\n🤖 VLM Processing Mode Selection")
    print("=" * 40)
    print("1. ☁️  Cloud VLM (Grok-4 via X.AI API)")
    print("   - Higher accuracy")
    print("   - Requires internet & API key")
    print("   - Processing cost applies")
    print("")
    
    # Check Ollama availability
    ollama_available = check_ollama_availability()
    if ollama_available:
        print("2. 🖥️  Local VLM (LLaVA via Ollama) ✅ Available")
        print("   - Privacy focused")
        print("   - No internet required")
        print("   - Free processing")
    else:
        print("2. 🖥️  Local VLM (LLaVA via Ollama) ❌ Not Available")
        print("   - Install Ollama: 'curl -fsSL https://ollama.com/install.sh | sh'")
        print("   - Install LLaVA: 'ollama pull llava:7b'")
        print("   - Start service: 'ollama serve'")
    
    print("=" * 40)
    
    while True:
        choice = input("Choose processing mode (1 for Cloud, 2 for Local): ").strip()
        if choice == "1":
            return "cloud"
        elif choice == "2":
            if not ollama_available:
                print("❌ Local VLM not available. Please install and start Ollama with LLaVA model.")
                continue
            return "local"
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

def call_local_vlm_api(prompt: str, image_path: str) -> str:
    """
    Call local LLaVA VLM via Ollama with prompt and image.
    Returns raw text content for display.
    """
    print("🔄 Preparing local VLM request...")
    api_start_time = time.time()
    
    # Encode image to base64 with size based on LOCAL_RESIZE_WIDTH
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

def main():
    """
    Main function to orchestrate the process.
    Now interactive: prompts user for input; image path is predefined with specific image name.
    """
    print("=" * 60)
    print("🤖 VLM Object Recognition System")
    print("=" * 60)
    
    overall_start_time = time.time()
    start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕐 Process started at: {start_timestamp}")
    
    try:
        user_input = input("\n💬 Enter your command (e.g., 'please grab the apple to me'): ").strip()
        image_dir = "/Users/yanbo/Projects/vlmTry/sampleImages"
        image_name = "image_000078.jpg"
        image_path = os.path.join(image_dir, image_name)
        
        print(f"\n📂 Loading image: {image_name}")
        with Image.open(image_path) as img:
            width, height = img.size
            print(f"   ✓ Image loaded successfully: {width}x{height}")
        
        print(f"\n🎯 Extracting target object from user input...")
        object_str = extract_object(user_input)
        print(f"   ✓ Target object identified: '{object_str}'")
        
        print(f"\n📝 Building prompt for VLM...")
        # --- Get user choice for VLM processing ---
        vlm_choice = get_vlm_choice()
        
        # Get dimensions by encoding the image with appropriate size based on mode
        if vlm_choice == "cloud":
            resize_width = RESIZE_WIDTH
        else:  # local
            resize_width = LOCAL_RESIZE_WIDTH
            
        _, original_width, original_height, new_width, new_height = encode_image(image_path, resize_width)
        print(f"   ✓ Dimension scaling: {original_width}x{original_height} → {new_width}x{new_height}")
        
        # Build appropriate prompt based on VLM choice
        if vlm_choice == "cloud":
            prompt = build_prompt(object_str, new_width, new_height)
        else:  # local
            prompt = build_local_prompt(object_str, new_width, new_height)
        
        print(f"   ✓ {vlm_choice.title()} prompt ready (length: {len(prompt)} characters)")
        
        if vlm_choice == "cloud":
            # Validate API key for cloud mode
            if not API_KEY:
                raise ValueError("XAI_API_KEY environment variable not set. Required for cloud mode.")
            print(f"\n🚀 Calling Grok-4 Vision API (Cloud)...")
            response_text = call_grok4_api(prompt, image_path, API_KEY)
        else:  # local
            # Check Ollama availability before proceeding
            if not check_ollama_availability():
                raise Exception("Ollama service is not available or LLaVA model is not found. Please check your Ollama installation.")
            
            print(f"\n🖥️  Calling Local LLaVA via Ollama...")
            response_text = call_local_vlm_api(prompt, image_path)
        
        print(f"\n🔄 Processing API response...")
        coord_str, recognized = parse_response(response_text, object_str, original_width, original_height, new_width, new_height)
        
        print(f"\n📤 Generating final response...")
        resp_text = generate_response(object_str, recognized, coord_str, response_text)
        
        overall_end_time = time.time()
        total_time = overall_end_time - overall_start_time
        end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "=" * 60)
        print("📋 FINAL RESULTS")
        print("=" * 60)
        print(resp_text)
        print(f"\n⏱️  TIMING SUMMARY:")
        print(f"   Started:  {start_timestamp}")
        print(f"   Finished: {end_timestamp}")
        print(f"   Total processing time: {total_time:.2f} seconds")
        print("=" * 60)
        
        print(f"\n🔊 Converting to speech...")
        text_to_speech(resp_text)

        # --- Show image with star if coordinates are valid ---
        if recognized and coord_str != "0 | 0 | 0":
            print(f"\n🎨 Displaying image with markers...")
            try:
                coords = [
                    [int(s.strip()) for s in coord.split('|')]
                    for coord in coord_str.split(';')
                ]
                with Image.open(image_path) as img:
                    draw = ImageDraw.Draw(img)
                    for i, (h, v, _) in enumerate(coords):
                        # Draw star at each (h, v)
                        points = []
                        star_size = 20
                        for j in range(5):
                            angle = math.radians(j * 144 - 90)
                            outer_x = h + star_size * math.cos(angle)
                            outer_y = v + star_size * math.sin(angle)
                            points.append((outer_x, outer_y))
                        draw.polygon(points, fill="yellow", outline="red")
                        print(f"   ✓ Marked object {i+1} at coordinates ({h}, {v})")
                    img.show()
                    print(f"   ✓ Image displayed with {len(coords)} marker(s)")
            except Exception as e:
                print(f"   ❌ Could not plot markers: {e}")

    except ValueError as ve:
        error_msg = str(ve)
        print(f"\n❌ Input Error: {error_msg}")
        text_to_speech(error_msg)
    except Exception as e:
        error_msg = f"System Error: {str(e)}"
        print(f"\n❌ {error_msg}")
        text_to_speech(error_msg)
    finally:
        if 'overall_start_time' in locals():
            final_end_time = time.time()
            total_runtime = final_end_time - overall_start_time
            print(f"\n🏁 Session ended. Total runtime: {total_runtime:.2f} seconds")

if __name__ == "__main__":
    main()
