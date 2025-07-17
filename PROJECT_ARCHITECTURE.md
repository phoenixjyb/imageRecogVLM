# VLM Object Recognition System - Architecture Diagrams

This document contains comprehensive Mermaid diagrams that visualize the architecture and structure of the VLM Object Recognition System.

## 📊 System Architecture Overview

```mermaid
architecture-beta
    group main(cloud)[VLM System Core]
    group original(server)[Original Implementation]
    group modular(cloud)[Modular Architecture]
    group testing(internet)[Testing Framework]
    group docs(database)[Documentation]

    service legacy(server)[imageRecogVLM.py] in original
    service config(disk)[Config Files] in original
    service samples(database)[Sample Images] in original

    service mainApp(server)[main.py] in modular
    service configMod(disk)[config/] in modular
    service inputMod(server)[input/] in modular
    service vlmMod(cloud)[vlm/] in modular
    service imageMod(server)[image/] in modular
    service outputMod(server)[output/] in modular
    service utilsMod(disk)[utils/] in modular

    service compareTests(internet)[Compare Tests] in testing
    service verifyTests(internet)[Verify Tests] in testing
    service unitTests(internet)[Unit Tests] in testing
    service results(database)[Test Results] in testing

    service readme(database)[README Files] in docs
    service projectSummary(database)[PROJECT_SUMMARY.md] in docs
    service devStats(database)[DEVELOPMENT_STATISTICS.md] in docs

    legacy:R --> mainApp:L
    configMod:B --> inputMod:T
    inputMod:R --> vlmMod:L
    vlmMod:R --> imageMod:L
    imageMod:R --> outputMod:L
    mainApp:B --> configMod:T
    mainApp:B --> inputMod:T
    mainApp:B --> vlmMod:T
    mainApp:B --> imageMod:T
    mainApp:B --> outputMod:T
    
    compareTests:B --> legacy:T
    compareTests:B --> mainApp:T
    verifyTests:B --> vlmMod:T
    unitTests:B --> modular{group}:T
```

## 🔄 System Flow Architecture

```mermaid
flowchart TB
    subgraph "User Interface Layer"
        UI[User Input]
        VOICE[🎤 Voice Input]
        TEXT[⌨️ Text Input]
    end

    subgraph "Input Processing Layer"
        SPEECH[Speech Recognition]
        LANG[Language Detection]
        TRANS[Translation Engine]
        EXTRACT[Object Extraction]
    end

    subgraph "VLM Processing Layer"
        VLM_SEL{VLM Selection}
        GROK[☁️ Grok-4 API]
        QWEN[☁️ Qwen-VL API]
        LLAVA[🖥️ LLaVA Local]
    end

    subgraph "Image Processing Layer"
        IMG_PROC[Image Processor]
        COORD_PARSE[Coordinate Parser]
        ANNOTATE[Image Annotator]
    end

    subgraph "Output Layer"
        RESPONSE[Response Generator]
        TTS[🔊 Text-to-Speech]
        DISPLAY[📱 Visual Display]
    end

    subgraph "Configuration Layer"
        CONFIG[Settings Manager]
        API_KEYS[API Key Manager]
    end

    UI --> VOICE
    UI --> TEXT
    VOICE --> SPEECH
    TEXT --> LANG
    SPEECH --> LANG
    LANG --> TRANS
    TRANS --> EXTRACT
    LANG --> EXTRACT
    EXTRACT --> VLM_SEL

    VLM_SEL --> GROK
    VLM_SEL --> QWEN
    VLM_SEL --> LLAVA

    GROK --> COORD_PARSE
    QWEN --> COORD_PARSE
    LLAVA --> COORD_PARSE

    COORD_PARSE --> IMG_PROC
    IMG_PROC --> ANNOTATE
    COORD_PARSE --> RESPONSE
    ANNOTATE --> DISPLAY
    RESPONSE --> TTS
    RESPONSE --> DISPLAY

    CONFIG --> VLM_SEL
    API_KEYS --> GROK
    API_KEYS --> QWEN

    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef processing fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef vlm fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef image fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef config fill:#f9fbe7,stroke:#689f38,stroke-width:2px

    class UI,VOICE,TEXT input
    class SPEECH,LANG,TRANS,EXTRACT processing
    class VLM_SEL,GROK,QWEN,LLAVA vlm
    class IMG_PROC,COORD_PARSE,ANNOTATE image
    class RESPONSE,TTS,DISPLAY output
    class CONFIG,API_KEYS config
```

