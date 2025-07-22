"""API key management for VLM providers."""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class APIKeys:
    """Manages API keys for different VLM providers."""
    
    xai_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    moonshot_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None  # For future OpenAI integration
    
    def __post_init__(self):
        """Load API keys from environment variables."""
        self.xai_api_key = os.getenv('XAI_API_KEY')
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY')
        self.moonshot_api_key = os.getenv('MOONSHOT_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
    
    def get_grok_key(self) -> Optional[str]:
        """Get X.AI (Grok) API key."""
        return self.xai_api_key
    
    def get_qwen_key(self) -> Optional[str]:
        """Get Alibaba Qwen API key."""
        return self.dashscope_api_key
    
    def get_kimi_key(self) -> Optional[str]:
        """Get Moonshot Kimi API key."""
        return self.moonshot_api_key
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return self.openai_api_key
    
    def validate_keys(self) -> dict:
        """Validate which API keys are available."""
        return {
            'grok': self.xai_api_key is not None,
            'qwen': self.dashscope_api_key is not None,
            'kimi': self.moonshot_api_key is not None,
            'openai': self.openai_api_key is not None
        }
    
    def has_key_for_provider(self, provider: str) -> bool:
        """Check if API key is available for the specified provider."""
        key_map = {
            'grok': self.xai_api_key,
            'qwen': self.dashscope_api_key,
            'kimi': self.moonshot_api_key,
            'openai': self.openai_api_key,
            'llava': True  # Local model, no API key needed
        }
        return key_map.get(provider.lower(), False) is not None
