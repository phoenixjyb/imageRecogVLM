# VLM 物体识别系统（三模式）

一个综合性的多模态视觉语言模型（VLM）系统，支持通过三种不同的处理路径进行物体检测和定位：基于云端的 Grok-4、基于云端的 Qwen-VL，以及通过 Ollama 的本地 LLaVA。

## 🌟 功能特性

### 多 VLM 支持
- **☁️ Grok-4** - 通过 X.AI API 进行高精度云端处理
- **☁️ Qwen-VL** - 通过 DashScope API 提供出色的中文语言支持  
- **🖥️ LLaVA** - 通过 Ollama 进行注重隐私的本地处理

### 语言支持
- **🌍 双语命令** - 支持中文和英文输入
- **🔄 自动翻译** - 基于模式匹配的中文到英文自动翻译
- **🎯 智能物体提取** - 自然语言命令的智能解析

### 高级处理
- **📐 原始分辨率** - 以全分辨率处理图像以获得最大精度
- **🎯 精确坐标** - 像素级精确的物体定位与视觉标记
- **🔊 音频反馈** - 使用 macOS 内置 `say` 命令的文本转语音响应
- **🖼️ 视觉标注** - 用黄色星形标记显示检测到的物体

### 系统架构
- **🔧 模块化设计** - VLM 提供商之间的清晰分离
- **⚡ 智能回退** - 优雅的错误处理和替代路径
- **📊 性能监控** - 详细的计时和处理统计

## 🚀 快速开始

### 前置要求

1. **Python 依赖**
```bash
pip install requests pillow openai python-dotenv
```

2. **环境变量**
```bash
export XAI_API_KEY="your_x_ai_api_key"          # 用于 Grok-4
export DASHSCOPE_API_KEY="your_dashscope_key"   # 用于 Qwen-VL
```

3. **本地处理（可选）**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 安装 LLaVA 模型
ollama pull llava:latest

# 启动 Ollama 服务
ollama serve
```

### 基本用法

```bash
python3 imageRecogVLM.py
```

**英文命令：**
```
"please grab the apple to me"
"find the red coke bottle"
"identify the book on the shelf"
```

**中文命令：**
```
"请帮我拿可乐给我"
"找苹果给我"
"帮我找书"
```

## 🏗️ 系统架构

### 处理流程
1. **输入处理** - 语言检测和翻译
2. **VLM 选择** - 3种处理模式的交互式选择
3. **图像编码** - 原始分辨率的高质量 base64 编码
4. **API 调用** - 特定提供商的提示优化和 API 调用
5. **响应解析** - 坐标提取和验证
6. **输出生成** - 包含视觉和音频反馈的综合响应

### VLM 比较

| 功能特性 | Grok-4 | Qwen-VL | LLaVA（本地）|
|---------|---------|---------|---------------|
| **准确性** | 高 | 良好 | 中等 |
| **速度** | 中等 | 中等 | 快速 |
| **成本** | 付费 | 付费 | 免费 |
| **隐私** | 云端 | 云端 | 本地 |
| **中文支持** | 基础 | 优秀 | 有限 |
| **需要网络** | 是 | 是 | 否 |

## 📁 项目结构

```
vlmTry/
├── imageRecogVLM.py          # 主应用程序
├── sampleImages/             # 测试图像目录
│   ├── image_000078.jpg
│   └── image_000354.jpg
├── hello_qwen.py            # Qwen API 测试脚本
├── README.md                # 英文说明文档
├── README_CN.md             # 中文说明文档
└── system_arch_new.mmd      # 系统架构图
```

## 🔧 配置

### 图像处理
- **分辨率**：使用原始图像分辨率以获得最大精度
- **质量**：高质量 JPEG 编码（原始图像 95%）
- **格式**：用于 API 传输的 Base64 编码

### API 端点
- **Grok-4**：`https://api.x.ai/v1/chat/completions`
- **Qwen-VL**：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **LLaVA**：`http://localhost:11434/api/generate`（本地）

## 🌏 中文语言支持

### 支持的模式

**命令模式：**
- `请.*?拿.*?给我` → "please grab {} to me"
- `帮我.*?拿.*` → "help me get {}"
- `找.*?给我` → "find {} for me"
- `给我.*?拿` → "get me {}"
- `请.*?找` → "please find {}"
- `帮我.*?找` → "help me find {}"

**物体词汇：**
- `可乐|可口可乐` → "coke"
- `苹果` → "apple"
- `书|书本` → "book"
- `瓶子|水瓶` → "bottle"
- `钥匙` → "keys"
- `手机|电话` → "phone"
- 更多...

### 添加新词汇

要扩展中文支持，请编辑 `translate_chinese_to_english()` 中的 `chinese_patterns` 字典：

```python
chinese_patterns = {
    # 添加新的命令模式
    r'我想要.*': 'I want {}',
    
    # 添加新的物体翻译
    r'橙子|橘子': 'orange',
    r'香蕉': 'banana',
}
```

## 📊 输出格式

### 控制台输出
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
可乐已识别，让我为您取来

==================================================
📄 原始 QWEN-VL 模型输出：
==================================================
[VLM 响应内容]
==================================================

📊 坐标汇总表：
----------------------------------------
| 物体 ID | H（水平） | V（垂直） |
|-----------|----------------|--------------|
|     1     |        520     |      340     |
----------------------------------------

🔊 已播放音频：'可乐已找到'
🖼️ 显示带有标注物体位置的图像...
✅ 进程结束于：2025-01-16 14:30:32
```

### 视觉输出
- **黄色星形标记**放置在检测到的物体中心点
- **图像显示**带有标注叠加层
- **坐标验证**确保标记在图像边界内

## 🛠️ 故障排除

### 常见问题

**API 密钥错误：**
```bash
# 设置环境变量
export XAI_API_KEY="your_key_here"
export DASHSCOPE_API_KEY="your_key_here"
```

**Ollama 连接问题：**
```bash
# 检查 Ollama 状态
ollama list

# 重启 Ollama 服务
ollama serve

# 安装缺失的模型
ollama pull llava:latest
```

**音频问题：**
- 使用 macOS 内置 `say` 命令
- 如果 TTS 失败会自动回退到纯文本
- 可以通过设置 `tts_enabled = False` 来禁用

### 性能优化

**获得高精度：**
- 使用 Grok-4 获得最佳结果
- 使用原始图像分辨率
- 提供具体的物体描述

**提高速度：**
- 使用本地 LLaVA 处理
- 如需要可启用图像缩放
- 使用更短、更简单的命令

**中文处理：**
- 使用 Qwen-VL 获得最佳中文语言支持
- 为特定领域词汇扩展 `chinese_patterns`
- 在处理前测试翻译

## 📈 性能指标

典型处理时间：
- **Grok-4**：3-8 秒（取决于图像大小）
- **Qwen-VL**：2-5 秒（良好优化）
- **LLaVA 本地**：1-3 秒（最快，取决于硬件）

## 🤝 贡献

扩展系统的方法：

1. **添加新的 VLM 提供商**，通过实现 API 调用模式
2. **扩展语言支持**，通过向翻译函数添加模式
3. **改进物体检测**，通过为特定用例优化提示
4. **添加新的输出格式**，通过扩展响应生成

## 📄 许可证

此项目为开源项目。请确保您遵守所使用的任何商业 VLM API 的服务条款。

## 🙏 致谢

- **X.AI** 提供 Grok-4 API 访问
- **阿里云** 通过 DashScope 提供 Qwen-VL
- **Ollama** 提供本地 LLaVA 处理基础设施
- **OpenAI** 提供兼容的 API 标准
