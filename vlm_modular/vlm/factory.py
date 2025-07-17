"""VLM Factory for creating client instances."""

import os
import sys
from typing import Optional

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vlm.base import VLMClient
from vlm.grok_client import GrokClient
from vlm.qwen_client_openai import QwenClient  # Use OpenAI-compatible client
from vlm.llava_client import LLaVAClient
from config.api_keys import APIKeys
from config.settings import VLMSettings

class VLMFactory:
    """Factory class for creating VLM client instances."""
    
    def __init__(self, api_keys: APIKeys, settings: VLMSettings):
        """Initialize factory with API keys and settings."""
        self.api_keys = api_keys
        self.settings = settings
    
    def create_client(self, provider: str) -> Optional[VLMClient]:
        """Create a VLM client for the specified provider."""
        provider = provider.lower()
        
        if provider == "grok":
            return self._create_grok_client()
        elif provider == "qwen":
            return self._create_qwen_client()
        elif provider == "llava":
            return self._create_llava_client()
        else:
            raise ValueError(f"Unsupported VLM provider: {provider}")
    
    def _create_grok_client(self) -> Optional[GrokClient]:
        """Create Grok client instance."""
        api_key = self.api_keys.get_grok_key()
        if not api_key:
            raise ValueError("Grok API key not found. Please set XAI_API_KEY environment variable.")
        
        return GrokClient(api_key, self.settings.grok_model)
    
    def _create_qwen_client(self) -> Optional[QwenClient]:
        """Create Qwen client instance."""
        api_key = self.api_keys.get_qwen_key()
        if not api_key:
            raise ValueError("Qwen API key not found. Please set DASHSCOPE_API_KEY environment variable.")
        
        return QwenClient(api_key, self.settings.qwen_model)
    
    def _create_llava_client(self) -> Optional[LLaVAClient]:
        """Create LLaVA client instance."""
        # LLaVA is local, no API key needed
        client = LLaVAClient(model=self.settings.llava_model)
        
        # Check if server is running
        if not client.check_server_status():
            raise ConnectionError("LLaVA server is not running. Please start Ollama with LLaVA model.")
        
        return client
    
    def get_available_providers(self) -> list:
        """Get list of available VLM providers based on API keys."""
        available = []
        
        # Check Grok
        if self.api_keys.has_key_for_provider("grok"):
            available.append("grok")
        
        # Check Qwen
        if self.api_keys.has_key_for_provider("qwen"):
            available.append("qwen")
        
        # Check LLaVA (always available if server is running)
        try:
            llava_client = LLaVAClient()
            if llava_client.check_server_status():
                available.append("llava")
        except:
            pass
        
        return available
    
    def get_default_client(self) -> Optional[VLMClient]:
        """Get the default VLM client based on settings."""
        default_provider = self.settings.default_vlm_provider
        available_providers = self.get_available_providers()
        
        if default_provider in available_providers:
            return self.create_client(default_provider)
        
        # Fallback to first available provider
        if available_providers:
            fallback_provider = available_providers[0]
            print(f"Default provider '{default_provider}' not available. Using '{fallback_provider}' instead.")
            return self.create_client(fallback_provider)
        
        raise ValueError("No VLM providers are available. Please check your API keys and server status.")
    
    def validate_provider(self, provider: str) -> bool:
        """Validate if a provider is available."""
        return provider.lower() in self.get_available_providers()
    
    def get_provider_info(self) -> dict:
        """Get information about all providers."""
        info = {}
        
        for provider in ["grok", "qwen", "llava"]:
            try:
                client = self.create_client(provider)
                info[provider] = {
                    'available': True,
                    'model': client.model,
                    'requires_api_key': provider != "llava"
                }
            except Exception as e:
                info[provider] = {
                    'available': False,
                    'error': str(e),
                    'requires_api_key': provider != "llava"
                }
        
        return info
