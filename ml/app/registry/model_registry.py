"""Model registry implementation for loading and managing pluggable models.

Handles model discovery, instantiation, and error isolation during loading.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.registry.config_loader import load_registry_config, RegistryConfig, ModelRegistryEntry
from app.registry.model_interface import ModelInterface, validate_model_interface, ModelValidationError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadedModel:
    """A successfully loaded model with its metadata.
    
    Attributes:
        identifier: Model identifier from config
        instance: Model instance
        entry: Original registry entry
    """
    identifier: str
    instance: ModelInterface
    entry: ModelRegistryEntry


@dataclass(frozen=True)
class ModelLoadError:
    """Record of a failed model load attempt.
    
    Attributes:
        identifier: Model identifier that failed
        error_type: Type of error that occurred
        error_message: Human-readable error description
    """
    identifier: str
    error_type: str
    error_message: str


class ModelRegistry:
    """Registry for managing pluggable ML models.
    
    The registry loads models from configuration and provides access to
    valid models. Invalid models are tracked for debugging but don't block
    other models from loading.
    
    Example:
        registry = ModelRegistry()
        registry.load_from_config()
        
        # Get available models
        models = registry.get_available_models()
        
        # Get specific model
        model = registry.get_model("baseline")
    """
    
    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._models: dict[str, LoadedModel] = {}
        self._errors: list[ModelLoadError] = []
        self._config: RegistryConfig | None = None
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if registry has been initialized."""
        return self._initialized
    
    @property
    def load_errors(self) -> list[ModelLoadError]:
        """Get list of models that failed to load."""
        return self._errors.copy()
    
    def load_from_config(self, config_path: Path | str | None = None) -> None:
        """Load models from registry configuration.
        
        Args:
            config_path: Path to config file. If None, uses default.
            
        Note:
            Invalid models are logged and tracked but don't prevent other
            models from loading.
        """
        logger.info("registry.loading config_path=%s", config_path or "default")
        
        try:
            self._config = load_registry_config(config_path)
        except Exception as e:
            logger.error("registry.config_failed error=%s", e)
            self._config = RegistryConfig(models=[], default_model=None)
        
        # Clear previous state
        self._models = {}
        self._errors = []
        
        # Load each enabled model
        loaded_count = 0
        for entry in self._config.models:
            if not entry.enabled:
                logger.debug("registry.skip_disabled identifier=%s", entry.identifier)
                continue
            
            try:
                loaded = self._load_model(entry)
                self._models[entry.identifier] = loaded
                loaded_count += 1
                logger.info(
                    "registry.loaded identifier=%s name=%s version=%s",
                    entry.identifier, entry.name, entry.version
                )
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                self._errors.append(ModelLoadError(
                    identifier=entry.identifier,
                    error_type=error_type,
                    error_message=error_msg,
                ))
                logger.error(
                    "registry.load_failed identifier=%s error_type=%s error=%s",
                    entry.identifier, error_type, error_msg
                )
        
        self._initialized = True
        
        logger.info(
            "registry.complete loaded=%d errors=%d",
            loaded_count, len(self._errors)
        )
    
    def _load_model(self, entry: ModelRegistryEntry) -> LoadedModel:
        """Load a single model from its registry entry.
        
        Args:
            entry: Model registry entry
            
        Returns:
            LoadedModel instance
            
        Raises:
            ImportError: If module cannot be imported
            AttributeError: If class cannot be found
            ModelValidationError: If class doesn't implement interface
        """
        # Import the module
        try:
            module = importlib.import_module(entry.module_path)
        except ImportError as e:
            raise ImportError(
                f"Failed to import module '{entry.module_path}': {e}"
            ) from e
        
        # Get the class
        try:
            model_class = getattr(module, entry.class_name)
        except AttributeError as e:
            raise AttributeError(
                f"Class '{entry.class_name}' not found in module '{entry.module_path}'"
            ) from e
        
        # Validate interface
        try:
            validate_model_interface(model_class)
        except ModelValidationError as e:
            raise ModelValidationError(
                f"Model '{entry.identifier}' interface validation failed: {e}"
            ) from e
        
        # Instantiate the model
        try:
            instance = model_class()
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate model '{entry.identifier}': {e}"
            ) from e
        
        return LoadedModel(
            identifier=entry.identifier,
            instance=instance,
            entry=entry,
        )
    
    def get_model(self, identifier: str) -> ModelInterface | None:
        """Get a model by its identifier.
        
        Args:
            identifier: Model identifier
            
        Returns:
            Model instance or None if not found
        """
        loaded = self._models.get(identifier)
        return loaded.instance if loaded else None
    
    def has_model(self, identifier: str) -> bool:
        """Check if a model is available.
        
        Args:
            identifier: Model identifier
            
        Returns:
            True if model exists and is loaded
        """
        return identifier in self._models
    
    def get_available_models(self) -> list[dict]:
        """Get list of available models with metadata.
        
        Returns:
            List of model info dictionaries
        """
        return [
            {
                "identifier": loaded.identifier,
                "name": loaded.entry.name,
                "version": loaded.entry.version,
                "description": loaded.entry.description,
            }
            for loaded in self._models.values()
        ]
    
    def get_default_model(self) -> ModelInterface | None:
        """Get the default model as configured.
        
        Returns:
            Default model instance or None if not configured/available
        """
        if self._config is None or self._config.default_model is None:
            return None
        return self.get_model(self._config.default_model)
    
    def get_default_model_identifier(self) -> str | None:
        """Get the default model identifier.
        
        Returns:
            Default model identifier or None
        """
        if self._config is None:
            return None
        return self._config.default_model


# Singleton registry instance
_registry_instance: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get the singleton registry instance.
    
    Returns:
        ModelRegistry singleton
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance


def initialize_registry(config_path: Path | str | None = None) -> ModelRegistry:
    """Initialize the registry from configuration.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Initialized registry
    """
    registry = get_registry()
    registry.load_from_config(config_path)
    return registry
