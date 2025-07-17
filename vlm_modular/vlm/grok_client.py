"""Grok VLM client implementation."""

import requests
import json
import os
import sys
import time
from typing import Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vlm.base import VLMClient

class GrokClient(VLMClient):
    """Client for X.AI Grok vision model."""
    
    def __init__(self, api_key: str, model: str = "grok-4-0709"):
        """Initialize Grok client."""
        super().__init__(api_key, model)
        self.base_url = "https://api.x.ai/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # Use same proxy setup as original
        self.proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    
    def query_image(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Query Grok with image and prompt."""
        if not self.validate_api_key():
            return self.handle_error(ValueError("No API key provided"), "Grok query")
        
        if not self.validate_image_data(image_data):
            return self.handle_error(ValueError("Invalid image data"), "Grok query")
        
        try:
            # Use exact same payload format as original
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text", 
                                "text": prompt
                            }, 
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Use original timeout and proxy settings with retry logic
            session = requests.Session()
            retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            
            response = session.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                proxies=self.proxies,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info("Grok query successful")
                return {
                    'success': True,
                    'response': result,
                    'provider': 'grok'
                }
            else:
                error_msg = f"Grok API error: {response.status_code} - {response.text}"
                return self.handle_error(ValueError(error_msg), "Grok API")
                
        except Exception as e:
            return self.handle_error(e, "Grok query")
    
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Grok response to extract object coordinates."""
        objects = []
        
        try:
            if not response.get('success', False):
                return objects
            
            # Extract text content from response
            content = ""
            if 'response' in response and 'choices' in response['response']:
                choices = response['response']['choices']
                if choices and len(choices) > 0:
                    content = choices[0].get('message', {}).get('content', '')
            
            if not content:
                self.logger.warning("No content found in Grok response")
                return objects
            
            self.logger.info(f"Parsing Grok content: {content[:200]}...")
            
            # Parse coordinates using multiple patterns
            objects.extend(self._parse_bounding_box_format(content))
            objects.extend(self._parse_coordinates_format(content))
            objects.extend(self._parse_table_format(content))
            
            self.logger.info(f"Grok parser found {len(objects)} objects")
            return objects
            
        except Exception as e:
            self.logger.error(f"Error parsing Grok response: {e}")
            return objects
    
    def _parse_bounding_box_format(self, content: str) -> List[Dict[str, Any]]:
        """Parse 'Bounding box: [x1, y1, x2, y2]' format."""
        import re
        objects = []
        
        # Pattern for "Bounding box: [x1, y1, x2, y2]"
        pattern = r'(?:Bounding box|bbox|coordinates?):\s*\[?\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]?'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            x1, y1, x2, y2 = map(float, match.groups())
            objects.append({
                'coordinates': [x1, y1, x2, y2],
                'confidence': 0.8,
                'source': 'grok_bbox'
            })
        
        return objects
    
    def _parse_coordinates_format(self, content: str) -> List[Dict[str, Any]]:
        """Parse general coordinate patterns."""
        import re
        objects = []
        
        # Pattern for any [x1, y1, x2, y2] format
        pattern = r'\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            x1, y1, x2, y2 = map(float, match.groups())
            # Validate coordinates are reasonable
            if all(coord >= 0 for coord in [x1, y1, x2, y2]) and x2 > x1 and y2 > y1:
                objects.append({
                    'coordinates': [x1, y1, x2, y2],
                    'confidence': 0.7,
                    'source': 'grok_coords'
                })
        
        return objects
    
    def _parse_table_format(self, content: str) -> List[Dict[str, Any]]:
        """Parse table format responses."""
        import re
        objects = []
        
        # Look for table rows with coordinates
        lines = content.split('\n')
        for line in lines:
            if '|' in line and '[' in line:
                # Extract coordinates from table cell
                coord_match = re.search(r'\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]', line)
                if coord_match:
                    x1, y1, x2, y2 = map(float, coord_match.groups())
                    objects.append({
                        'coordinates': [x1, y1, x2, y2],
                        'confidence': 0.6,
                        'source': 'grok_table'
                    })
        
        return objects
