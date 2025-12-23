"""
Image processing utilities for thumbnail generation
"""
from PIL import Image
import io
import os
from pathlib import Path
from typing import Tuple, Optional


class ImageProcessor:
    """Handles image resizing and thumbnail generation"""

    # Thumbnail settings optimized for mobile feeds (Instagram-like)
    THUMBNAIL_SIZE = (400, 400)  # Max dimensions
    THUMBNAIL_QUALITY = 70  # JPEG quality (lower = smaller file)
    ORIGINAL_MAX_SIZE = (1200, 1200)  # Max size for original images
    ORIGINAL_QUALITY = 85

    @staticmethod
    def create_thumbnail(image_bytes: bytes) -> bytes:
        """
        Create optimized thumbnail from image bytes
        Target: 30-50 KB for fast loading

        Args:
            image_bytes: Original image bytes

        Returns:
            Thumbnail image bytes (JPEG format)
        """
        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (handles PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize maintaining aspect ratio
        img.thumbnail(ImageProcessor.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        # Save to bytes with optimization
        output = io.BytesIO()
        img.save(
            output,
            format='JPEG',
            quality=ImageProcessor.THUMBNAIL_QUALITY,
            optimize=True,
            progressive=True  # Progressive JPEG for better perceived load time
        )

        return output.getvalue()

    @staticmethod
    def optimize_original(image_bytes: bytes) -> bytes:
        """
        Optimize original image while maintaining good quality
        Target: 100-200 KB

        Args:
            image_bytes: Original image bytes

        Returns:
            Optimized image bytes (JPEG format)
        """
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if too large
        img.thumbnail(ImageProcessor.ORIGINAL_MAX_SIZE, Image.Resampling.LANCZOS)

        # Save with good quality
        output = io.BytesIO()
        img.save(
            output,
            format='JPEG',
            quality=ImageProcessor.ORIGINAL_QUALITY,
            optimize=True,
            progressive=True
        )

        return output.getvalue()

    @staticmethod
    def get_image_info(image_bytes: bytes) -> dict:
        """
        Get information about an image

        Returns:
            Dict with width, height, format, mode, size_kb
        """
        img = Image.open(io.BytesIO(image_bytes))
        return {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
            'size_kb': len(image_bytes) / 1024
        }


def generate_thumbnail_filename(original_filename: str) -> str:
    """
    Generate thumbnail filename from original filename
    Example: "bull_photo.jpg" -> "bull_photo_thumb.jpg"
    """
    path = Path(original_filename)
    return f"{path.stem}_thumb{path.suffix}"


def process_bull_image_upload(
    image_bytes: bytes,
    filename: str
) -> Tuple[bytes, bytes, str, str]:
    """
    Process uploaded bull image: create both optimized original and thumbnail

    Args:
        image_bytes: Original uploaded image bytes
        filename: Original filename

    Returns:
        Tuple of (original_bytes, thumbnail_bytes, original_filename, thumbnail_filename)
    """
    # Generate filenames
    original_filename = filename
    thumbnail_filename = generate_thumbnail_filename(filename)

    # Process images
    processor = ImageProcessor()
    optimized_original = processor.optimize_original(image_bytes)
    thumbnail = processor.create_thumbnail(image_bytes)

    # Log sizes for debugging
    original_kb = len(optimized_original) / 1024
    thumb_kb = len(thumbnail) / 1024
    print(f"Image processing: Original={original_kb:.1f}KB, Thumbnail={thumb_kb:.1f}KB")

    return optimized_original, thumbnail, original_filename, thumbnail_filename
