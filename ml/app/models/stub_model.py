"""Baseline stub model implementation.

This is the default fallback model that assigns a score of 0 to all results.
It serves as both a working example and the baseline when no other models are available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.registry.model_interface import ModelInterface

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


class BaselineModel(ModelInterface):
    """Baseline model that assigns neutral scores (0.0) to all results.
    
    This is the simplest possible model that serves as the default fallback
    when no trained model is available. All results receive a score of 0
    indicating neutral relevance.
    
    Example:
        model = BaselineModel()
        scores = model.predict(X)  # Returns array of zeros
    """
    
    def __init__(self) -> None:
        """Initialize the baseline model."""
        self._version = "1.0.0"
    
    def fit(self, X: "pd.DataFrame | np.ndarray", y: "np.ndarray") -> "BaselineModel":
        """Train the model - no-op for baseline.
        
        The baseline model doesn't learn from data, so this is a no-op.
        
        Args:
            X: Feature matrix (ignored)
            y: Target labels (ignored)
            
        Returns:
            self
        """
        # Baseline model doesn't train - just return self
        return self
    
    def predict(self, X: "pd.DataFrame | np.ndarray") -> list[float]:
        """Predict relevance scores.
        
        Returns an array of zeros with length matching the input.
        
        Args:
            X: Feature matrix (only shape is used)
            
        Returns:
            Array of zeros (n_samples,)
        """
        # Get number of samples from input
        if hasattr(X, 'shape'):
            n_samples = X.shape[0]
        elif hasattr(X, '__len__'):
            n_samples = len(X)
        else:
            n_samples = 1

        # Return neutral scores
        return [0.0] * n_samples
    
    @property
    def version(self) -> str:
        """Return model version."""
        return self._version
    
    @property
    def name(self) -> str:
        """Return human-readable model name."""
        return "Baseline Model"
    
    @property
    def description(self) -> str:
        """Return model description."""
        return "Default fallback model that assigns neutral relevance scores (0.0) to all results."
