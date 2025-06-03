"""Base image processing utilities for the Hack Tractor project."""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Base class for image processing in the Hack Tractor project."""
    
    def __init__(self, config=None):
        """Initialize the image processor.
        
        Args:
            config (dict, optional): Configuration parameters
        """
        self.config = config or {}
        logger.info("Initialized ImageProcessor")
    
    def preprocess(self, image):
        """Preprocess an image for analysis.
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        # Resize if dimensions are provided
        if 'width' in self.config and 'height' in self.config:
            image = cv2.resize(
                image, 
                (self.config['width'], self.config['height']),
                interpolation=cv2.INTER_AREA
            )
        
        # Convert to grayscale if specified
        if self.config.get('grayscale', False):
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply blur if specified
        if 'blur_kernel' in self.config:
            kernel_size = self.config['blur_kernel']
            image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
            
        return image
    
    def detect_edges(self, image, low_threshold=50, high_threshold=150):
        """Detect edges in an image.
        
        Args:
            image (numpy.ndarray): Input image
            low_threshold (int): Lower threshold for edge detection
            high_threshold (int): Higher threshold for edge detection
            
        Returns:
            numpy.ndarray: Edge image
        """
        return cv2.Canny(image, low_threshold, high_threshold)
    
    def find_contours(self, image):
        """Find contours in an image.
        
        Args:
            image (numpy.ndarray): Input binary image
            
        Returns:
            tuple: (contours, hierarchy)
        """
        contours, hierarchy = cv2.findContours(
            image, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        return contours, hierarchy
