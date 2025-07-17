# VLM 物体识别系统 - 模块化架构

🤖 专业的模块化视觉语言模型（VLM）物体识别系统，支持多个提供商、语音输入和高级图像标注。

## 🌟 功能特性

- **多VLM支持**：Grok-4 (X.AI)、Qwen-VL (阿里云)、LLaVA (本地)
- **语音输入**：多语言语音识别和回退机制
- **高级解析**：支持不同VLM响应格式的智能坐标解析
- **图像标注**：专业的边界框和星形标记注释
- **文本转语音**：跨平台TTS支持
- **模块化设计**：清晰、可维护、可扩展的架构

## 🏗️ 架构

这是VLM物体识别系统的**模块化版本**，从原始的单体实现完全重构为专业、可维护的架构。

```
📁 vlm_modular/
├── 🔧 config/         # 配置和API管理
├── 🎤 input/          # 语音和文本处理
├── 🤖 vlm/            # VLM提供商实现
├── 🖼️ image/          # 图像处理和标注
├── 🔊 output/         # 响应生成和TTS
├── 🛠️ utils/          # 工具函数
└── 🚀 main.py        # 应用程序入口
```

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/phoenixjyb/imageRecogVLM.git
cd imageRecogVLM

# 切换到模块化架构分支
git checkout modular-architecture

# 安装依赖
pip install -r requirements.txt
```

### 2. 设置API密钥

```bash
# Grok (X.AI)
export XAI_API_KEY="your_grok_api_key"

# Qwen (阿里云)
export DASHSCOPE_API_KEY="your_qwen_api_key"

# LLaVA (本地) - 安装Ollama
brew install ollama  # macOS
ollama pull llava
ollama serve
```

### 3. 运行系统

```bash
cd vlm_modular
python main.py
```

## � 支持的提供商

| 提供商 | 类型 | 需要API密钥 | 最适用于 |
|----------|------|------------------|----------|
| **Grok** (X.AI) | 云端 | ✅ XAI_API_KEY | 高精度，最新模型 |
| **Qwen** (阿里云) | 云端 | ✅ DASHSCOPE_API_KEY | 优秀的表格解析，中文支持 |
| **LLaVA** | 本地 | ❌ (Ollama) | 隐私保护，离线使用，无费用 |

## � 文档

- 📚 **[详细文档](vlm_modular/README.md)** - 完整使用指南
- 🧪 **测试**：运行 `python vlm_modular/test_system.py`
- 🎤 **语音输入**：支持英语和中文，具有回退机制
- 🔊 **TTS**：跨平台文本转语音 (macOS, Linux, Windows)

## � 架构对比

| 功能 | 原版 (master) | 模块化 (当前分支) |
|---------|-------------------|----------------------|
| **结构** | 单个1000+行文件 | 6个模块包 (24+文件) |
| **可维护性** | ❌ 难以修改 | ✅ 易于更新组件 |
| **测试** | ❌ 单体测试 | ✅ 组件级测试 |
| **可扩展性** | ❌ 难以添加提供商 | ✅ 轻松添加新VLM |
| **代码质量** | ❌ 混合关注点 | ✅ 清晰分离 |
| **文档** | ❌ 基础 | ✅ 全面 |

## � 配置

用于自定义的环境变量：

```bash
export VLM_DEFAULT_PROVIDER="grok"    # 默认VLM提供商
export VLM_ENABLE_VOICE="true"        # 启用语音输入
export VLM_ENABLE_TTS="true"          # 启用文本转语音
export VLM_IMAGE_WIDTH="640"          # 输出图像宽度
export VLM_IMAGE_HEIGHT="480"         # 输出图像高度
export VLM_DEBUG="false"              # 启用调试日志
```

## 📊 性能

模块化架构提供：
- **更好的错误处理**：具有特定错误消息的优雅失败
- **改进的解析**：支持6+种坐标格式模式
- **增强的可靠性**：重试机制和回退
- **专业日志**：全面的调试支持

## 🤝 贡献

模块化架构使贡献变得容易：

1. **添加新VLM提供商**：扩展 `vlm/` 包
2. **改进解析**：增强 `image/coordinate_parser.py`
3. **添加输入方法**：扩展 `input/` 包
4. **增强输出**：改进 `output/` 组件

## � 许可证

此项目仅供教育和研究目的。

## � 链接

- **原版**：查看 `master` 分支
- **问题和功能**：[GitHub Issues](https://github.com/phoenixjyb/imageRecogVLM/issues)
- **拉取请求**：[GitHub PRs](https://github.com/phoenixjyb/imageRecogVLM/pulls)

---

**注意**：这是模块化架构分支。要查看原始单体实现，请切换到 `master` 分支。
