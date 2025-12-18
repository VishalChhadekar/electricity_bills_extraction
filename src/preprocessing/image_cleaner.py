"""
Image preprocessing module for cleaning and enhancing bill images.
Improves OCR accuracy through grayscale conversion, thresholding, denoising, and deskewing.
"""

import cv2
import numpy as np


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image to improve OCR accuracy.
    
    Business Logic:
    - Grayscale conversion reduces complexity and improves text detection
    - Denoising removes artifacts that confuse OCR
    - Adaptive thresholding handles varying lighting conditions in scanned bills
    - Deskewing corrects rotation from scanning/photography
    
    Processing Pipeline:
    1. Convert to grayscale
    2. Denoise using bilateral filter (preserves edges)
    3. Apply adaptive thresholding for binarization
    4. Detect and correct skew
    
    Args:
        image: Input image as numpy array (RGB or grayscale)
        
    Returns:
        Preprocessed image as numpy array
    """
    # Step 1: Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()
    
    # Step 2: Denoise - bilateral filter preserves edges while removing noise
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Step 3: Adaptive thresholding - handles varying lighting across the bill
    # ADAPTIVE_THRESH_GAUSSIAN_C works well for documents
    thresh = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,  # Block size
        2    # Constant subtracted from mean
    )
    
    # Step 4: Deskew - correct rotation
    deskewed = deskew_image(thresh)
    
    return deskewed


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct skew in the image.
    
    Business Logic:
    - Scanned/photographed bills are often slightly rotated
    - Text lines should be horizontal for optimal OCR
    - Uses Hough Line Transform to detect dominant angle
    
    Args:
        image: Binary image (thresholded)
        
    Returns:
        Deskewed image
    """
    # Find all coordinates of non-zero pixels (text)
    coords = np.column_stack(np.where(image > 0))
    
    # If image is mostly empty, return as-is
    if len(coords) < 100:
        return image
    
    # Calculate minimum area rectangle around text
    # This gives us the rotation angle
    angle = cv2.minAreaRect(coords)[-1]
    
    # Normalize angle to [-45, 45] range
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Only correct if skew is significant (> 0.5 degrees)
    if abs(angle) < 0.5:
        return image
    
    # Rotate image to correct skew
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return rotated
