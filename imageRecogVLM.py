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

# Securely load API key from environment variable
API_KEY = os.getenv('XAI_API_KEY')
if not API_KEY:
    raise ValueError("XAI_API_KEY environment variable not set.")

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
    
    # Fallback: Look for 'the [object]' and take the phrase after 'the'
    if 'the' in input_text:
        idx = input_text.index('the') + len('the')
        object_str = input_text[idx:].strip().split()[0]
        return object_str
    
    # Ultimate fallback: Take the last noun-like word
    words = input_text.split()
    if words:
        return words[-1].strip()
    
    raise ValueError("Could not extract object from input text. Please use a format like 'please grab the [object] to me' or 'identify the [object]'.")

def build_prompt(object_str: str, image_width: int, image_height: int) -> str:
    """
    Build the augmented prompt for the VLM, including the resized image resolution, and request a table.
    """
    return (
        f"please use the vlm such as grok4 to read the image provided, which has been resized to a resolution of {image_width}x{image_height} pixels, "
        f"and locate the object of interest '{object_str}' (specifically looking for Coca-Cola cans with red color and white logo). "
        f"Please summarize the coordinates in a concise table with columns 'H', 'V', and 'ID' for each instance found. If no object is found, return a table with 'H', 'V', 'ID' values of 0, 0, 0."
    )

def encode_image(image_path: str) -> tuple[str, int, int, int, int]:
    """
    Encode image to base64 after preprocessing to resize to 256px width, maintaining aspect ratio.
    Returns the base64 string and original/new dimensions.
    """
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        original_width, original_height = img.size
        new_width = 256
        aspect_ratio = original_height / original_width
        new_height = int(new_width * aspect_ratio)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            resized_img.save(temp_file, format='JPEG', quality=85)
            temp_file.seek(0)
            base64_data = base64.b64encode(temp_file.read()).decode('utf-8')
        os.unlink(temp_file.name)
        return base64_data, original_width, original_height, new_width, new_height

def call_grok4_api(prompt: str, image_path: str, api_key: str) -> str:
    """
    Call Grok4 API with prompt and image, with retry logic.
    Returns raw text content for display.
    """
    base64_image, original_width, original_height, new_width, new_height = encode_image(image_path)
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-4-0709",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
    }
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    print("Sending API request...")
    
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    
    try:
        response = session.post(url, headers=headers, json=payload, proxies=proxies, timeout=120)
        print(f"Raw API response (text): {response.json()['choices'][0]['message']['content']}")
        print(f"API response status: {response.status_code}")
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.text}")
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed after retries: {str(e)}")

def parse_response(response_text: str, object_str: str) -> tuple[str, bool]:
    """
    Parse VLM response for coordinates from a table, rescale to original resolution (640x480).
    Returns formatted table string and recognized flag.
    """
    print(f"Parsing response: {response_text}")
    # Find all table rows (skip header and separator)
    lines = [line.strip() for line in response_text.strip().split('\n')]
    data_rows = []
    for line in lines:
        if re.match(r'^\|\s*\d+', line):  # Row starts with | and a number
            data_rows.append(line)
    if not data_rows:
        return "0 | 0 | 0", False

    coordinates = []
    for row in data_rows:
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        print(f"Raw cells from row '{row}': {cells}")  # Debug the extracted cells
        if len(cells) >= 3:
            try:
                h = int(cells[0])
                v = int(cells[1])
                id_num = cells[2] if cells[2].isdigit() else "0"
                # Rescale coordinates to original resolution (640x480)
                original_width, original_height = 640, 480
                new_width, new_height = 256, 192
                scaled_h = int(h * (original_width / new_width))
                scaled_v = int(v * (original_height / new_height))
                coordinates.append((scaled_h, scaled_v, id_num))
                print(f"Extracted and scaled: H={scaled_h}, V={scaled_v}, ID={id_num}")
            except Exception as e:
                print(f"Skipping invalid row due to {e}: {row}")

    if not coordinates:
        return "0 | 0 | 0", False

    recognized = True
    if len(coordinates) == 1:
        h, v, id_num = coordinates[0]
        return f"{h} | {v} | {id_num}", recognized
    else:
        coord_str = "; ".join([f"{h} | {v} | {id_num}" for h, v, id_num in coordinates])
        return coord_str, recognized

def generate_response(object_str: str, recognized: bool, coord_str: str) -> str:
    """
    Generate textual response based on recognition, including a concise table.
    """
    if recognized:
        return f"{object_str} is recognized, let me fetch it to you\n\nRaw Text Output:\n{coord_str}"
    else:
        return "sorry, I cannot locate it\n\nRaw Text Output:\n0 | 0 | 0"

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

def main():
    """
    Main function to orchestrate the process.
    Now interactive: prompts user for input; image path is predefined with specific image name.
    """
    try:
        user_input = input("Enter your command (e.g., 'please grab the coke cola to me'): ").strip()
        image_dir = "/Users/yanbo/Projects/vlmTry/sampleImages"
        image_name = "image_000078.jpg"
        image_path = os.path.join(image_dir, image_name)
        
        with Image.open(image_path) as img:
            width, height = img.size
            print(f"Image loaded: {width}x{height}")
        
        object_str = extract_object(user_input)
        prompt = build_prompt(object_str, 256, 192)
        response_text = call_grok4_api(prompt, image_path, API_KEY)
        coord_str, recognized = parse_response(response_text, object_str)
        resp_text = generate_response(object_str, recognized, coord_str)
        print(resp_text)
        text_to_speech(resp_text)

        # --- Show image with star if coordinates are valid ---
        if recognized and coord_str != "0 | 0 | 0":
            try:
                coords = [
                    [int(s.strip()) for s in coord.split('|')]
                    for coord in coord_str.split(';')
                ]
                with Image.open(image_path) as img:
                    draw = ImageDraw.Draw(img)
                    for h, v, _ in coords:
                        # Draw star at each (h, v)
                        points = []
                        star_size = 20
                        for i in range(5):
                            angle = math.radians(i * 144 - 90)
                            outer_x = h + star_size * math.cos(angle)
                            outer_y = v + star_size * math.sin(angle)
                            points.append((outer_x, outer_y))
                        draw.polygon(points, fill="yellow", outline="red")
                    img.show()
            except Exception as e:
                print(f"Could not plot star: {e}")

    except ValueError as ve:
        error_msg = str(ve)
        print(error_msg)
        text_to_speech(error_msg)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        text_to_speech(error_msg)

if __name__ == "__main__":
    main()