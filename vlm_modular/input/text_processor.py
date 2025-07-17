"""Text processing utilities for VLM queries."""

import re
import logging
import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import VLMSettings

class TextProcessor:
    """Handles text processing and query preparation for VLM requests."""
    
    def __init__(self, settings: VLMSettings):
        """Initialize text processor with settings."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Chinese to English translation mapping for common objects
        self.chinese_to_english = {
            "红色汽车": "red car",
            "蓝色卡车": "blue truck", 
            "人": "person",
            "自行车": "bicycle",
            "摩托车": "motorcycle",
            "飞机": "airplane",
            "公交车": "bus",
            "火车": "train",
            "船": "boat",
            "汽车": "car",
            "卡车": "truck",
            "红色": "red",
            "蓝色": "blue",
            "绿色": "green",
            "黄色": "yellow",
            "黑色": "black",
            "白色": "white"
        }
    
    def process_user_query(self, query: str) -> str:
        """Process user query and normalize it."""
        if not query:
            return ""
        
        # Clean the query
        query = query.strip().lower()
        
        # Translate Chinese to English if needed
        query = self.translate_chinese_to_english(query)
        
        # Normalize common variations
        query = self.normalize_query(query)
        
        self.logger.info(f"Processed query: {query}")
        return query
    
    def translate_chinese_to_english(self, text: str) -> str:
        """Translate Chinese terms to English."""
        # Check for exact matches first
        if text in self.chinese_to_english:
            translated = self.chinese_to_english[text]
            self.logger.info(f"Translated '{text}' to '{translated}'")
            return translated
        
        # Check for partial matches
        for chinese, english in self.chinese_to_english.items():
            if chinese in text:
                text = text.replace(chinese, english)
                self.logger.info(f"Partial translation: {text}")
        
        return text
    
    def normalize_query(self, query: str) -> str:
        """Normalize query variations to standard forms."""
        # Common object normalizations
        normalizations = {
            "automobile": "car",
            "vehicle": "car", 
            "motorbike": "motorcycle",
            "bike": "bicycle",
            "plane": "airplane",
            "person walking": "person",
            "people": "person",
            "human": "person"
        }
        
        for variant, standard in normalizations.items():
            if variant in query:
                query = query.replace(variant, standard)
        
        return query
    
    def create_vlm_prompt(self, query: str, provider: str, image_width: int = 640, image_height: int = 480) -> str:
        """Create optimized prompt for specific VLM provider."""
        base_prompt = f"Find and locate all instances of '{query}' in this image."
        
        if provider.lower() == "grok":
            return self._create_grok_prompt(query, image_width, image_height)
        elif provider.lower() == "qwen":
            return self._create_qwen_prompt(query, image_width, image_height)
        elif provider.lower() == "llava":
            return self._create_llava_prompt(query, image_width, image_height)
        else:
            return base_prompt
    
    def _create_grok_prompt(self, query: str, image_width: int, image_height: int) -> str:
        """Create Grok-optimized prompt - matches original imageRecogVLM.py exactly."""
        # Use the exact same logic as build_grok_prompt from original
        return (
            f"Analyze this {image_width}x{image_height} pixel image. "
            f"Locate all instances of '{query}' in the image. "
            f"For each '{query}' object found: "
            f"1. Calculate the exact center point of the object "
            f"2. Provide coordinates in this table format: "
            f"| H | V | ID | "
            f"|---|---|----| "
            f"Where H = horizontal center pixel, V = vertical center pixel. "
            f"If no '{query}' is found, return: | 0 | 0 | 0 |"
        )
    
    def _create_qwen_prompt(self, query: str, image_width: int, image_height: int) -> str:
        """Create Qwen-optimized prompt - copied from original imageRecogVLM.py."""
        return (
            f"Analyze this {image_width}x{image_height} pixel image. "
            f"Look for '{query}' objects in the image. "
            f"For each '{query}' you find, identify where the center of that object is located. "
            f"Provide the center coordinates in this table format: "
            f"| H | V | ID |"
            f"|---|---|----| "
            f"Where H is the horizontal pixel position and V is the vertical pixel position of the center. "
            f"If you don't see any '{query}', return: | 0 | 0 | 0 |"
        )
    
    def _create_llava_prompt(self, query: str, image_width: int, image_height: int) -> str:
        """Create LLaVA-optimized prompt - copied from original imageRecogVLM.py."""
        return f"""Analyze this {image_width}x{image_height} pixel image carefully. Look for '{query}' objects in the image.

