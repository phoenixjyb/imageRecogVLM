# VLM Object Recognition System (Modular Version)

A modular Vision Language Model (VLM) object recognition system that supports multiple VLM providers, voice input, and image annotation.

## Features

- **Multiple VLM Support**: Grok-4 (X.AI), Qwen-VL (Alibaba), LLaVA (local)
- **Voice Input**: Speech recognition with fallback support
- **Image Processing**: Automatic resizing, base64 encoding, and annotation
- **Coordinate Parsing**: Advanced parsing for different VLM response formats
- **Text-to-Speech**: Multi-platform TTS support
- **Modular Architecture**: Clean separation of concerns across packages

## Directory Structure

```
vlm_modular/
├── config/                 # Configuration and API key management
│   ├── __init__.py
│   ├── api_keys.py        # API key handling
│   └── settings.py        # Application settings
├── input/                 # Input handling (voice and text)
│   ├── __init__.py
│   ├── text_processor.py  # Text processing and translation
│   └── voice_handler.py   # Voice input handling
├── vlm/                   # VLM provider implementations
│   ├── __init__.py
│   ├── base.py           # Base VLM client interface
│   ├── factory.py        # VLM client factory
│   ├── grok_client.py    # X.AI Grok implementation
│   ├── llava_client.py   # LLaVA local implementation
│   └── qwen_client.py    # Alibaba Qwen implementation
├── image/                # Image processing and annotation
│   ├── __init__.py
│   ├── annotator.py      # Image annotation with stars/boxes
│   ├── coordinate_parser.py # Advanced coordinate parsing
│   └── processor.py      # Image loading and processing
├── output/               # Output generation and TTS
│   ├── __init__.py
│   ├── response_generator.py # Human-readable response generation
│   └── tts_handler.py    # Text-to-speech handling
├── utils/                # Utility functions
│   └── __init__.py
└── main.py              # Main application entry point
```

## Installation

1. Install required packages:
```bash
pip install pillow requests speech_recognition
```

2. Set up API keys as environment variables:
```bash
export XAI_API_KEY="your_grok_api_key"
export DASHSCOPE_API_KEY="your_qwen_api_key"
```

3. For LLaVA support, install and run Ollama:
```bash
# Install Ollama (see https://ollama.ai/)
ollama pull llava
ollama serve
```

## Usage

### Basic Usage

```python
from vlm_modular.main import VLMObjectRecognition

# Initialize system
vlm_system = VLMObjectRecognition()

# Run object detection
result = vlm_system.run_object_detection(
    image_path="/path/to/image.jpg",
    query="red car",
    provider="grok"
)

print(f"Found {result['objects_found']} objects")
```

### Command Line Usage

```bash
cd vlm_modular
python main.py
```

### Configuration

You can configure the system using environment variables:

```bash
export VLM_DEFAULT_PROVIDER="grok"    # Default VLM provider
export VLM_ENABLE_VOICE="true"        # Enable voice input
export VLM_ENABLE_TTS="true"          # Enable text-to-speech
export VLM_IMAGE_WIDTH="640"          # Output image width
export VLM_IMAGE_HEIGHT="480"         # Output image height
export VLM_DEBUG="false"              # Enable debug logging
```

## Supported VLM Providers

### 1. Grok (X.AI)
- **API Key**: Set `XAI_API_KEY` environment variable
- **Model**: grok-vision-beta
- **Features**: High-quality object detection with precise coordinates

### 2. Qwen (Alibaba)
- **API Key**: Set `DASHSCOPE_API_KEY` environment variable  
- **Model**: qwen-vl-max-0809
- **Features**: Good table format parsing, ratio coordinate support

### 3. LLaVA (Local)
- **Setup**: Requires Ollama with LLaVA model
- **Model**: llava
- **Features**: Local processing, no API key required

## Voice Input

The system supports voice input with automatic fallback:

1. **Online Recognition**: Google Speech Recognition
2. **Offline Recognition**: Sphinx (if available)
3. **Keyword Fallback**: Predefined object keywords

Supported languages: English (en-US), Chinese (zh-CN)

## Image Processing

- **Input**: Various image formats (JPEG, PNG, etc.)
- **Resizing**: Automatic resize to 640x480 (configurable)
- **Annotation**: Star markers and bounding boxes
- **Output**: Annotated images with detection results

## Text-to-Speech

Multi-platform TTS support:

- **macOS**: `say` command
- **Linux**: espeak, festival, speech-dispatcher
- **Windows**: PowerShell SAPI

## Advanced Features

### Coordinate Parsing

The system includes advanced coordinate parsing that handles:

- Bracket format: `[x1, y1, x2, y2]`
- Parentheses format: `(x1, y1, x2, y2)`
- Bounding box format: `bbox: [coordinates]`
- Table format: Markdown tables with coordinates
- Ratio coordinates: Decimal values converted to pixels
- Descriptive locations: "top left", "center", etc.

### Response Generation

Generates human-readable responses including:

- Object count and confidence levels
- Location descriptions (top, bottom, left, right, center)
- Provider-specific information
- Detailed technical reports

### Error Handling

Robust error handling with:

- API failure recovery
- Coordinate validation
- Image processing fallbacks
- Logging and debugging support

## Development

### Adding New VLM Providers

1. Create a new client class inheriting from `VLMClient`
2. Implement `query_image()` and `parse_response()` methods
3. Add the provider to `VLMFactory`
4. Update configuration settings

### Extending Functionality

The modular architecture makes it easy to:

- Add new input methods (keyboard, file, etc.)
- Implement additional image processing features
- Create new output formats (JSON, XML, etc.)
- Add custom coordinate parsing patterns

## Logging

The system provides comprehensive logging:

```python
# Enable debug logging
export VLM_DEBUG="true"

# Log files
vlm_system.log  # Main application log
```

## Troubleshooting

### Common Issues

1. **No API Key Found**
   - Set the appropriate environment variable
   - Check variable name spelling

2. **LLaVA Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check if LLaVA model is installed: `ollama list`

3. **Voice Input Not Working**
   - Check microphone permissions
   - Install speech_recognition dependencies
   - Disable voice input: `export VLM_ENABLE_VOICE="false"`

4. **TTS Not Working**
   - Check system TTS availability
   - Disable TTS: `export VLM_ENABLE_TTS="false"`

### Performance Tips

- Use appropriate image sizes (640x480 default)
- Enable debug logging only when needed
- Cache VLM responses for repeated queries
- Use local LLaVA for offline processing

## License

This project is provided as-is for educational and research purposes.
