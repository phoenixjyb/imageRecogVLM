#!/usr/bin/env python3
"""
Image Resizer Script
Reads an image from ~/Downloads/image_000777.jpg, resizes it to 640x480,
and saves it as image_000777_rsz.jpg in the same folder.
"""

import os
from PIL import Image

def resize_image():
    """
    Resize image to 640x480 and save with 'rsz' suffix.
    """
    # Define file paths
    input_path = os.path.expanduser("~/Downloads/image_000777.jpg")
    
    # Extract directory, filename (without extension), and extension
    directory = os.path.dirname(input_path)
    filename_without_ext = os.path.splitext(os.path.basename(input_path))[0]
    extension = os.path.splitext(input_path)[1]
    
    # Create output filename with 'rsz' suffix
    output_filename = f"{filename_without_ext}_rsz{extension}"
    output_path = os.path.join(directory, output_filename)
    
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"❌ Error: Input file not found: {input_path}")
            return
        
        print(f"📸 Loading image: {input_path}")
        
        # Open and resize image
        with Image.open(input_path) as img:
            original_size = img.size
            print(f"   Original size: {original_size[0]}x{original_size[1]}")
            
            # Resize to 640x480 (this will change aspect ratio if original doesn't match)
            resized_img = img.resize((640, 480), Image.Resampling.LANCZOS)
            print(f"   Resized to: 640x480")
            
            # Save the resized image
            resized_img.save(output_path, quality=95)
            print(f"✅ Resized image saved: {output_path}")
            
    except FileNotFoundError:
        print(f"❌ Error: File not found: {input_path}")
    except Exception as e:
        print(f"❌ Error processing image: {e}")

if __name__ == "__main__":
    resize_image()