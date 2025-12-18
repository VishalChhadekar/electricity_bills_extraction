"""
Google Cloud Vision OCR module.
Extracts text from preprocessed bill images using Google Cloud Vision API.
"""

import os
from google.cloud import vision
import cv2


def perform_ocr(image) -> str:
    """
    Perform OCR on image using Google Cloud Vision API.
    
    Business Logic:
    - Google Vision handles multilingual text (English + regional languages)
    - Returns full text with layout preserved via newlines
    - Requires GOOGLE_APPLICATION_CREDENTIALS environment variable
    
    Args:
        image: Preprocessed image as numpy array
        
    Returns:
        Extracted text as string
        
    Raises:
        Exception: If Google Cloud credentials are not configured
    """
    # Verify credentials are set
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        raise Exception(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
            "Please set it to the path of your service account JSON file."
        )
    
    # Initialize Vision API client
    client = vision.ImageAnnotatorClient()
    
    # Convert numpy array to bytes for API
    # Encode as PNG to preserve quality
    success, encoded_image = cv2.imencode('.png', image)
    if not success:
        raise Exception("Failed to encode image")
    
    image_bytes = encoded_image.tobytes()
    
    # Create Vision API image object
    vision_image = vision.Image(content=image_bytes)
    
    # Perform text detection
    # document_text_detection is optimized for documents (vs general text_detection)
    response = client.document_text_detection(image=vision_image)
    
    # Check for errors
    if response.error.message:
        raise Exception(f"Google Vision API error: {response.error.message}")
    
    # Extract full text from response
    # full_text_annotation preserves layout better than individual text_annotations
    text = response.full_text_annotation.text if response.full_text_annotation else ""
    
    return text


def clean_ocr_text(text: str) -> str:
    """
    Clean and normalize OCR output.
    
    Business Logic:
    - Remove excessive whitespace that confuses extraction
    - Normalize line breaks for consistent parsing
    - Preserve structure needed for field extraction
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text
    """
    # Remove excessive blank lines (more than 2 consecutive)
    lines = text.split('\n')
    cleaned_lines = []
    blank_count = 0
    
    for line in lines:
        if line.strip():
            cleaned_lines.append(line)
            blank_count = 0
        else:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append(line)
    
    # Join and normalize whitespace
    cleaned = '\n'.join(cleaned_lines)
    
    # Replace multiple spaces with single space
    import re
    cleaned = re.sub(r' +', ' ', cleaned)
    
    return cleaned.strip()
