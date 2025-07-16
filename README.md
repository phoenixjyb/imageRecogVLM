# VLM Object Recognition System (3-Mode)

A comprehensive multi-modal Vision Language Model (VLM) system that supports object detection and localization through three different processing pathways: cloud-based Grok-4, cloud-based Qwen-VL, and local LLaVA via Ollama.

## 🌟 Features

### Multi-VLM Support
- **☁️ Grok-4** - High accuracy cloud processing via X.AI API
- **☁️ Qwen-VL** - Excellent Chinese language support via DashScope API  
- **🖥️ LLaVA** - Privacy-focused local processing via Ollama

### Language Support
- **🌍 Bilingual Commands** - Supports both English and Chinese input
- **🔄 Auto-Translation** - Automatic Chinese-to-English translation with pattern matching
- **🎯 Smart Object Extraction** - Intelligent parsing of natural language commands

### Advanced Processing
- **📐 Original Resolution** - Processes images at full resolution for maximum accuracy
- **🎯 Precise Coordinates** - Pixel-perfect object localization with visual markers
- **🔊 Audio Feedback** - Text-to-speech responses using macOS built-in `say` command
- **🖼️ Visual Annotation** - Displays detected objects with yellow star markers

### System Architecture
- **🔧 Modular Design** - Clean separation between VLM providers
- **⚡ Smart Fallbacks** - Graceful error handling and alternative pathways
- **📊 Performance Monitoring** - Detailed timing and processing statistics

## 🚀 Quick Start

### Prerequisites

1. **Python Dependencies**
```bash
pip install requests pillow openai python-dotenv
```

2. **Environment Variables**
```bash
export XAI_API_KEY="your_x_ai_api_key"          # For Grok-4
export DASHSCOPE_API_KEY="your_dashscope_key"   # For Qwen-VL
```

3. **Local Processing (Optional)**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install LLaVA model
ollama pull llava:latest

# Start Ollama service
ollama serve
```

### Basic Usage

```bash
python3 imageRecogVLM.py
```

**English Commands:**
```
"please grab the apple to me"
"find the red coke bottle"
"identify the book on the shelf"
```

**Chinese Commands:**
```
"请帮我拿可乐给我"
"找苹果给我"
"帮我找书"
```

## 🏗️ System Architecture

### Processing Flow
1. **Input Processing** - Language detection and translation
2. **VLM Selection** - Interactive choice between 3 processing modes
3. **Image Encoding** - High-quality base64 encoding at original resolution
4. **API Calling** - Provider-specific prompt optimization and API calls
5. **Response Parsing** - Coordinate extraction and validation
6. **Output Generation** - Comprehensive response with visual and audio feedback

### VLM Comparison

| Feature | Grok-4 | Qwen-VL | LLaVA (Local) |
|---------|---------|---------|---------------|
| **Accuracy** | High | Good | Moderate |
| **Speed** | Medium | Medium | Fast |
| **Cost** | Paid | Paid | Free |
| **Privacy** | Cloud | Cloud | Local |
| **Chinese Support** | Basic | Excellent | Limited |
| **Internet Required** | Yes | Yes | No |

## 📁 Project Structure

```
vlmTry/
├── imageRecogVLM.py          # Main application
├── sampleImages/             # Test images directory
│   ├── image_000078.jpg
│   └── image_000354.jpg
├── hello_qwen.py            # Qwen API test script
├── README.md                # This file
└── system_arch_new.mmd      # System architecture diagram
```

## 🔧 Configuration

### Image Processing
- **Resolution**: Uses original image resolution for maximum accuracy
- **Quality**: High-quality JPEG encoding (95% for originals)
- **Format**: Base64 encoding for API transmission

### API Endpoints
- **Grok-4**: `https://api.x.ai/v1/chat/completions`
- **Qwen-VL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **LLaVA**: `http://localhost:11434/api/generate` (local)

## 🌏 Chinese Language Support

### Supported Patterns

**Command Patterns:**
- `请.*?拿.*?给我` → "please grab {} to me"
- `帮我.*?拿.*` → "help me get {}"
- `找.*?给我` → "find {} for me"
- `给我.*?拿` → "get me {}"
- `请.*?找` → "please find {}"
- `帮我.*?找` → "help me find {}"

