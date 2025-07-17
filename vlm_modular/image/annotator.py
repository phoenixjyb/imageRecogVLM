"""Image annotation utilities for marking detected objects."""

import logging
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple, Optional

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import VLMSettings

class ImageAnnotator:
    """Handles image annotation with detected object markers."""
    
    def __init__(self, settings: VLMSettings):
        """Initialize image annotator with settings."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Try to load a font
        self.font = self._load_font()
    
    def _load_font(self) -> Optional[ImageFont.FreeTypeFont]:
        """Load a font for text annotations."""
        try:
            # Try to load a system font
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/usr/share/fonts/truetype/arial.ttf",  # Linux
                "C:/Windows/Fonts/arial.ttf"  # Windows
            ]
            
            for font_path in font_paths:
                try:
                    return ImageFont.truetype(font_path, self.settings.annotation_font_size)
                except:
                    continue
            
            # Fallback to default font
            return ImageFont.load_default()
        except Exception as e:
            self.logger.warning(f"Could not load font: {e}")
            return None
    
    def annotate_objects(self, image: Image.Image, objects: List[Dict[str, Any]], 
                        object_name: str = "object") -> Image.Image:
        """Annotate image with detected objects."""
        if not objects:
            self.logger.info("No objects to annotate")
            return image
        
        try:
            # Create a copy of the image for annotation
            annotated_image = image.copy()
            draw = ImageDraw.Draw(annotated_image)
            
            for i, obj in enumerate(objects):
                if 'coordinates' in obj:
                    coords = obj['coordinates']
                    confidence = obj.get('confidence', 0.5)
                    source = obj.get('source', 'unknown')
                    
                    # Draw bounding box
                    self._draw_bounding_box(draw, coords, confidence)
                    
                    # Draw star marker at center
                    self._draw_star_marker(draw, coords)
                    
                    # Draw label
                    self._draw_label(draw, coords, object_name, i + 1, confidence, source)
            
            self.logger.info(f"Annotated {len(objects)} objects on image")
            return annotated_image
            
        except Exception as e:
            self.logger.error(f"Failed to annotate objects: {e}")
            return image
    
    def _draw_bounding_box(self, draw: ImageDraw.Draw, coords: List[float], confidence: float):
        """Draw bounding box around detected object."""
        if len(coords) == 2:
            # Center point coordinates only - draw a circle around the center
            h, v = coords
            radius = 10  # Small radius for center point indication
            
            # Choose color based on confidence
            if confidence >= 0.7:
                color = "green"
            elif confidence >= 0.5:
                color = "yellow"
            else:
                color = "orange"
            
            # Draw circle around center point
            draw.ellipse([h-radius, v-radius, h+radius, v+radius], outline=color, width=3)
            
        elif len(coords) == 4:
            # Bounding box coordinates
            x1, y1, x2, y2 = coords
            
            # Choose color based on confidence
            if confidence >= 0.7:
                color = "green"
            elif confidence >= 0.5:
                color = "yellow"
            else:
                color = "orange"
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
    
    def _draw_star_marker(self, draw: ImageDraw.Draw, coords: List[float]):
        """Draw star marker at the center of detected object."""
        if len(coords) == 2:
            # Center point coordinates
            center_x, center_y = coords
        elif len(coords) == 4:
            # Bounding box coordinates - calculate center
            x1, y1, x2, y2 = coords
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
        else:
            return  # Invalid coordinates
        
        star_size = self.settings.annotation_star_size
        color = self.settings.annotation_text_color
        
        # Draw star shape
        star_points = self._generate_star_points(center_x, center_y, star_size)
        draw.polygon(star_points, fill=color, outline=color)
    
    def _generate_star_points(self, center_x: float, center_y: float, size: int) -> List[Tuple[float, float]]:
        """Generate points for a star shape."""
        import math
        
        points = []
        outer_radius = size
        inner_radius = size * 0.4
        
        for i in range(10):  # 5 points star = 10 vertices
            angle = (i * math.pi) / 5
            if i % 2 == 0:
                # Outer point
                x = center_x + outer_radius * math.cos(angle - math.pi/2)
                y = center_y + outer_radius * math.sin(angle - math.pi/2)
            else:
                # Inner point
                x = center_x + inner_radius * math.cos(angle - math.pi/2)
                y = center_y + inner_radius * math.sin(angle - math.pi/2)
            points.append((x, y))
        
        return points
    
    def _draw_label(self, draw: ImageDraw.Draw, coords: List[float], object_name: str, 
                   instance_num: int, confidence: float, source: str):
        """Draw label with object information."""
        if len(coords) == 2:
            # Center point coordinates
            center_x, center_y = coords
            label_x = center_x - 30  # Offset label to the left of center
            label_y = max(center_y - 50, 10)  # Position above center point
        elif len(coords) == 4:
            # Bounding box coordinates
            x1, y1, x2, y2 = coords
            label_x = x1
            label_y = max(y1 - 30, 10)  # Ensure label is visible
        else:
            return  # Invalid coordinates
        
        # Create label text
        label = f"{object_name} #{instance_num}"
        detail_label = f"conf: {confidence:.2f} ({source})"
        
        # Draw background rectangle for better readability
        if self.font:
            try:
                # Get text dimensions using textbbox
                bbox = draw.textbbox((label_x, label_y), label, font=self.font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # Fallback for older PIL versions
                text_width, text_height = draw.textsize(label, font=self.font)
        else:
            # Estimate size without font
            text_width = len(label) * 8
            text_height = 12
        
        # Draw background rectangle
        bg_coords = [label_x - 2, label_y - 2, label_x + text_width + 2, label_y + text_height + 15]
        draw.rectangle(bg_coords, fill="white", outline="black")
        
        # Draw text
        draw.text((label_x, label_y), label, fill="black", font=self.font)
        draw.text((label_x, label_y + text_height + 2), detail_label, fill="gray", font=self.font)
    
    def create_summary_annotation(self, image: Image.Image, objects: List[Dict[str, Any]], 
                                 object_name: str, total_found: int) -> Image.Image:
        """Add summary annotation to image."""
        try:
            annotated_image = image.copy()
            draw = ImageDraw.Draw(annotated_image)
            
            # Create summary text
            summary_text = f"Found {total_found} {object_name}(s)"
            if objects:
                avg_confidence = sum(obj.get('confidence', 0) for obj in objects) / len(objects)
                summary_text += f" (avg confidence: {avg_confidence:.2f})"
            
            # Position at top of image
            text_x = 10
            text_y = 10
            
            # Draw background
            if self.font:
                try:
                    bbox = draw.textbbox((text_x, text_y), summary_text, font=self.font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except:
                    text_width, text_height = draw.textsize(summary_text, font=self.font)
            else:
                text_width = len(summary_text) * 8
                text_height = 12
            
            bg_coords = [text_x - 5, text_y - 5, text_x + text_width + 5, text_y + text_height + 5]
            draw.rectangle(bg_coords, fill="lightblue", outline="blue")
            
            # Draw summary text
            draw.text((text_x, text_y), summary_text, fill="darkblue", font=self.font)
            
            return annotated_image
            
        except Exception as e:
            self.logger.error(f"Failed to create summary annotation: {e}")
            return image
    
    def highlight_best_detection(self, image: Image.Image, objects: List[Dict[str, Any]]) -> Image.Image:
        """Highlight the detection with highest confidence."""
        if not objects:
            return image
        
        try:
            # Find object with highest confidence
            best_object = max(objects, key=lambda obj: obj.get('confidence', 0))
            
            annotated_image = image.copy()
            draw = ImageDraw.Draw(annotated_image)
            
            coords = best_object['coordinates']
            
            # Draw thick highlight border
            x1, y1, x2, y2 = coords
            for offset in range(5):
                draw.rectangle([x1-offset, y1-offset, x2+offset, y2+offset], 
                             outline="red", width=1)
            
            # Draw "BEST" label
            label_x = x1
            label_y = max(y1 - 40, 10)
            draw.text((label_x, label_y), "BEST MATCH", fill="red", font=self.font)
            
            return annotated_image
            
        except Exception as e:
            self.logger.error(f"Failed to highlight best detection: {e}")
            return image