## 🏗️ Modular System Architecture

```mermaid
flowchart LR
    subgraph "vlm_modular/"
        MAIN[main.py<br/>🚀 Entry Point]
        
        subgraph "config/"
            SETTINGS[settings.py<br/>⚙️ System Config]
            KEYS[api_keys.py<br/>🔑 API Management]
        end
        
        subgraph "input/"
            VOICE_H[voice_handler.py<br/>🎤 Speech Processing]
            TEXT_P[text_processor.py<br/>📝 Text Processing]
        end
        
        subgraph "vlm/"
            FACTORY[factory.py<br/>🏭 VLM Factory]
            BASE[base.py<br/>🔧 Base Interface]
            GROK_C[grok_client.py<br/>☁️ Grok Client]
            QWEN_C[qwen_client_openai.py<br/>☁️ Qwen Client]
            LLAVA_C[llava_client.py<br/>🖥️ LLaVA Client]
        end
        
        subgraph "image/"
            PROCESSOR[processor.py<br/>🖼️ Image Processing]
            ANNOTATOR[annotator.py<br/>✏️ Image Annotation]
            COORD_PARSER[coordinate_parser.py<br/>📍 Coordinate Parsing]
        end
        
        subgraph "output/"
            RESP_GEN[response_generator.py<br/>💬 Response Generation]
            TTS_H[tts_handler.py<br/>🔊 Text-to-Speech]
        end
        
        subgraph "utils/"
            UTILS[__init__.py<br/>🛠️ Utilities]
        end
    end

    MAIN --> SETTINGS
    MAIN --> KEYS
    MAIN --> VOICE_H
    MAIN --> TEXT_P
    MAIN --> FACTORY
    MAIN --> PROCESSOR
    MAIN --> ANNOTATOR
    MAIN --> COORD_PARSER
    MAIN --> RESP_GEN
    MAIN --> TTS_H

    FACTORY --> BASE
    FACTORY --> GROK_C
    FACTORY --> QWEN_C
    FACTORY --> LLAVA_C
    FACTORY --> KEYS
    FACTORY --> SETTINGS

    VOICE_H --> SETTINGS
    TEXT_P --> SETTINGS
    PROCESSOR --> SETTINGS
    ANNOTATOR --> SETTINGS
    RESP_GEN --> SETTINGS
    TTS_H --> SETTINGS

    classDef main fill:#ff6b6b,stroke:#d63031,stroke-width:3px,color:#fff
    classDef config fill:#fdcb6e,stroke:#e17055,stroke-width:2px
    classDef input fill:#6c5ce7,stroke:#5f3dc4,stroke-width:2px,color:#fff
    classDef vlm fill:#a29bfe,stroke:#6c5ce7,stroke-width:2px
    classDef image fill:#fd79a8,stroke:#e84393,stroke-width:2px
    classDef output fill:#00b894,stroke:#00a085,stroke-width:2px,color:#fff
    classDef utils fill:#636e72,stroke:#2d3436,stroke-width:2px,color:#fff

    class MAIN main
    class SETTINGS,KEYS config
    class VOICE_H,TEXT_P input
    class FACTORY,BASE,GROK_C,QWEN_C,LLAVA_C vlm
    class PROCESSOR,ANNOTATOR,COORD_PARSER image
    class RESP_GEN,TTS_H output
    class UTILS utils
```

## 🧪 Testing Framework Architecture

