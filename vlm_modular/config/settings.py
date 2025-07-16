"""Application settings and configuration."""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class VLMSettings:
    """Central configuration for VLM Object Recognition System."""
    
    # VLM Provider settings
    default_vlm_provider: str = "grok"
    available_providers: list = field(default_factory=lambda: ["grok", "qwen", "llava"])
    
    # Voice input settings
    enable_voice_input: bool = True
    voice_timeout: float = 5.0
    voice_phrase_time_limit: float = 10.0
    offline_voice_keywords: list = field(default_factory=lambda: [
        "red car", "blue truck", "person", "bicycle", "motorcycle", "airplane", "bus", "train", "boat"
    ])
    
    # Image processing settings
    image_output_width: int = 640
    image_output_height: int = 480
    annotation_star_size: int = 10
    annotation_text_color: str = "red"
    annotation_font_size: int = 12
    
    # TTS settings
    enable_tts: bool = True
    tts_timeout: float = 10.0
    
    # API settings
    grok_model: str = "grok-vision-beta"
    qwen_model: str = "qwen-vl-max-0809"
    llava_model: str = "llava"
    
    # Request settings
    max_retries: int = 3
    request_timeout: float = 30.0
    
    # Logging settings
    enable_debug_logging: bool = False
    log_vlm_responses: bool = True
    
    @classmethod
    def load_from_env(cls) -> 'VLMSettings':
        """Load settings from environment variables."""
        settings = cls()
        
        # Override with environment variables if present
        settings.default_vlm_provider = os.getenv('VLM_DEFAULT_PROVIDER', settings.default_vlm_provider)
        settings.enable_voice_input = os.getenv('VLM_ENABLE_VOICE', 'true').lower() == 'true'
        settings.voice_timeout = float(os.getenv('VLM_VOICE_TIMEOUT', str(settings.voice_timeout)))
        settings.image_output_width = int(os.getenv('VLM_IMAGE_WIDTH', str(settings.image_output_width)))
        settings.image_output_height = int(os.getenv('VLM_IMAGE_HEIGHT', str(settings.image_output_height)))
        settings.enable_tts = os.getenv('VLM_ENABLE_TTS', 'true').lower() == 'true'
        settings.enable_debug_logging = os.getenv('VLM_DEBUG', 'false').lower() == 'true'
        
        return settings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'default_vlm_provider': self.default_vlm_provider,
            'available_providers': self.available_providers,
            'enable_voice_input': self.enable_voice_input,
            'voice_timeout': self.voice_timeout,
            'image_output_width': self.image_output_width,
            'image_output_height': self.image_output_height,
            'enable_tts': self.enable_tts,
            'enable_debug_logging': self.enable_debug_logging
        }
