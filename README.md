# README.md: VLM Object Recognition and Star Plotting

## Project Overview
This Python program integrates with a Vision-Language Model (VLM), such as Grok4 from xAI, to recognize objects in images based on user text commands and visually mark them with stars. It processes inputs like "please grab the coke cola to me", extracts the object (e.g., "coke cola"), queries the VLM via API with an image, parses coordinates (H for horizontal, V for vertical; origin at top-left), handles multiple objects with unique IDs, generates recognition responses, and outputs via text and Text-to-Speech (TTS).

Key Features:
- Object extraction from natural language commands.
- API integration with Grok4 for multimodal (text + image) processing.
- Coordinate parsing with support for single/multiple objects.
- Success/failure responses with TTS playback.
- Predefined image path for simplicity.
- Visual marking of detected objects on the image.

The program is designed for modularity and can be extended for robotics or assistive tech applications.

## System Requirements
- Python 3.x
- Libraries: `requests`, `re`, `random`, `base64`, `PIL` (Pillow), `gtts`, `pygame`
- Environment variable: `GROK4_API_KEY` (set your xAI API key)
- Internet access for API calls and TTS (gTTS requires online synthesis)

Installation:
```bash
pip install requests pillow gtts pygame
```

## Usage
1. **Set your API key**  
   Export your API key as an environment variable:
   ```sh
   export GROK4_API_KEY=your_key_here
   ```

2. **Prepare your image**  
   Place your image in the `sampleImages` directory and update the filename in `imageRecogVLM.py` if needed.

3. **Run the script**  
   ```sh
   python imageRecogVLM.py
   ```

4. **Interact**  
   When prompted, enter a command such as:
   ```
   please grab the coke cola to me
   ```

5. **Result**  
   - The script will print and speak the recognition result.
   - If objects are found, it will display the image with yellow stars marking each detected object.

## How It Works
- **Prompt Construction:**  
  The script builds a prompt for the VLM, specifying the object and requesting a Markdown table of coordinates.

- **API Call:**  
  The image is encoded (resized to 256px width for the API, but coordinates are not rescaled for plotting) and sent to the VLM API. The response is expected to contain a table like:
  ```
  | H | V | ID |
  |---|---|----|
  | 320 | 200 | 1 |
  | 400 | 210 | 2 |
  ```

- **Parsing and Plotting:**  
  The script parses all coordinate rows and draws a 5-pointed yellow star at each `(H, V)` position on the image. If multiple objects are detected, all are marked.

- **No Resizing for Plotting:**  
  The coordinates are used as-is, matching the original image size.

## Example Output
- **Terminal:**
  ```
  coke cola is recognized, let me fetch it to you

  Raw Text Output:
  320 | 200 | 1; 400 | 210 | 2
  ```
- **Image:**  
  The displayed image will have yellow stars at (320, 200) and (400, 210).

## Notes
- The script expects the VLM API to return coordinates in the same resolution as the original image.
- If no object is found, the script will say so and not plot any stars.
- Multiple objects are supported and will each be marked with a yellow star.