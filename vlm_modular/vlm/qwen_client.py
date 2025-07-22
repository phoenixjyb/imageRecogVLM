"""Qwen VLM client implementation."""

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

class QwenClient(VLMClient):
    """Client for Alibaba Qwen vision model."""
    
    def __init__(self, api_key: str, model: str = "qwen-vl-max"):
        """Initialize Qwen client."""
        super().__init__(api_key, model)
        self.base_url = "dashscope.aliyuncs.com"
        self.endpoint = "/api/v1/services/aigc/multimodal-generation/generation"
    
    def query_image(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Query Qwen with image and prompt."""
        if not self.validate_api_key():
            return self.handle_error(ValueError("No API key provided"), "Qwen query")
        
        if not self.validate_image_data(image_data):
            return self.handle_error(ValueError("Invalid image data"), "Qwen query")
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Establish HTTPS connection
            conn = http.client.HTTPSConnection(self.base_url, context=context)
            
            # Prepare payload
            payload = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"text": prompt},
                                {"image": f"data:image/jpeg;base64,{image_data}"}
                            ]
                        }
                    ]
                },
                "parameters": {
                    "max_tokens": 2000
                }
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Send request
            conn.request("POST", self.endpoint, json.dumps(payload), headers)
            response = conn.getresponse()
            
            if response.status == 200:
                data = response.read()
                result = json.loads(data.decode('utf-8'))
                self.logger.info("Qwen query successful")
                return {
                    'success': True,
                    'response': result,
                    'provider': 'qwen'
                }
            else:
                error_msg = f"Qwen API error: {response.status} - {response.read().decode('utf-8')}"
                return self.handle_error(ValueError(error_msg), "Qwen API")
                
        except Exception as e:
            return self.handle_error(e, "Qwen query")
        finally:
            try:
                conn.close()
            except:
                pass
    
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Qwen response to extract object coordinates."""
        objects = []
        
        try:
            if not response.get('success', False):
                return objects
            
            # Extract content from Qwen response
            content = ""
            if 'response' in response and 'output' in response['response']:
                output = response['response']['output']
                if 'choices' in output and len(output['choices']) > 0:
                    choice = output['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        message_content = choice['message']['content']
                        if isinstance(message_content, list):
                            # Handle list format
                            for item in message_content:
                                if isinstance(item, dict) and 'text' in item:
                                    content += item['text'] + " "
                        else:
                            content = str(message_content)
            
            if not content:
                self.logger.warning("No content found in Qwen response")
                return objects
            
            self.logger.info(f"Parsing Qwen content: {content[:200]}...")
            
            # Parse using different methods
            objects.extend(self._parse_table_format(content))
            objects.extend(self._parse_coordinate_patterns(content))
            objects.extend(self._parse_ratio_coordinates(content))
            
            self.logger.info(f"Qwen parser found {len(objects)} objects")
            return objects
            
        except Exception as e:
            self.logger.error(f"Error parsing Qwen response: {e}")
            return objects
    
    def _parse_table_format(self, content: str) -> List[Dict[str, Any]]:
        """Parse table format with coordinates."""
        import re
        objects = []
        
        # Look for markdown table format
        lines = content.split('\n')
        for line in lines:
            if '|' in line and ('[' in line or '(' in line):
                # Extract coordinates from various bracket formats
                patterns = [
                    r'\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]',
                    r'\((\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)',
                    r'(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        coords = [float(x) for x in match.groups()]
                        if len(coords) == 4:
                            objects.append({
                                'coordinates': coords,
                                'confidence': 0.8,
                                'source': 'qwen_table'
                            })
                        break
        
        return objects
    
    def _parse_coordinate_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Parse various coordinate patterns."""
        import re
        objects = []
        
        # Multiple coordinate patterns
        patterns = [
            r'(?:coordinates?|bbox|box):\s*\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]',
            r'(?:位置|坐标):\s*\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]',
            r'\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]'
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
                        'source': 'qwen_pattern'
                    })
        
        return objects
    
    def _parse_ratio_coordinates(self, content: str) -> List[Dict[str, Any]]:
        """Parse ratio-based coordinates and convert to pixels."""
        import re
        objects = []
        
        # Look for ratio patterns like 0.1, 0.2, 0.3, 0.4
        ratio_pattern = r'(?:0\.\d+)\s*,\s*(?:0\.\d+)\s*,\s*(?:0\.\d+)\s*,\s*(?:0\.\d+)'
        matches = re.finditer(ratio_pattern, content)
        
        for match in matches:
            # Extract ratios and convert to coordinates (assuming 640x480 image)
            ratio_str = match.group()
            ratios = [float(x.strip()) for x in ratio_str.split(',')]
            
            if len(ratios) == 4:
                # Convert ratios to pixel coordinates (assuming 640x480)
                x1 = ratios[0] * 640
                y1 = ratios[1] * 480
                x2 = ratios[2] * 640
                y2 = ratios[3] * 480
                
                objects.append({
                    'coordinates': [x1, y1, x2, y2],
                    'confidence': 0.6,
                    'source': 'qwen_ratio'
                })
        
        return objects
