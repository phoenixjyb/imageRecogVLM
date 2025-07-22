"""Kimi VLM client implementation using Moonshot API."""

import http.client
import json
import ssl
import os
import sys
from typing import Dict, Any, List

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vlm.base import VLMClient

class KimiClient(VLMClient):
    """Client for Moonshot Kimi vision model."""
    
    def __init__(self, api_key: str, model: str = "moonshot-v1-32k-vision-preview"):
        """Initialize Kimi client."""
        super().__init__(api_key, model)
        self.base_url = "api.moonshot.cn"
        self.endpoint = "/v1/chat/completions"
        self.timeout = 90  # Increase timeout for vision models
    
    def query_image(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Query Kimi with image and prompt."""
        if not self.validate_api_key():
            return self.handle_error(ValueError("No API key provided"), "Kimi query")
        
        if not self.validate_image_data(image_data):
            return self.handle_error(ValueError("Invalid image data"), "Kimi query")
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Establish HTTPS connection with timeout
            conn = http.client.HTTPSConnection(self.base_url, context=context, timeout=self.timeout)
            
            # Prepare payload - Moonshot API follows OpenAI format
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
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Send request with timeout handling
            conn.request("POST", self.endpoint, json.dumps(payload), headers)
            response = conn.getresponse()
            
            if response.status == 200:
                data = response.read()
                result = json.loads(data.decode('utf-8'))
                self.logger.info("Kimi query successful")
                return {
                    'success': True,
                    'response': result,
                    'provider': 'kimi'
                }
            else:
                error_msg = f"Kimi API error: {response.status} - {response.read().decode('utf-8')}"
                return self.handle_error(ValueError(error_msg), "Kimi API")
                
        except Exception as e:
            # Handle specific timeout errors
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                error_msg = f"Kimi API timeout after {self.timeout}s - try reducing image size or check network connection"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'provider': 'kimi'
                }
            return self.handle_error(e, "Kimi query")
        finally:
            try:
                conn.close()
            except:
                pass
    
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Kimi response to extract object coordinates."""
        objects = []
        
        try:
            if not response.get('success', False):
                return objects
            
            # Extract content from Kimi response (OpenAI format)
            api_response = response.get('response', {})
            choices = api_response.get('choices', [])
            
            if not choices:
                self.logger.warning("No choices found in Kimi response")
                return objects
            
            content = choices[0].get('message', {}).get('content', '')
            self.logger.info(f"Kimi response content: {content[:200]}...")
            
            # Parse coordinate table format like other VLMs
            coordinates = self._parse_coordinate_table(content)
            
            # Convert to object format
            for i, (h, v, id_num) in enumerate(coordinates):
                if h > 0 or v > 0:  # Skip (0,0) coordinates
                    objects.append({
                        'coordinates': [float(h), float(v)],
                        'confidence': 0.8,  # Default confidence
                        'id': id_num,
                        'source': 'kimi'
                    })
            
            self.logger.info(f"Parsed {len(objects)} objects from Kimi response")
            return objects
            
        except Exception as e:
            self.logger.error(f"Error parsing Kimi response: {e}")
            return objects
    
    def _parse_coordinate_table(self, content: str) -> List[tuple]:
        """Parse coordinate table from response content."""
        import re
        
        coordinates = []
        
        try:
            # Look for table format: | H | V | ID |
            lines = content.split('\n')
            
            for line in lines:
                if '|' in line:
                    # Clean and split by pipe
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    
                    if len(cells) >= 2:
                        try:
                            # Try to parse as numbers
                            h = int(float(cells[0]))
                            v = int(float(cells[1]))
                            id_num = cells[2] if len(cells) > 2 and cells[2].isdigit() else str(len(coordinates) + 1)
                            
                            coordinates.append((h, v, id_num))
                            
                        except ValueError:
                            # Skip non-numeric rows (headers, etc.)
                            continue
            
            # Also try regex patterns for coordinate extraction
            if not coordinates:
                patterns = [
                    r'\((\d+)\s*,\s*(\d+)\)',  # (x, y) format
                    r'(\d+)\s*,\s*(\d+)',      # x, y format
                    r'H[:\s]*(\d+).*?V[:\s]*(\d+)',  # H: x V: y format
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for i, match in enumerate(matches):
                        h, v = int(match[0]), int(match[1])
                        coordinates.append((h, v, str(i + 1)))
                    
                    if coordinates:
                        break
            
        except Exception as e:
            self.logger.error(f"Error parsing coordinate table: {e}")
        
        return coordinates
    
    def analyze_image(self, image_data: str, prompt: str) -> str:
        """Analyze image with Kimi and return raw response text."""
        try:
            result = self.query_image(image_data, prompt)
            
            if result.get('success', False):
                api_response = result.get('response', {})
                choices = api_response.get('choices', [])
                
                if choices:
                    return choices[0].get('message', {}).get('content', '')
            
            return "Error: Failed to get response from Kimi API"
            
        except Exception as e:
            self.logger.error(f"Error in Kimi image analysis: {e}")
            return f"Error: {str(e)}"