For each '{query}' object you find:
1. Determine the exact center point of that object
2. Give me the center coordinates in this format:

Center point: (H, V)

Where H is the horizontal pixel position (0-{image_width}) and V is the vertical pixel position (0-{image_height}).
VERIFY that all coordinates are within the image bounds before responding.
If you find multiple objects, list each center point separately."""
    
    def extract_object_name(self, query: str) -> str:
        """Extract the main object name from a query."""
        if not query:
            return ""
        
        query = query.lower().strip()
        
        # Define patterns to extract objects from different command formats
        patterns = [
            # "pass me the [object]", "give me the [object]", "hand me the [object]" - me is optional
            r'(?:pass|give|hand|fetch|bring|get)\s+(?:me\s+)?(?:the\s+)?(\w+)',
            # "find the [object]", "locate the [object]", "show me the [object]"
            r'(?:find|locate|show|detect)\s+(?:me\s+)?(?:the\s+)?(\w+)',
            # "where is the [object]", "find me the [object]"
            r'(?:where\s+is|find\s+me)\s+(?:the\s+)?(\w+)',
            # "I need the [object]", "I want the [object]"
            r'(?:i\s+(?:need|want|see))\s+(?:the\s+)?(\w+)',
            # "[color] [object]" - like "red car", "blue truck"
            r'(?:red|blue|green|yellow|black|white|orange|purple|pink|brown)\s+(\w+)',
            # "the [object]" - simple pattern
            r'(?:the\s+)?(\w+)',
        ]
        
        # Try each pattern in order of specificity
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                object_name = match.group(1)
                # Filter out common non-object words
                if object_name not in ['me', 'is', 'you', 'it', 'that', 'this', 'can', 'will', 'should']:
                    self.logger.info(f"Extracted object '{object_name}' from query '{query}'")
                    return object_name
        
        # Fallback: remove common command words and return remaining meaningful words
        words_to_remove = {
            'please', 'can', 'you', 'help', 'me', 'pass', 'give', 'hand', 'bring', 
            'get', 'fetch', 'find', 'locate', 'show', 'detect', 'where', 'is', 
            'the', 'a', 'an', 'all', 'some', 'i', 'need', 'want', 'see', 'to',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that',
            'these', 'those', 'and', 'or', 'but', 'for', 'with', 'at', 'in',
            'on', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'why', 'how', 'what', 'which',
            'who', 'if', 'because', 'as', 'until', 'while', 'of', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'from', 'by', 'very', 'too', 'any', 'may', 'might', 'must',
            'shall', 'will', 'would', 'should', 'could', 'ought', 'am', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'say', 'says', 'said', 'go', 'goes', 'went', 'gone'
        }
        
        words = query.split()
        filtered_words = [word for word in words if word not in words_to_remove and len(word) > 1]
        
        if filtered_words:
            # Return the last meaningful word (likely the object)
            object_name = filtered_words[-1]
            self.logger.info(f"Fallback extracted object '{object_name}' from query '{query}'")
            return object_name
        
        # Ultimate fallback
        self.logger.warning(f"Could not extract object from query '{query}', using original")
        return query
    
    def validate_query(self, query: str) -> bool:
        """Validate if query is suitable for object detection."""
        if not query or len(query.strip()) < 2:
            return False
        
        # Check for basic object detection terms
        valid_patterns = [
            r'\b(car|truck|person|bicycle|motorcycle|airplane|bus|train|boat)\b',
            r'\b(red|blue|green|yellow|black|white)\s+\w+',
            r'\w+\s+(car|truck|vehicle|object)'
        ]
        
        for pattern in valid_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        # If no patterns match, still allow the query (might be valid)
        return True
    
    def get_query_metadata(self, query: str) -> Dict[str, Any]:
        """Extract metadata from query for processing optimization."""
        metadata = {
            'original_query': query,
            'processed_query': self.process_user_query(query),
            'object_name': self.extract_object_name(query),
            'has_color': bool(re.search(r'\b(red|blue|green|yellow|black|white|orange|purple|pink|brown|gray|grey)\b', query, re.IGNORECASE)),
            'has_size': bool(re.search(r'\b(big|small|large|tiny|huge|little)\b', query, re.IGNORECASE)),
            'is_valid': self.validate_query(query),
            'language': 'chinese' if any(ord(char) > 127 for char in query) else 'english'
        }
        
        return metadata
