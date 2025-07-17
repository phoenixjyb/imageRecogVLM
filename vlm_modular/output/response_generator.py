"""Response generation for VLM object detection results."""

import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import VLMSettings

class ResponseGenerator:
    """Generates human-readable responses from VLM detection results."""
    
    def __init__(self, settings: VLMSettings):
        """Initialize response generator with settings."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, objects: List[Dict[str, Any]], object_name: str, 
                         provider: str, query: str = "") -> str:
        """Generate response text from detection results."""
        if not objects:
            return self._generate_not_found_response(object_name, provider)
        
        return self._generate_found_response(objects, object_name, provider, query)
    
    def _generate_not_found_response(self, object_name: str, provider: str) -> str:
        """Generate response when no objects are found."""
        responses = [
            f"I couldn't find any {object_name} in the image.",
            f"No {object_name} detected in the current image.",
            f"Sorry, I don't see any {object_name} in this picture.",
            f"The image doesn't appear to contain any {object_name}."
        ]
        
        # Add provider-specific notes
        provider_notes = {
            'grok': "Grok vision analysis completed.",
            'qwen': "Qwen vision analysis completed.",
            'llava': "LLaVA local analysis completed."
        }
        
        base_response = responses[0]  # Use first response as default
        provider_note = provider_notes.get(provider.lower(), f"{provider} analysis completed.")
        
        return f"{base_response} {provider_note}"
    
    def _generate_found_response(self, objects: List[Dict[str, Any]], object_name: str, 
                                provider: str, query: str) -> str:
        """Generate response when objects are found."""
        count = len(objects)
        
        # Basic count message
        if count == 1:
            base_msg = f"I found 1 {object_name} in the image."
        else:
            base_msg = f"I found {count} {object_name}s in the image."
        
        # Add confidence information
        confidence_info = self._generate_confidence_summary(objects)
        
        # Add location summary
        location_info = self._generate_location_summary(objects)
        
        # Add provider info
        provider_info = self._generate_provider_info(provider, objects)
        
        # Combine all parts
        parts = [base_msg]
        if confidence_info:
            parts.append(confidence_info)
        if location_info:
            parts.append(location_info)
        if provider_info:
            parts.append(provider_info)
        
        return " ".join(parts)
    
    def _generate_confidence_summary(self, objects: List[Dict[str, Any]]) -> str:
        """Generate confidence summary for detections."""
        if not objects:
            return ""
        
        confidences = [obj.get('confidence', 0.5) for obj in objects]
        avg_confidence = sum(confidences) / len(confidences)
        max_confidence = max(confidences)
        
        if avg_confidence >= 0.8:
            return "Detection confidence is high."
        elif avg_confidence >= 0.6:
            return "Detection confidence is moderate."
        elif max_confidence >= 0.7:
            return "Some detections have good confidence."
        else:
            return "Detection confidence is low - results may be approximate."
    
    def _generate_location_summary(self, objects: List[Dict[str, Any]]) -> str:
        """Generate location summary with center points for detections."""
        if not objects:
            return ""
        
        # Generate center point table
        center_table = self._generate_center_point_table(objects)
        
        if len(objects) == 1:
            obj = objects[0]
            center_h = obj.get('center_h', 0)
            center_v = obj.get('center_v', 0)
            descriptive_location = self._describe_location_from_center(center_h, center_v)
            return f"Center point: H={center_h}, V={center_v} (located {descriptive_location}). {center_table}"
        else:
            return f"Multiple objects detected. {center_table}"
    
    def _generate_center_point_table(self, objects: List[Dict[str, Any]]) -> str:
        """Generate a table showing center points (H, V) for all detected objects."""
        if not objects:
            return ""
        
        table_lines = [
            "\n📊 Center Point Summary:",
            "| Object ID | H (Horizontal) | V (Vertical) | Format |",
            "|-----------|----------------|--------------|--------|"
        ]
        
        for i, obj in enumerate(objects, 1):
            center_h = obj.get('center_h', 0)
            center_v = obj.get('center_v', 0)
            format_type = obj.get('format', 'unknown')
            
            table_lines.append(f"|    {i:2d}     |      {center_h:4d}      |     {center_v:4d}     | {format_type:6s} |")
        
        table_lines.append("")  # Empty line after table
        return "\n".join(table_lines)
    
    def _describe_location_from_center(self, center_h: int, center_v: int, 
                                     image_width: int = 640, image_height: int = 480) -> str:
        """Describe location in human-readable terms from center point."""
        # Determine horizontal position
        if center_h < image_width * 0.33:
            h_pos = "left"
        elif center_h > image_width * 0.67:
            h_pos = "right"
        else:
            h_pos = "center"
        
        # Determine vertical position
        if center_v < image_height * 0.33:
            v_pos = "top"
        elif center_v > image_height * 0.67:
            v_pos = "bottom"
        else:
            v_pos = "middle"
        
        # Combine positions
        if h_pos == "center" and v_pos == "middle":
            return "in the center"
        elif h_pos == "center":
            return f"in the {v_pos}"
        elif v_pos == "middle":
            return f"on the {h_pos}"
        else:
            return f"in the {v_pos} {h_pos}"
    
    def _describe_location(self, coords: List[float], image_width: int = 640, image_height: int = 480) -> str:
        """Describe location in human-readable terms."""
        x1, y1, x2, y2 = coords
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Determine horizontal position
        if center_x < image_width * 0.33:
            h_pos = "left"
        elif center_x > image_width * 0.67:
            h_pos = "right"
        else:
            h_pos = "center"
        
        # Determine vertical position
        if center_y < image_height * 0.33:
            v_pos = "top"
        elif center_y > image_height * 0.67:
            v_pos = "bottom"
        else:
            v_pos = "middle"
        
        # Combine positions
        if h_pos == "center" and v_pos == "middle":
            return "in the center"
        elif h_pos == "center":
            return f"in the {v_pos}"
        elif v_pos == "middle":
            return f"on the {h_pos}"
        else:
            return f"in the {v_pos} {h_pos}"
    
    def _generate_provider_info(self, provider: str, objects: List[Dict[str, Any]]) -> str:
        """Generate provider-specific information."""
        provider_descriptions = {
            'grok': "Analyzed using Grok vision AI.",
            'qwen': "Analyzed using Qwen vision model.",
            'llava': "Analyzed using local LLaVA model."
        }
        
        base_info = provider_descriptions.get(provider.lower(), f"Analyzed using {provider}.")
        
        # Add source information if available
        sources = set(obj.get('source', 'unknown') for obj in objects)
        if len(sources) == 1 and 'unknown' not in sources:
            source = list(sources)[0]
            if 'table' in source:
                base_info += " Results parsed from structured table format."
            elif 'bbox' in source:
                base_info += " Results parsed from bounding box format."
            elif 'ratio' in source:
                base_info += " Results converted from ratio coordinates."
        
        return base_info
    
    def generate_detailed_response(self, objects: List[Dict[str, Any]], object_name: str, 
                                  provider: str, image_path: str = "") -> str:
        """Generate detailed response with technical information."""
        if not objects:
            return self._generate_not_found_response(object_name, provider)
        
        response_parts = [
            f"Detection Report for '{object_name}':",
            f"Total found: {len(objects)}",
            f"Provider: {provider}",
        ]
        
        if image_path:
            response_parts.append(f"Image: {image_path}")
        
        response_parts.append("")  # Empty line
        
        # Add details for each detection
        for i, obj in enumerate(objects, 1):
            coords = obj['coordinates']
            confidence = obj.get('confidence', 0.5)
            source = obj.get('source', 'unknown')
            
            location_desc = self._describe_location(coords)
            
            obj_details = [
                f"Detection #{i}:",
                f"  Location: {location_desc}",
                f"  Coordinates: [{coords[0]:.1f}, {coords[1]:.1f}, {coords[2]:.1f}, {coords[3]:.1f}]",
                f"  Confidence: {confidence:.2f}",
                f"  Source: {source}",
                ""
            ]
            response_parts.extend(obj_details)
        
        return "\n".join(response_parts)
    
    def generate_json_response(self, objects: List[Dict[str, Any]], object_name: str, 
                              provider: str, query: str = "") -> Dict[str, Any]:
        """Generate structured JSON response."""
        return {
            'query': query,
            'object_name': object_name,
            'provider': provider,
            'total_found': len(objects),
            'success': len(objects) > 0,
            'objects': objects,
            'summary': self.generate_response(objects, object_name, provider, query),
            'confidence_stats': self._get_confidence_stats(objects) if objects else None
        }
    
    def _get_confidence_stats(self, objects: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get confidence statistics for detections."""
        if not objects:
            return {}
        
        confidences = [obj.get('confidence', 0.5) for obj in objects]
        
        return {
            'average': sum(confidences) / len(confidences),
            'maximum': max(confidences),
            'minimum': min(confidences),
            'count': len(confidences)
        }
    
    def generate_comparison_response(self, results: Dict[str, List[Dict[str, Any]]], 
                                   object_name: str) -> str:
        """Generate response comparing results from multiple providers."""
        provider_counts = {provider: len(objects) for provider, objects in results.items()}
        
        if not any(provider_counts.values()):
            return f"No {object_name} was detected by any provider."
        
        response_parts = [f"Detection comparison for '{object_name}':"]
        
        for provider, count in provider_counts.items():
            if count > 0:
                avg_conf = sum(obj.get('confidence', 0.5) for obj in results[provider]) / count
                response_parts.append(f"  {provider}: {count} found (avg confidence: {avg_conf:.2f})")
            else:
                response_parts.append(f"  {provider}: 0 found")
        
        # Find consensus
        max_count = max(provider_counts.values())
        best_providers = [p for p, c in provider_counts.items() if c == max_count]
        
        if len(best_providers) == 1:
            response_parts.append(f"\nBest result: {best_providers[0]} with {max_count} detections.")
        else:
            response_parts.append(f"\nTie between: {', '.join(best_providers)} with {max_count} detections each.")
        
        return "\n".join(response_parts)
