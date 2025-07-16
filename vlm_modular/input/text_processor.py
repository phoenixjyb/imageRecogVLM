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
    
    def create_vlm_prompt(self, query: str, provider: str) -> str:
        """Create optimized prompt for specific VLM provider."""
        base_prompt = f"Find and locate all instances of '{query}' in this image."
        
        if provider.lower() == "grok":
            return self._create_grok_prompt(query)
        elif provider.lower() == "qwen":
            return self._create_qwen_prompt(query)
        elif provider.lower() == "llava":
            return self._create_llava_prompt(query)
        else:
            return base_prompt
    
    def _create_grok_prompt(self, query: str) -> str:
        """Create Grok-optimized prompt."""
        return f"""Find all instances of '{query}' in this image and provide their locations.

For each object found, provide the bounding box coordinates in this exact format:
Object: {query}
Bounding box: [x1, y1, x2, y2]

Where:
- x1, y1 are the top-left corner coordinates  
- x2, y2 are the bottom-right corner coordinates
- Coordinates should be actual pixel values

Please be precise with the coordinates and list each instance separately."""
    
    def _create_qwen_prompt(self, query: str) -> str:
        """Create Qwen-optimized prompt."""
        return f"""Analyze this image and find all instances of '{query}'. 

Provide the results in a clear table format:

| Object | Bounding Box |
|--------|--------------|
| {query} | [x1,y1,x2,y2] |

Use actual pixel coordinates where [x1,y1] is top-left and [x2,y2] is bottom-right.
List each instance as a separate row."""
    
    def _create_llava_prompt(self, query: str) -> str:
        """Create LLaVA-optimized prompt."""
        return f"""Look at this image and find all '{query}' objects.

For each {query} you find, give me:
1. Object name: {query}
2. Location: [x1, y1, x2, y2] in pixels

Format each result clearly:
Object: {query}
Coordinates: [x1, y1, x2, y2]

Be specific with pixel coordinates."""
    
    def extract_object_name(self, query: str) -> str:
        """Extract the main object name from a query."""
        # Remove common articles and adjectives
        words_to_remove = ["the", "a", "an", "all", "some", "find", "locate", "detect"]
        
        words = query.split()
        filtered_words = [word for word in words if word not in words_to_remove]
        
        # Return the main object (usually the last significant word)
        if filtered_words:
            return " ".join(filtered_words)
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
