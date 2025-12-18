"""
File loading utilities for handling PDF and image inputs.
Converts PDFs to images and loads image files.
"""

import os
from typing import List
from pdf2image import convert_from_path
from PIL import Image
import numpy as np


def load_file(file_path: str) -> List[np.ndarray]:
    """
    Load a file (PDF or image) and return a list of images as numpy arrays.
    
    Business Logic:
    - PDFs may have multiple pages, each converted to an image
    - Images are returned as-is in a single-element list
    - All outputs are normalized to numpy arrays for consistent processing
    
    Args:
        file_path: Path to the input file (PDF or image)
        
    Returns:
        List of images as numpy arrays (one per page for PDFs)
        
    Raises:
        ValueError: If file format is unsupported
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Handle PDF files - convert each page to image
    if file_ext == '.pdf':
        images = convert_from_path(file_path)
        # Convert PIL images to numpy arrays
        return [np.array(img) for img in images]
    
    # Handle image files (jpg, jpeg, png)
    elif file_ext in ['.jpg', '.jpeg', '.png']:
        img = Image.open(file_path)
        return [np.array(img)]
    
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def save_json(data: dict, output_path: str) -> None:
    """
    Save dictionary as JSON file.
    
    Args:
        data: Dictionary to save
        output_path: Path where JSON will be saved
    """
    import json
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(file_path: str) -> dict:
    """
    Load JSON file as dictionary.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary from JSON file
    """
    import json
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
