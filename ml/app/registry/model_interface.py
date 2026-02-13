"""Model interface contract for pluggable ML models."""

from __future__ import annotations

import abc
from typing import Any


class ModelInterface(abc.ABC):
    """Abstract base class for all pluggable scoring models.

    The contract follows a scikit-learn style shape: ``fit(X, y)`` and
    ``predict(X)``. Implementations may accept DataFrame-like or array-like
    inputs and must return one score per input row.
    """

    @abc.abstractmethod
    def fit(self, X: Any, y: Any) -> "ModelInterface":
        """Train the model on the provided data and return ``self``."""

    @abc.abstractmethod
    def predict(self, X: Any) -> Any:
        """Predict relevance scores for the provided data."""

    @property
    def version(self) -> str:
        """Return the model version identifier."""
        return "unknown"

    @property
    def name(self) -> str:
        """Return the human-readable model name."""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """Return optional model description."""
        return ""


class ModelValidationError(Exception):
    """Raised when a model fails interface validation."""


def validate_model_interface(model_class: type) -> None:
    """Validate that a class implements required fit/predict methods."""
    required_methods = ["fit", "predict"]
    missing = []

    for method in required_methods:
        method_value = getattr(model_class, method, None)
        if method_value is None:
            missing.append(method)
        elif not callable(method_value):
            missing.append(f"{method} (not callable)")

    if missing:
        raise ModelValidationError(
            f"Model class {model_class.__name__} missing required interface: {', '.join(missing)}"
        )


def is_model_instance(obj: object) -> bool:
    """Check if an object is a valid model instance.
    
    Args:
        obj: Object to check
        
    Returns:
        True if obj implements ModelInterface, False otherwise
    """
    return isinstance(obj, ModelInterface)