```mermaid
flowchart TB
    subgraph "testing/"
        MAIN_TEST[test_system.py<br/>🧪 Main Test Suite]
        
        subgraph "Comparison Tests"
            COMP_VLM[compare_vlm_outputs.py<br/>🔄 VLM Output Comparison]
            COMP_GROK[compare_grok_outputs.py<br/>🔄 Grok Specific Tests]
            COMP_API[compare_grok_api.py<br/>🔄 API Level Tests]
        end
        
        subgraph "Verification Tests"
            VERIFY_GROK[verify_grok_implementation.py<br/>✅ Grok Verification]
            VERIFY_MOD[test_modular_grok.py<br/>✅ Modular Tests]
        end
        
        subgraph "Test Results"
            VLM_RESULTS[vlm_comparison_results.json<br/>📊 VLM Results]
            GROK_RESULTS[grok_verification_results.json<br/>📊 Grok Results]
            API_RESULTS[grok_api_comparison.json<br/>📊 API Results]
        end
        
        TEST_README[README.md<br/>📚 Testing Documentation]
    end

    subgraph "Source Systems"
        ORIGINAL[../imageRecogVLM.py<br/>📜 Original Implementation]
        MODULAR[../vlm_modular/<br/>🏗️ Modular System]
    end

    MAIN_TEST --> COMP_VLM
    MAIN_TEST --> COMP_GROK
    MAIN_TEST --> VERIFY_GROK

    COMP_VLM --> ORIGINAL
    COMP_VLM --> MODULAR
    COMP_VLM --> VLM_RESULTS

    COMP_GROK --> ORIGINAL
    COMP_GROK --> MODULAR
    COMP_GROK --> GROK_RESULTS

    COMP_API --> ORIGINAL
    COMP_API --> API_RESULTS

    VERIFY_GROK --> MODULAR
    VERIFY_GROK --> GROK_RESULTS

    VERIFY_MOD --> MODULAR

    classDef test fill:#74b9ff,stroke:#0984e3,stroke-width:2px
    classDef comparison fill:#a29bfe,stroke:#6c5ce7,stroke-width:2px
    classDef verification fill:#00b894,stroke:#00a085,stroke-width:2px
    classDef results fill:#fdcb6e,stroke:#e17055,stroke-width:2px
    classDef source fill:#fd79a8,stroke:#e84393,stroke-width:2px
    classDef docs fill:#55a3ff,stroke:#2980b9,stroke-width:2px

    class MAIN_TEST test
    class COMP_VLM,COMP_GROK,COMP_API comparison
    class VERIFY_GROK,VERIFY_MOD verification
    class VLM_RESULTS,GROK_RESULTS,API_RESULTS results
    class ORIGINAL,MODULAR source
    class TEST_README docs
```

## 📁 Complete Project Structure

```mermaid
flowchart TB
    subgraph "vlmTry/"
        ROOT_FILES[📄 Root Files<br/>README.md<br/>README_CN.md<br/>requirements.txt<br/>.gitignore]
        
        LEGACY[📜 imageRecogVLM.py<br/>Original Monolithic System]
        
        DOCS[📚 Documentation<br/>PROJECT_SUMMARY.md<br/>DEVELOPMENT_STATISTICS.md<br/>PROJECT_ARCHITECTURE.md]
        
        subgraph "sampleImages/"
            SAMPLE1[image_000777_rsz.jpg]
            SAMPLE2[image_000354.jpg]
            SAMPLE3[image_000078.jpg]
            ANNOTATIONS[*_annotated.jpg files]
        end
        
        subgraph "vlm_modular/"
            direction TB
            MOD_MAIN[main.py]
            MOD_TEST[test_system.py]
            MOD_LOG[vlm_system.log]
            
            MOD_CONFIG[config/]
            MOD_INPUT[input/]
            MOD_VLM[vlm/]
            MOD_IMAGE[image/]
            MOD_OUTPUT[output/]
            MOD_UTILS[utils/]
        end
        
        subgraph "testing/"
            direction TB
            TEST_COMP[Compare Tests]
            TEST_VERIFY[Verify Tests]
            TEST_UNIT[Unit Tests]
            TEST_RESULTS[Results JSON]
            TEST_README[README.md]
        end
    end

    ROOT_FILES -.-> LEGACY
    ROOT_FILES -.-> DOCS
    LEGACY -.-> MOD_MAIN
    SAMPLE1 --> MOD_MAIN
    MOD_MAIN --> MOD_CONFIG
    MOD_MAIN --> MOD_INPUT
    MOD_MAIN --> MOD_VLM
    MOD_MAIN --> MOD_IMAGE
    MOD_MAIN --> MOD_OUTPUT
    
    TEST_COMP --> LEGACY
    TEST_COMP --> MOD_MAIN
    TEST_VERIFY --> MOD_VLM
    TEST_UNIT --> MOD_MAIN

    classDef root fill:#2d3436,stroke:#636e72,stroke-width:2px,color:#fff
    classDef legacy fill:#e17055,stroke:#d63031,stroke-width:2px,color:#fff
    classDef docs fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff
    classDef samples fill:#00b894,stroke:#00cec9,stroke-width:2px,color:#fff
    classDef modular fill:#6c5ce7,stroke:#a29bfe,stroke-width:2px,color:#fff
    classDef testing fill:#fd79a8,stroke:#fdcb6e,stroke-width:2px

    class ROOT_FILES root
    class LEGACY legacy
    class DOCS docs
    class SAMPLE1,SAMPLE2,SAMPLE3,ANNOTATIONS samples
    class MOD_MAIN,MOD_TEST,MOD_LOG,MOD_CONFIG,MOD_INPUT,MOD_VLM,MOD_IMAGE,MOD_OUTPUT,MOD_UTILS modular
    class TEST_COMP,TEST_VERIFY,TEST_UNIT,TEST_RESULTS,TEST_README testing
```

