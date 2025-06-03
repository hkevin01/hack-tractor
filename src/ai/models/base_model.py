"""Base model class for all AI models in the Hack Tractor project."""

import os
import json
from abc import ABC, abstractmethod
import numpy as np
import logging

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """Abstract base class for all models in the Hack Tractor project."""
    
    def __init__(self, name, version="0.1.0"):
        """Initialize the base model.
        
        Args:
            name (str): Name of the model
            version (str): Version of the model
        """
        self.name = name
        self.version = version
        self.model = None
        self.metadata = {
            "name": name,
            "version": version,
            "created_at": None,
            "updated_at": None,
            "metrics": {}
        }
        logger.info(f"Initialized {name} model (v{version})")
    
    @abstractmethod
    def train(self, X, y, **kwargs):
        """Train the model.
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training parameters
        """
        pass
    
    @abstractmethod
    def predict(self, X, **kwargs):
        """Make predictions with the model.
        
        Args:
            X: Input features
            **kwargs: Additional prediction parameters
            
        Returns:
            Predictions from the model
        """
        pass
    
    @abstractmethod
    def save(self, path):
        """Save the model to disk.
        
        Args:
            path (str): Path to save the model
        """
        pass
    
    @abstractmethod
    def load(self, path):
        """Load the model from disk.
        
        Args:
            path (str): Path to load the model from
        """
        pass
    
    def save_metadata(self, path):
        """Save model metadata to disk.
        
        Args:
            path (str): Path to save the metadata
        """
        metadata_path = os.path.join(path, f"{self.name}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
