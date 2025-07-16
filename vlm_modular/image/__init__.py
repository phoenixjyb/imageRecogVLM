"""Image processing package for VLM system."""

from .processor import ImageProcessor
from .annotator import ImageAnnotator
from .coordinate_parser import CoordinateParser

__all__ = ['ImageProcessor', 'ImageAnnotator', 'CoordinateParser']