## 🔄 VLM Provider Integration Flow

```mermaid
sequenceDiagram
    participant User
    participant Main as main.py
    participant Factory as VLMFactory
    participant Grok as GrokClient
    participant Qwen as QwenClient
    participant LLaVA as LLaVAClient
    participant Parser as CoordinateParser
    participant Annotator as ImageAnnotator

    User->>Main: Voice/Text Input
    Main->>Main: Extract Object
    Main->>Factory: create_client(provider)
    
    alt Grok Selected
        Factory->>Grok: Initialize with API key
        Main->>Grok: analyze_image(prompt, image)
        Grok->>Grok: Call X.AI API
        Grok-->>Main: Raw response
    else Qwen Selected
        Factory->>Qwen: Initialize with API key
        Main->>Qwen: analyze_image(prompt, image)
        Qwen->>Qwen: Call DashScope API
        Qwen-->>Main: Raw response
    else LLaVA Selected
        Factory->>LLaVA: Initialize local client
        Main->>LLaVA: analyze_image(prompt, image)
        LLaVA->>LLaVA: Call Ollama API
        LLaVA-->>Main: Raw response
    end

    Main->>Parser: parse_coordinates(response)
    Parser-->>Main: Parsed coordinates
    Main->>Annotator: annotate_image(image, coords)
    Annotator-->>Main: Annotated image
    Main-->>User: Response + Annotated Image
```

## 📈 Development Evolution

```mermaid
gitgraph
    commit id: "Initial Monolithic System"
    commit id: "Basic VLM Integration"
    commit id: "Voice Input Added"
    
    branch modular-architecture
    commit id: "Modular Architecture Setup"
    commit id: "Config Module"
    commit id: "Input Module"
    commit id: "VLM Module & Factory"
    commit id: "Image Processing Module"
    commit id: "Output Module"
    
    branch testing-framework
    commit id: "Comparison Tests"
    commit id: "Verification Scripts"
    commit id: "Unit Tests"
    commit id: "Test Results Tracking"
    merge modular-architecture
    
    branch documentation
    commit id: "README Updates"
    commit id: "Project Summary"
    commit id: "Development Statistics"
    commit id: "Architecture Diagrams"
    merge modular-architecture
    
    commit id: "Production Ready Release" type: HIGHLIGHT
```

---

## 🛠️ How to Use These Diagrams

1. **VS Code with Mermaid Extension**: Copy any diagram code block and paste it into a `.md` file
2. **Mermaid Live Editor**: Visit [mermaid.live](https://mermaid.live) and paste the code
3. **GitHub/GitLab**: These diagrams will render automatically in markdown files
4. **Documentation**: Include these in your project documentation for visual clarity

The diagrams accurately reflect your current project structure and can be updated as the system evolves!