**Object Vocabulary:**
- `可乐|可口可乐` → "coke"
- `苹果` → "apple"
- `书|书本` → "book"
- `瓶子|水瓶` → "bottle"
- `钥匙` → "keys"
- `手机|电话` → "phone"
- And more...

### Adding New Vocabulary

To extend Chinese support, edit the `chinese_patterns` dictionary in `translate_chinese_to_english()`:

```python
chinese_patterns = {
    # Add new command patterns
    r'我想要.*': 'I want {}',
    
    # Add new object translations
    r'橙子|橘子': 'orange',
    r'香蕉': 'banana',
}
```

## 📊 Output Format

### Console Output
```
🤖 VLM Object Recognition System (3-Mode)
============================================================
🕐 Process started at: 2025-01-16 14:30:25

💬 Enter your command: 请帮我拿可乐给我

🌏 Original Chinese command: '请帮我拿可乐给我'
🔄 Translated English command: 'please grab coke to me'
✅ Using translated command for processing

🎯 Target object identified: 'coke'
📂 Loading image: image_000354.jpg
   ✓ Image loaded successfully: 1024x768

🔧 Building prompt for VLM...
   ✓ Using resolution: 1024x768 (original size)

[VLM Selection Menu]
Choose processing mode (1 for Grok, 2 for Qwen, 3 for Local): 2

🚀 Calling Qwen-VL Vision API (Cloud)...
📡 Qwen API response received in 2.34 seconds
✅ Total Qwen API process completed in 3.12 seconds

🔍 Starting coordinate parsing...
   📊 No scaling needed - using original coordinates
   🎯 Row 1: Direct coordinates(520,340) [ID: 1]
✅ Successfully extracted 1 valid coordinate(s)

📬 Response:
==================================================
coke is recognized, let me fetch it to you

==================================================
📄 ORIGINAL QWEN-VL MODEL OUTPUT:
==================================================
[VLM response content]
==================================================

📊 COORDINATE SUMMARY TABLE:
----------------------------------------
| Object ID | H (Horizontal) | V (Vertical) |
|-----------|----------------|--------------|
|     1     |        520     |      340     |
----------------------------------------

🔊 Audio played: 'coke found'
🖼️ Showing image with annotated object location...
✅ Process ended at: 2025-01-16 14:30:32
```

### Visual Output
- **Yellow star markers** placed at detected object center points
- **Image display** with annotation overlay
- **Coordinate validation** ensures markers are within image bounds

## 🛠️ Troubleshooting

### Common Issues

**API Key Errors:**
```bash
# Set environment variables
export XAI_API_KEY="your_key_here"
export DASHSCOPE_API_KEY="your_key_here"
```

**Ollama Connection Issues:**
```bash
# Check Ollama status
ollama list

# Restart Ollama service
ollama serve

# Install missing models
ollama pull llava:latest
```

**Audio Issues:**
- Uses macOS built-in `say` command
- Automatically falls back to text-only if TTS fails
- Can be disabled by setting `tts_enabled = False`

### Performance Optimization

**For High Accuracy:**
- Use Grok-4 for best results
- Use original image resolution
- Provide specific object descriptions

**For Speed:**
- Use local LLaVA processing
- Enable image resizing if needed
- Use shorter, simpler commands

**For Chinese Processing:**
- Use Qwen-VL for best Chinese language support
- Expand `chinese_patterns` for domain-specific vocabulary
- Test translations before processing

## 📈 Performance Metrics

Typical processing times:
- **Grok-4**: 3-8 seconds (depending on image size)
- **Qwen-VL**: 2-5 seconds (good optimization)
- **LLaVA Local**: 1-3 seconds (fastest, hardware dependent)

## 🤝 Contributing

To extend the system:

1. **Add new VLM providers** by implementing the API call pattern
2. **Expand language support** by adding patterns to translation functions
3. **Improve object detection** by optimizing prompts for specific use cases
4. **Add new output formats** by extending the response generation

## 📄 License

This project is open source. Please ensure you comply with the terms of service for any commercial VLM APIs you use.

## 🙏 Acknowledgments

- **X.AI** for Grok-4 API access
- **Alibaba Cloud** for Qwen-VL via DashScope
- **Ollama** for local LLaVA processing infrastructure
- **OpenAI** for compatible API standards