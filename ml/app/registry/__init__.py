"""Model registry package for pluggable ML models."""

from app.registry.model_interface import ModelInterface, ModelValidationError, validate_model_interface
from app.registry.model_registry import ModelRegistry, initialize_registry, get_registry
from app.registry.config_loader import load_registry_config, ModelRegistryEntry, RegistryConfig

__all__ = [
    "ModelInterface",
    "ModelValidationError",
    "validate_model_interface",
    "ModelRegistry",
    "initialize_registry",
    "get_registry",
    "load_registry_config",
    "ModelRegistryEntry",
    "RegistryConfig",
]