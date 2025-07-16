"""LLaVA VLM client implementation."""

import requests
import json
import os
import sys
from typing import Dict, Any, List

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vlm.base import VLMClient

class LLaVAClient(VLMClient):
    """Client for local LLaVA model via Ollama."""
    
    def __init__(self, api_key: str = None, model: str = "llava"):
        """Initialize LLaVA client."""
        super().__init__(api_key, model)  # LLaVA doesn't need API key for local
        self.base_url = "http://localhost:11434/api/generate"
    
    def query_image(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Query LLaVA with image and prompt."""
        if not self.validate_image_data(image_data):
            return self.handle_error(ValueError("Invalid image data"), "LLaVA query")
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500
                }
            }
            
            # Create session without proxy for localhost
            session = requests.Session()
            session.proxies = {
                'http': None,
                'https': None
            }
            session.trust_env = False
            
            response = session.post(
                self.base_url,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info("LLaVA query successful")
                return {
                    'success': True,
                    'response': result,
                    'provider': 'llava'
                }
            else:
                error_msg = f"LLaVA API error: {response.status_code} - {response.text}"
                return self.handle_error(ValueError(error_msg), "LLaVA API")
                
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to LLaVA server. Make sure Ollama is running with LLaVA model."
            return self.handle_error(ConnectionError(error_msg), "LLaVA connection")
        except Exception as e:
            return self.handle_error(e, "LLaVA query")
    
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse LLaVA response to extract object coordinates."""
        objects = []
        
        try:
            if not response.get('success', False):
                return objects
            
            # Extract content from LLaVA response
            content = ""
            if 'response' in response and 'response' in response['response']:
                content = response['response']['response']
            
            if not content:
                self.logger.warning("No content found in LLaVA response")
                return objects
            
            self.logger.info(f"Parsing LLaVA content: {content[:200]}...")
            
            # Parse using different methods
            objects.extend(self._parse_coordinate_patterns(content))
            objects.extend(self._parse_object_format(content))
            objects.extend(self._parse_location_format(content))
            
            # If no coordinates found, try to parse descriptive locations
            if not objects:
                objects.extend(self._parse_descriptive_locations(content))
            
            self.logger.info(f"LLaVA parser found {len(objects)} objects")
            return objects
            
        except Exception as e:
            self.logger.error(f"Error parsing LLaVA response: {e}")
            return objects
    
    def _parse_coordinate_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Parse coordinate patterns from LLaVA response."""
        import re
        objects = []
        
        # Various coordinate patterns
        patterns = [
            r'(?:coordinates?|location):\s*\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]',
            r'\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]',
            r'(?:at|located at):\s*\(?(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)?'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                coords = [float(x) for x in match.groups()]
                # Validate coordinates
                if all(coord >= 0 for coord in coords) and coords[2] > coords[0] and coords[3] > coords[1]:
                    objects.append({
                        'coordinates': coords,
                        'confidence': 0.7,
                        'source': 'llava_coords'
                    })
        
        return objects
    
    def _parse_object_format(self, content: str) -> List[Dict[str, Any]]:
        """Parse 'Object: name, Coordinates: [...]' format."""
        import re
        objects = []
        
        # Look for Object/Coordinates format
        pattern = r'Object:\s*\w+\s*(?:,\s*)?(?:Coordinates?|Location):\s*\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            coords = [float(x) for x in match.groups()]
            objects.append({
                'coordinates': coords,
                'confidence': 0.8,
                'source': 'llava_object'
            })
        
        return objects
    
    def _parse_location_format(self, content: str) -> List[Dict[str, Any]]:
        """Parse numbered location format."""
        import re
        objects = []
        
        # Look for numbered format like "1. Object name: [x,y,x,y]"
        pattern = r'\d+\.\s*[^:]+:\s*\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            coords = [float(x) for x in match.groups()]
            objects.append({
                'coordinates': coords,
                'confidence': 0.6,
                'source': 'llava_numbered'
            })
        
        return objects
    
    def _parse_descriptive_locations(self, content: str) -> List[Dict[str, Any]]:
        """Parse descriptive locations when coordinates aren't provided."""
        import re
        objects = []
        
        # Look for descriptive terms and assign approximate coordinates
        descriptive_patterns = {
            r'(?:top|upper).*?(?:left|corner)': [100, 50, 200, 150],
            r'(?:top|upper).*?(?:right|corner)': [440, 50, 540, 150],
            r'(?:bottom|lower).*?(?:left|corner)': [100, 330, 200, 430],
            r'(?:bottom|lower).*?(?:right|corner)': [440, 330, 540, 430],
            r'(?:center|middle)': [270, 190, 370, 290],
            r'(?:left|left side)': [50, 190, 150, 290],
            r'(?:right|right side)': [490, 190, 590, 290],
            r'(?:top|upper)': [270, 50, 370, 150],
            r'(?:bottom|lower)': [270, 330, 370, 430]
        }
        
        for pattern, coords in descriptive_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                objects.append({
                    'coordinates': coords,
                    'confidence': 0.3,
                    'source': 'llava_descriptive'
                })
                break  # Only use the first match
        
        return objects
    
    def validate_api_key(self) -> bool:
        """LLaVA doesn't need API key validation for local deployment."""
        return True
    
    def check_server_status(self) -> bool:
        """Check if LLaVA server is running."""
        try:
            # Create session without proxy for localhost
            session = requests.Session()
            session.proxies = {
                'http': None,
                'https': None
            }
            session.trust_env = False
            
            response = session.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"LLaVA server check failed: {e}")
            return False
