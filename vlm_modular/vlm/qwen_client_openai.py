"""Qwen VLM client implementation using OpenAI-compatible endpoint."""

import os
import sys
import logging
from typing import Dict, Any, List

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from vlm.base import VLMClient

class QwenClient(VLMClient):
    """Client for Alibaba Qwen vision model using OpenAI-compatible endpoint."""
    
    def __init__(self, api_key: str, model: str = "qwen-vl-max"):
        """Initialize Qwen client with OpenAI-compatible endpoint."""
        super().__init__(api_key, model)
        self.logger = logging.getLogger(__name__)
        
        if OpenAI is None:
            raise ImportError("OpenAI package is required for Qwen client. Install with: pip install openai")
        
        # Use OpenAI client with DashScope-compatible endpoint (same as original)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    
    def query_image(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Query Qwen with image and prompt using OpenAI-compatible endpoint."""
        if not self.validate_api_key():
            return self.handle_error(ValueError("No API key provided"), "Qwen query")
        
        if not self.validate_image_data(image_data):
            return self.handle_error(ValueError("Invalid image data"), "Qwen query")
        
        try:
            self.logger.info("Calling Qwen API via OpenAI-compatible endpoint")
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }]
            )
            
            response_content = completion.choices[0].message.content
            self.logger.info("Qwen query successful")
            
            return {
                'success': True,
                'response': response_content,  # Return raw text content like original
                'provider': 'qwen'
            }
            
        except Exception as e:
            return self.handle_error(e, "Qwen query")
    
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Qwen response to extract object coordinates."""
        objects = []
        
        try:
            if not response.get('success', False):
                return objects
            
            # Extract content from simple response format
            content = response.get('response', '')
            if not content:
                return objects
            
            self.logger.info(f"Parsing Qwen content: {content[:100]}...")
            
            # Parse table format coordinates
            import re
            
            # Look for table format: | H | V | ID | or | H | V |
            table_pattern = r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|(?:\s*(\d+)\s*\|)?'
            matches = re.findall(table_pattern, content)
            
            for i, match in enumerate(matches):
                h, v = int(match[0]), int(match[1])
                obj_id = int(match[2]) if match[2] else i + 1
                
                if h == 0 and v == 0:  # Skip "not found" responses
                    continue
                
                obj = {
                    'object': 'detected_object',
                    'coordinates': [h, v],
                    'center_h': h,
                    'center_v': v,
                    'confidence': 0.9,
                    'format': 'center_point',
                    'source': 'qwen_table'
                }
                objects.append(obj)
            
            self.logger.info(f"Qwen parser found {len(objects)} objects")
            return objects
            
        except Exception as e:
            self.logger.error(f"Error parsing Qwen response: {e}")
            return []
