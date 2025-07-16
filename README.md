# VLM Image Recognition Script

A Python script that uses Vision Language Models (VLMs) to analyze images and identify objects within them. Supports both cloud-based and local processing modes.

## Features

- **Dual-Mode Processing**: Choose between cloud (X.AI Grok-4) and local (Ollama LLaVA) VLM processing
- **Object Recognition**: Analyzes images to identify and locate objects
- **Coordinate Detection**: Provides x,y coordinates of identified objects with dynamic scaling
- **Confidence Scores**: Returns confidence levels for each detection
- **Visual Feedback**: Draws markers on detected objects and saves annotated images
- **Audio Feedback**: Text-to-speech announcement of results
- **Coefficient-Controlled Sizing**: Configurable image resizing with unified dimensions across modes
- **Proxy Bypass**: Automatic proxy bypass for local Ollama connections
- **Comprehensive Logging**: Detailed logging of all operations with timing information

## System Requirements
- Python 3.7+
- **For Cloud Mode**: X.AI API key (sign up at X.AI)
- **For Local Mode**: Ollama with LLaVA model installed
- Libraries: `requests`, `pillow`, `base64`, `sys`, `subprocess`, `pathlib`
- Text-to-speech: `espeak` or `festival` (Linux/macOS)

## Installation
1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Cloud Mode Setup
Set up your X.AI API key as an environment variable:
```bash
export XAI_API_KEY="your_api_key_here"
```

### Local Mode Setup
Install and configure Ollama with LLaVA:
```bash
# Install Ollama (visit https://ollama.ai for instructions)
# Pull the LLaVA model
ollama pull llava
```

## Usage

### Cloud Mode (Default)
```bash
python imageRecogVLM.py path/to/your/image.jpg
```

### Local Mode
```bash
python imageRecogVLM.py path/to/your/image.jpg --local
```

The script will:
1. Load and resize the image for optimal processing
2. Send the image to the selected VLM (cloud or local) for analysis
3. Parse the response to extract object information
4. Draw star markers on detected objects with coordinate scaling
5. Save the annotated image
6. Provide text-to-speech feedback
7. Log all results with comprehensive timing information

## Configuration

You can modify several constants at the top of the script:

- `RESIZE_WIDTH`: Target width for image processing (default: 256px)
- `LOCAL_RESIZE_COEFFICIENT`: Coefficient for local mode sizing (default: 1.0)
- `RESIZE_QUALITY`: JPEG quality for compression (default: 85)
- Various timeout and retry settings for both cloud and local modes


## Output
The script generates:
- **Console Output**: Detailed logging of object detection results with coordinates and confidence scores
- **Annotated Image**: Original image with star markers on detected objects (`annotated_output.jpg`)
- **Audio Feedback**: Spoken confirmation of detection results
- **Timing Information**: Performance metrics for both processing modes

## Example Output
```
2024-01-15 10:30:45 - Processing image: sampleImages/image_000078.jpg
2024-01-15 10:30:45 - Using LOCAL mode with Ollama LLaVA
2024-01-15 10:30:45 - Image resized to 256x192 (original: 640x480)
2024-01-15 10:30:47 - LOCAL API Response time: 2.15 seconds
2024-01-15 10:30:47 - Found 2 objects:
  - bottle (confidence: 0.85) at (128, 96) → scaled to (320, 240)
  - cup (confidence: 0.72) at (200, 150) → scaled to (500, 375)
2024-01-15 10:30:48 - Annotated image saved as: annotated_output.jpg
```

## Troubleshooting

### Cloud Mode Issues
- Verify `XAI_API_KEY` environment variable is set correctly
- Check internet connectivity
- Ensure API quota is not exceeded

### Local Mode Issues
- Verify Ollama is running: `ollama list`
- Check if LLaVA model is installed: `ollama pull llava`
- Ensure port 11434 is available
- Check proxy settings if behind corporate firewall

### General Issues
- Verify image file exists and is in supported format (JPG, PNG)
- Check Python dependencies are installed
- Ensure text-to-speech system is available (`espeak` or `festival`)

## Technical Notes

- **Coordinate System**: Origin (0,0) at top-left, coordinates scaled from processed to original image dimensions
- **Image Processing**: Maintains aspect ratio during resizing
- **Proxy Handling**: Automatic bypass for localhost connections in local mode
- **Error Handling**: Comprehensive exception handling with fallback responses
- **Performance**: Local mode typically faster for repeated queries, cloud mode for occasional use

## Extending the Script

The script is designed for modularity. You can:
- Add new VLM providers by implementing the API interface pattern
- Modify the prompt template for different detection tasks
- Customize the visual marking system (stars, boxes, etc.)
- Integrate with robotic control systems using the coordinate output
- Add support for batch processing multiple images



## Notes
- The script expects the VLM API to return coordinates in the same resolution as the original image.
- If no object is found, the script will say so and not plot any stars.
- Multiple objects are supported and will each be marked with a yellow star.