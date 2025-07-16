"""Image processing utilities."""

import base64
import logging
import os
import sys
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import VLMSettings

class ImageProcessor:
    """Handles image loading, resizing, and encoding operations."""
    
    def __init__(self, settings: VLMSettings):
        """Initialize image processor with settings."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """Load image from file path."""
        try:
            image = Image.open(image_path)
            self.logger.info(f"Successfully loaded image: {image_path}")
            return image
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {e}")
            return None
    
    def resize_image(self, image: Image.Image, 
                    width: Optional[int] = None, 
                    height: Optional[int] = None) -> Image.Image:
        """Resize image to specified dimensions."""
        if width is None:
            width = self.settings.image_output_width
        if height is None:
            height = self.settings.image_output_height
        
        try:
            # Resize using high-quality resampling
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            self.logger.info(f"Resized image to {width}x{height}")
            return resized_image
        except Exception as e:
            self.logger.error(f"Failed to resize image: {e}")
            return image
    
    def encode_image_to_base64(self, image: Image.Image, format: str = "JPEG") -> str:
        """Encode image to base64 string."""
        try:
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Save to bytes
            buffer = BytesIO()
            image.save(buffer, format=format, quality=95)
            
            # Encode to base64
            image_bytes = buffer.getvalue()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            self.logger.info(f"Encoded image to base64 ({len(base64_string)} characters)")
            return base64_string
        
        except Exception as e:
            self.logger.error(f"Failed to encode image to base64: {e}")
            return ""
    
    def load_and_prepare_image(self, image_path: str) -> Optional[Tuple[Image.Image, str]]:
        """Load image and prepare it for VLM processing."""
        # Load image
        image = self.load_image(image_path)
        if image is None:
            return None
        
        # Resize image
        resized_image = self.resize_image(image)
        
        # Encode to base64
        base64_data = self.encode_image_to_base64(resized_image)
        if not base64_data:
            return None
        
        return resized_image, base64_data
    
    def get_image_dimensions(self, image: Image.Image) -> Tuple[int, int]:
        """Get image width and height."""
        return image.size
    
    def save_image(self, image: Image.Image, output_path: str, format: str = "JPEG") -> bool:
        """Save image to file."""
        try:
            # Convert to RGB if saving as JPEG
            if format.upper() == "JPEG" and image.mode != "RGB":
                image = image.convert("RGB")
            
            image.save(output_path, format=format, quality=95)
            self.logger.info(f"Saved image to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save image to {output_path}: {e}")
            return False
    
    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int] = (128, 128)) -> Image.Image:
        """Create thumbnail of image."""
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            self.logger.info(f"Created thumbnail with size {thumbnail.size}")
            return thumbnail
        except Exception as e:
            self.logger.error(f"Failed to create thumbnail: {e}")
            return image
    
    def validate_image_file(self, image_path: str) -> bool:
        """Validate if file is a valid image."""
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def get_image_info(self, image_path: str) -> dict:
        """Get detailed information about an image file."""
        try:
            with Image.open(image_path) as img:
                return {
                    'filename': image_path,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            self.logger.error(f"Failed to get image info for {image_path}: {e}")
            return {'error': str(e)}
