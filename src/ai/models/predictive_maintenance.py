"""
Predictive maintenance model for agricultural equipment.
Uses TensorFlow to predict when maintenance will be needed based on sensor data.
"""

import tensorflow as tf
from tensorflow import keras
import numpy as np
import pandas as pd
import os
import logging
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

class PredictiveMaintenanceModel:
    """TensorFlow model for predicting equipment maintenance needs."""
    
    def __init__(self, config=None):
        """
        Initialize the predictive maintenance model.
        
        Args:
            config (dict, optional): Configuration parameters
        """
        self.config = config or {
            'input_features': 10,
            'hidden_layers': [64, 32, 16],
            'dropout_rate': 0.2,
            'learning_rate': 0.001
        }
        self.model = None
        self.scaler = StandardScaler()
        self.history = None
        self.initialized = False
        logger.info("Initialized PredictiveMaintenanceModel")
    
    def build_model(self):
        """Build the TensorFlow model architecture."""
        input_dim = self.config['input_features']
        hidden_layers = self.config['hidden_layers']
        dropout_rate = self.config['dropout_rate']
        
        model = keras.Sequential()
        
        # Input layer
        model.add(keras.layers.Input(shape=(input_dim,)))
        
        # Hidden layers
        for units in hidden_layers:
            model.add(keras.layers.Dense(units, activation='relu'))
            model.add(keras.layers.Dropout(dropout_rate))
        
        # Output layer (probability of maintenance needed)
        model.add(keras.layers.Dense(1, activation='sigmoid'))
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC()]
        )
        
        self.model = model
        self.initialized = True
        logger.info(f"Built model with architecture: {hidden_layers}")
        return model
    
    def preprocess_data(self, X, y=None, training=False):
        """
        Preprocess the input data.
        
        Args:
            X (pd.DataFrame or np.ndarray): Input features
            y (pd.Series or np.ndarray, optional): Target values
            training (bool): Whether this is for training (fit scaler) or inference
        
        Returns:
            tuple: Preprocessed (X, y) or just X if y is None
        """
        # Convert to numpy if pandas
        if isinstance(X, pd.DataFrame):
            X = X.values
        if y is not None and isinstance(y, pd.Series):
            y = y.values
        
        # Scale features
        if training:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return (X_scaled, y) if y is not None else X_scaled
    
    def train(self, X, y, validation_split=0.2, epochs=50, batch_size=32):
        """
        Train the model.
        
        Args:
            X (pd.DataFrame or np.ndarray): Training features
            y (pd.Series or np.ndarray): Training targets
            validation_split (float): Fraction of data to use for validation
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
        
        Returns:
            keras.callbacks.History: Training history
        """
        if not self.initialized:
            self.build_model()
        
        # Preprocess data
        X_processed, y_processed = self.preprocess_data(X, y, training=True)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, y_processed, test_size=validation_split, random_state=42
        )
        
        # Train model
        logger.info(f"Training model on {len(X_train)} samples, validating on {len(X_val)} samples")
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3)
            ]
        )
        
        return self.history
    
    def predict(self, X):
        """
        Make predictions with the model.
        
        Args:
            X (pd.DataFrame or np.ndarray): Input features
        
        Returns:
            np.ndarray: Predicted probabilities
        """
        if not self.initialized or self.model is None:
            raise ValueError("Model not initialized or trained")
        
        # Preprocess data
        X_processed = self.preprocess_data(X)
        
        # Make predictions
        return self.model.predict(X_processed)
    
    def predict_maintenance_need(self, X, threshold=0.5):
        """
        Predict whether maintenance is needed based on a threshold.
        
        Args:
            X (pd.DataFrame or np.ndarray): Input features
            threshold (float): Probability threshold for maintenance need
        
        Returns:
            np.ndarray: Boolean array indicating maintenance need
        """
        predictions = self.predict(X)
        return predictions >= threshold
    
    def save(self, directory):
        """
        Save the model and scaler.
        
        Args:
            directory (str): Directory to save the model
        """
        if not self.initialized or self.model is None:
            raise ValueError("Model not initialized or trained")
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Save model
        model_path = os.path.join(directory, 'maintenance_model')
        self.model.save(model_path)
        
        # Save scaler
        import joblib
        scaler_path = os.path.join(directory, 'scaler.joblib')
        joblib.dump(self.scaler, scaler_path)
        
        # Save metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'history': None if self.history is None else {
                'accuracy': self.history.history.get('accuracy', [])[-1],
                'val_accuracy': self.history.history.get('val_accuracy', [])[-1],
                'loss': self.history.history.get('loss', [])[-1],
                'val_loss': self.history.history.get('val_loss', [])[-1]
            }
        }
        
        import json
        metadata_path = os.path.join(directory, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved model and metadata to {directory}")
    
    def load(self, directory):
        """
        Load the model and scaler.
        
        Args:
            directory (str): Directory to load the model from
        """
        # Load model
        model_path = os.path.join(directory, 'maintenance_model')
        self.model = keras.models.load_model(model_path)
        
        # Load scaler
        import joblib
        scaler_path = os.path.join(directory, 'scaler.joblib')
        self.scaler = joblib.load(scaler_path)
        
        # Load metadata
        import json
        metadata_path = os.path.join(directory, 'metadata.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            self.config = metadata['config']
        
        self.initialized = True
        logger.info(f"Loaded model and metadata from {directory}")
