"""Coordinate parsing utilities for VLM responses."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

class CoordinateParser:
    """Parses coordinates from VLM responses in various formats."""
    
    def __init__(self):
        """Initialize coordinate parser."""
        self.logger = logging.getLogger(__name__)
        
        # Define coordinate patterns for different formats
        self.patterns = {
            # Center point table format: | H | V | ID |
            'center_table': r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|',
            # Center point parentheses format: (H, V) or Center point: (H, V)
            'center_paren': r'(?:center point:?|center:?)?\s*\((\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)',
            # Legacy bounding box formats (for fallback)
            'bracket_coords': r'\[(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]',
            'paren_coords': r'\((\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)',
            'bbox_format': r'(?:bounding box|bbox|coordinates?):\s*\[?(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]?',
            'ratio_coords': r'(?:0\.\d+)\s*,\s*(?:0\.\d+)\s*,\s*(?:0\.\d+)\s*,\s*(?:0\.\d+)',
            'pixel_coords': r'(\d{1,4})\s*,\s*(\d{1,4})\s*,\s*(\d{1,4})\s*,\s*(\d{1,4})',
            'object_coords': r'Object:\s*\w+.*?(?:coordinates?|location):\s*\[?(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\]?'
        }
    
    def parse_coordinates(self, text: str, image_width: int = 640, image_height: int = 480) -> List[Dict[str, Any]]:
        """Parse coordinates from text response."""
        if not text:
            return []
        
        all_objects = []
        
        # Try each parsing method (prioritize center point formats)
        all_objects.extend(self._parse_center_point_formats(text, image_width, image_height))
        all_objects.extend(self._parse_standard_coordinates(text))
        all_objects.extend(self._parse_table_format(text))
        all_objects.extend(self._parse_ratio_coordinates(text, image_width, image_height))
        all_objects.extend(self._parse_descriptive_coordinates(text, image_width, image_height))
        
        # Remove duplicates and validate
        validated_objects = self._validate_and_deduplicate(all_objects, image_width, image_height)
        
        self.logger.info(f"Parsed {len(validated_objects)} valid coordinate sets from text")
        return validated_objects
    
    def _parse_standard_coordinates(self, text: str) -> List[Dict[str, Any]]:
        """Parse standard coordinate formats."""
        objects = []
        
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == 'ratio_coords':  # Handle separately
                continue
                
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    coords = [float(x) for x in match.groups()]
                    if len(coords) == 4:
                        # Create object with center point calculation (assuming pixel coordinates)
                        obj = self._create_object_with_center(
                            'detected_object',
                            coords,
                            640,  # Default width, will be recalculated if needed
                            480,  # Default height, will be recalculated if needed
                            confidence=self._get_confidence_for_pattern(pattern_name)
                        )
                        obj['source'] = f'parser_{pattern_name}'
                        objects.append(obj)
                except (ValueError, IndexError):
                    continue
        
        return objects
    
    def _parse_table_format(self, text: str) -> List[Dict[str, Any]]:
        """Parse markdown table format."""
        objects = []
        lines = text.split('\n')
        
        for line in lines:
            if '|' in line and ('[' in line or '(' in line):
                # Extract coordinates from table cells
                for pattern_name in ['bracket_coords', 'paren_coords']:
                    pattern = self.patterns[pattern_name]
                    match = re.search(pattern, line)
                    if match:
                        try:
                            coords = [float(x) for x in match.groups()]
                            objects.append({
                                'coordinates': coords,
                                'confidence': 0.7,
                                'source': 'parser_table'
                            })
                            break
                        except (ValueError, IndexError):
                            continue
        
        return objects
    
    def _parse_ratio_coordinates(self, text: str, image_width: int, image_height: int) -> List[Dict[str, Any]]:
        """Parse ratio-based coordinates (0.0 to 1.0) and convert to pixels."""
        objects = []
        
        # Look for ratio patterns
        ratio_pattern = r'(0\.\d+)\s*,\s*(0\.\d+)\s*,\s*(0\.\d+)\s*,\s*(0\.\d+)'
        matches = re.finditer(ratio_pattern, text)
        
        for match in matches:
            try:
                ratios = [float(x) for x in match.groups()]
                
                # Create object with center point calculation
                obj = self._create_object_with_center(
                    'detected_object',
                    ratios,
                    image_width,
                    image_height,
                    confidence=0.7
                )
                objects.append(obj)
                
            except (ValueError, IndexError):
                continue
        
        return objects
    
    def _parse_descriptive_coordinates(self, text: str, image_width: int, image_height: int) -> List[Dict[str, Any]]:
        """Parse descriptive location terms and convert to approximate coordinates."""
        objects = []
        
        # Define descriptive patterns and their approximate coordinates
        descriptive_map = {
            r'(?:top|upper).*?(?:left|corner)': (0.1, 0.1, 0.3, 0.3),
            r'(?:top|upper).*?(?:right|corner)': (0.7, 0.1, 0.9, 0.3),
            r'(?:bottom|lower).*?(?:left|corner)': (0.1, 0.7, 0.3, 0.9),
            r'(?:bottom|lower).*?(?:right|corner)': (0.7, 0.7, 0.9, 0.9),
            r'(?:center|middle|central)': (0.35, 0.35, 0.65, 0.65),
            r'(?:left|left side)': (0.05, 0.35, 0.25, 0.65),
            r'(?:right|right side)': (0.75, 0.35, 0.95, 0.65),
            r'(?:top|upper)(?!\s*(?:left|right))': (0.35, 0.05, 0.65, 0.25),
            r'(?:bottom|lower)(?!\s*(?:left|right))': (0.35, 0.75, 0.65, 0.95)
        }
        
        text_lower = text.lower()
        for pattern, ratio_coords in descriptive_map.items():
            if re.search(pattern, text_lower):
                # Create object with center point calculation from ratio coordinates
                obj = self._create_object_with_center(
                    'detected_object',
                    list(ratio_coords),
                    image_width,
                    image_height,
                    confidence=0.3
                )
                obj['source'] = 'parser_descriptive'
                objects.append(obj)
                break  # Only use first match
        
        return objects
    
    def _validate_and_deduplicate(self, objects: List[Dict[str, Any]], 
                                 image_width: int, image_height: int) -> List[Dict[str, Any]]:
        """Validate coordinates and remove duplicates."""
        validated = []
        
        for obj in objects:
            coords = obj['coordinates']
            
            # Basic validation
            if not self._validate_coordinates(coords, image_width, image_height):
                continue
            
            # Check for duplicates (within 10 pixels tolerance)
            if not self._is_duplicate(coords, validated, tolerance=10):
                validated.append(obj)
        
        # Sort by confidence (highest first)
        validated.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return validated
    
    def _validate_coordinates(self, coords: List[float], image_width: int, image_height: int) -> bool:
        """Validate if coordinates are reasonable."""
        # Use more lenient bounds like the original implementation
        # VLMs sometimes return coordinates slightly outside image bounds
        max_width = image_width * 2
        max_height = image_height * 2
        
        if len(coords) == 2:
            # Center point coordinates (H, V)
            h, v = coords
            
            # Check if coordinates are non-negative
            if h < 0 or v < 0:
                return False
            
            # Check if coordinates are within lenient bounds
            if h >= max_width or v >= max_height:
                return False
                
            return True
            
        elif len(coords) == 4:
            # Bounding box coordinates (x1, y1, x2, y2)
            x1, y1, x2, y2 = coords
            
            # Check if coordinates are non-negative
            if any(coord < 0 for coord in coords):
                return False
            
            # Check if coordinates are within lenient bounds
            if x1 >= max_width or y1 >= max_height or x2 >= max_width or y2 >= max_height:
                return False
            
            # Check if bounding box is valid (x2 > x1, y2 > y1)
            if x2 <= x1 or y2 <= y1:
                return False
            
            # Check if bounding box is reasonably sized (not too small)
            min_size = 5
            if (x2 - x1) < min_size or (y2 - y1) < min_size:
                return False
            
            return True
        else:
            return False
    
    def _is_duplicate(self, coords: List[float], existing: List[Dict[str, Any]], tolerance: float = 10) -> bool:
        """Check if coordinates are duplicate of existing ones."""
        if len(coords) == 2:
            # Center point coordinates
            h, v = coords
            
            for existing_obj in existing:
                existing_coords = existing_obj.get('coordinates', [])
                if len(existing_coords) == 2:
                    # Compare center points
                    eh, ev = existing_coords
                    if abs(h - eh) <= tolerance and abs(v - ev) <= tolerance:
                        return True
                elif len(existing_coords) == 4:
                    # Compare center point to existing bounding box center
                    ex1, ey1, ex2, ey2 = existing_coords
                    center_h = (ex1 + ex2) / 2
                    center_v = (ey1 + ey2) / 2
                    if abs(h - center_h) <= tolerance and abs(v - center_v) <= tolerance:
                        return True
            
        elif len(coords) == 4:
            # Bounding box coordinates
            x1, y1, x2, y2 = coords
            
            for existing_obj in existing:
                existing_coords = existing_obj.get('coordinates', [])
                if len(existing_coords) == 4:
                    # Compare bounding boxes
                    ex1, ey1, ex2, ey2 = existing_coords
                    if (abs(x1 - ex1) <= tolerance and abs(y1 - ey1) <= tolerance and
                        abs(x2 - ex2) <= tolerance and abs(y2 - ey2) <= tolerance):
                        return True
                elif len(existing_coords) == 2:
                    # Compare bounding box center to existing center point
                    eh, ev = existing_coords
                    center_h = (x1 + x2) / 2
                    center_v = (y1 + y2) / 2
                    if abs(center_h - eh) <= tolerance and abs(center_v - ev) <= tolerance:
                        return True
        
        return False
    
    def _get_confidence_for_pattern(self, pattern_name: str) -> float:
        """Get confidence score based on pattern type."""
        confidence_map = {
            'bracket_coords': 0.8,
            'paren_coords': 0.7,
            'bbox_format': 0.9,
            'pixel_coords': 0.6,
            'object_coords': 0.8
        }
        return confidence_map.get(pattern_name, 0.5)
    
    def parse_single_coordinate_set(self, text: str) -> Optional[List[float]]:
        """Parse a single set of coordinates from text."""
        objects = self.parse_coordinates(text)
        if objects:
            return objects[0]['coordinates']
        return None
    
    def extract_coordinate_context(self, text: str) -> List[Dict[str, Any]]:
        """Extract coordinates with surrounding context."""
        results = []
        
        for pattern_name, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    coords = [float(x) for x in match.groups()]
                    if len(coords) == 4:
                        # Get surrounding context (50 chars before and after)
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end]
                        
                        results.append({
                            'coordinates': coords,
                            'pattern': pattern_name,
                            'context': context.strip(),
                            'match_text': match.group(),
                            'confidence': self._get_confidence_for_pattern(pattern_name)
                        })
                except (ValueError, IndexError):
                    continue
        
        return results
    
    def calculate_center_point(self, coordinates: List[float], image_width: int, image_height: int) -> Dict[str, Any]:
        """Calculate center point from coordinates in different formats."""
        if len(coordinates) == 2:
            # Assume it's already center point coordinates (H, V)
            h, v = coordinates
            return {
                'center_h': int(h),
                'center_v': int(v),
                'format': 'center_point'
            }
        elif len(coordinates) == 4:
            x1, y1, x2, y2 = coordinates
            
            # Check if coordinates are ratios (between 0 and 1)
            if all(0 <= coord <= 1 for coord in coordinates):
                # Convert ratios to pixel coordinates
                x1_pixel = x1 * image_width
                y1_pixel = y1 * image_height
                x2_pixel = x2 * image_width
                y2_pixel = y2 * image_height
                
                # Calculate center point
                center_h = int((x1_pixel + x2_pixel) / 2)
                center_v = int((y1_pixel + y2_pixel) / 2)
                
                return {
                    'center_h': center_h,
                    'center_v': center_v,
                    'bbox_pixels': [int(x1_pixel), int(y1_pixel), int(x2_pixel), int(y2_pixel)],
                    'bbox_ratios': coordinates,
                    'format': 'ratio_bbox'
                }
            else:
                # Already pixel coordinates, calculate center
                center_h = int((x1 + x2) / 2)
                center_v = int((y1 + y2) / 2)
                
                return {
                    'center_h': center_h,
                    'center_v': center_v,
                    'bbox_pixels': [int(x1), int(y1), int(x2), int(y2)],
                    'format': 'pixel_bbox'
                }
        else:
            # Invalid coordinate format
            return {
                'center_h': 0,
                'center_v': 0,
                'format': 'invalid'
            }

    def _create_object_with_center(self, object_name: str, coordinates: List[float], 
                                 image_width: int, image_height: int, 
                                 confidence: float = 0.8) -> Dict[str, Any]:
        """Create object dictionary with center point calculation."""
        center_data = self.calculate_center_point(coordinates, image_width, image_height)
        
        return {
            'object': object_name,
            'coordinates': coordinates,
            'center_h': center_data['center_h'],
            'center_v': center_data['center_v'],
            'bbox_pixels': center_data.get('bbox_pixels', coordinates if len(coordinates) == 4 else []),
            'confidence': confidence,
            'format': center_data['format'],
            'source': 'coordinate_parser'
        }
    
    def _parse_center_point_formats(self, text: str, image_width: int, image_height: int) -> List[Dict[str, Any]]:
        """Parse center point table and other center point formats."""
        objects = []
        
        # Parse center point table format: | H | V | ID |
        center_table_pattern = r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|'
        matches = re.finditer(center_table_pattern, text)
        for match in matches:
            try:
                h, v, id_num = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if h == 0 and v == 0:  # Skip "not found" responses
                    continue
                
                # Validate and clip coordinates to image bounds
                original_h, original_v = h, v
                h = max(0, min(h, image_width - 1))
                v = max(0, min(v, image_height - 1))
                
                if original_h != h or original_v != v:
                    self.logger.warning(f"Clipped coordinates from ({original_h},{original_v}) to ({h},{v}) for image bounds {image_width}x{image_height}")
                    
                obj = {
                    'object_name': 'detected_object',
                    'coordinates': [h, v],  # Center point coordinates
                    'center_h': h,
                    'center_v': v,
                    'confidence': 0.9 if original_h == h and original_v == v else 0.7,  # Lower confidence for clipped coordinates
                    'format': 'center_point',
                    'source': 'center_table',
                    'valid': True
                }
                objects.append(obj)
                self.logger.info(f"Found center point from table: H={h}, V={v}, ID={id_num}")
            except (ValueError, IndexError):
                continue
        
        # Parse center point parentheses format: (H, V) or Center point: (H, V)
        center_paren_pattern = r'(?:center point:?|center:?)?\s*\((\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)'
        matches = re.finditer(center_paren_pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                h, v = float(match.group(1)), float(match.group(2))
                
                # Check if these are ratio coordinates (0-1 range)
                if 0 <= h <= 1 and 0 <= v <= 1:
                    h = int(h * image_width)
                    v = int(v * image_height)
                else:
                    h, v = int(h), int(v)
                
                obj = {
                    'object_name': 'detected_object',
                    'coordinates': [h, v],  # Center point coordinates
                    'center_h': h,
                    'center_v': v,
                    'confidence': 0.85,
                    'format': 'center_point',
                    'source': 'center_paren',
                    'valid': True
                }
                objects.append(obj)
                self.logger.info(f"Found center point from parentheses: H={h}, V={v}")
            except (ValueError, IndexError):
                continue
        
        return objects
