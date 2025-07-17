# VLM Object Recognition System - Modular Architecture

🤖 A professional, modular Vision Language Model (VLM) object recognition system with support for multiple providers, voice input, and advanced image annotation.

## 🌟 Features

- **Multi-VLM Support**: Grok-4 (X.AI), Qwen-VL (Alibaba), LLaVA (local)
- **Voice Input**: Speech recognition with multilingual support and fallbacks
- **Advanced Parsing**: Sophisticated coordinate parsing for different VLM response formats
- **Image Annotation**: Professional annotation with bounding boxes and star markers
- **Text-to-Speech**: Cross-platform TTS support
- **Modular Design**: Clean, maintainable, and extensible architecture

## 🏗️ Architecture

This is the **modular version** of the VLM Object Recognition System, completely refactored from the original monolithic implementation into a professional, maintainable architecture.

```
📁 vlm_modular/
├── 🔧 config/         # Configuration and API management
├── 🎤 input/          # Voice and text processing
├── 🤖 vlm/            # VLM provider implementations
├── 🖼️ image/          # Image processing and annotation
├── 🔊 output/         # Response generation and TTS
├── 🛠️ utils/          # Utility functions
└── 🚀 main.py        # Application entry point
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/phoenixjyb/imageRecogVLM.git
cd imageRecogVLM

# Switch to modular architecture branch
git checkout modular-architecture

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup API Keys

```bash
# For Grok (X.AI)
export XAI_API_KEY="your_grok_api_key"

# For Qwen (Alibaba)
export DASHSCOPE_API_KEY="your_qwen_api_key"

# For LLaVA (local) - install Ollama
brew install ollama  # macOS
ollama pull llava
ollama serve
```

### 3. Run the System

```bash
cd vlm_modular
python main.py
```

## 🎯 Supported Providers

| Provider | Type | API Key Required | Best For |
|----------|------|------------------|----------|
| **Grok** (X.AI) | Cloud | ✅ XAI_API_KEY | High accuracy, latest models |
| **Qwen** (Alibaba) | Cloud | ✅ DASHSCOPE_API_KEY | Good table parsing, Chinese support |
| **LLaVA** | Local | ❌ (Ollama) | Privacy, offline use, no costs |

## 📖 Documentation

- 📚 **[Detailed Documentation](vlm_modular/README.md)** - Complete usage guide
- 🧪 **Testing**: Run `python vlm_modular/test_system.py`
- 🎤 **Voice Input**: Supports English and Chinese with fallbacks
- 🔊 **TTS**: Cross-platform text-to-speech (macOS, Linux, Windows)

## 🆚 Architecture Comparison

| Feature | Original (master) | Modular (this branch) |
|---------|-------------------|----------------------|
| **Structure** | Single 1000+ line file | 6 modular packages (24+ files) |
| **Maintainability** | ❌ Hard to modify | ✅ Easy to update components |
| **Testing** | ❌ Monolithic testing | ✅ Component-level testing |
| **Extensibility** | ❌ Hard to add providers | ✅ Simple to add new VLMs |
| **Code Quality** | ❌ Mixed concerns | ✅ Clean separation |
| **Documentation** | ❌ Basic | ✅ Comprehensive |

## 🔧 Configuration

Environment variables for customization:

```bash
export VLM_DEFAULT_PROVIDER="grok"    # Default VLM provider
export VLM_ENABLE_VOICE="true"        # Enable voice input
export VLM_ENABLE_TTS="true"          # Enable text-to-speech
export VLM_IMAGE_WIDTH="640"          # Output image width
export VLM_IMAGE_HEIGHT="480"         # Output image height
export VLM_DEBUG="false"              # Enable debug logging
```

## 📊 Performance

The modular architecture provides:
- **Better Error Handling**: Graceful failures with specific error messages
- **Improved Parsing**: 6+ coordinate format patterns supported
- **Enhanced Reliability**: Retry mechanisms and fallbacks
- **Professional Logging**: Comprehensive debugging support

## 🤝 Contributing

This modular architecture makes contributing easy:

1. **Add new VLM providers**: Extend the `vlm/` package
2. **Improve parsing**: Enhance `image/coordinate_parser.py`
3. **Add input methods**: Extend the `input/` package
4. **Enhance output**: Improve `output/` components

## 📜 License

This project is provided for educational and research purposes.

## 🔗 Links

- **Original Version**: See `master` branch
- **Issues & Features**: [GitHub Issues](https://github.com/phoenixjyb/imageRecogVLM/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/phoenixjyb/imageRecogVLM/pulls)

---

**Note**: This is the modular architecture branch. For the original monolithic implementation, switch to the `master` branch.
