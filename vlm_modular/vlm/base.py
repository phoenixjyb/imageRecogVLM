"""Base VLM client interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

class VLMClient(ABC):
    """Abstract base class for VLM clients."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = ""):
        """Initialize VLM client."""
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def query_image(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """
        Query the VLM with an image and prompt.
        
        Args:
            image_data: Base64 encoded image data
            prompt: Text prompt for the VLM
            
        Returns:
            Dictionary containing the response from the VLM
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the VLM response to extract object locations.
        
        Args:
            response: Raw response from the VLM
            
        Returns:
            List of objects with their coordinates
        """
        pass
    
    def validate_image_data(self, image_data: str) -> bool:
        """Validate base64 image data."""
        if not image_data:
            return False
        
        # Check if it's valid base64
        try:
            import base64
            base64.b64decode(image_data)
            return True
        except Exception:
            return False
    
    def validate_api_key(self) -> bool:
        """Validate if API key is available."""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def get_provider_name(self) -> str:
        """Get the name of the VLM provider."""
        return self.__class__.__name__.replace('Client', '').lower()
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the model."""
        return {
            'provider': self.get_provider_name(),
            'model': self.model,
            'has_api_key': self.validate_api_key()
        }
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Handle and log errors consistently."""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg,
            'provider': self.get_provider_name(),
            'objects': []
        }
