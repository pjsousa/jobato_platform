"""Registry configuration loader for model discovery.

Loads model registry from YAML configuration and validates the schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModelRegistryEntry:
    """Configuration entry for a single model.
    
    Attributes:
        identifier: Unique model identifier (e.g., "baseline", "rf-v1")
        module_path: Python module path (e.g., "app.models.baseline")
        class_name: Class name within the module
        version: Model version string
        name: Human-readable name
        description: Optional description
        enabled: Whether this model is enabled
    """
    identifier: str
    module_path: str
    class_name: str
    version: str
    name: str
    description: str
    enabled: bool


@dataclass(frozen=True)
class RegistryConfig:
    """Complete registry configuration.
    
    Attributes:
        models: List of model entries
        default_model: Identifier of the default/fallback model
    """
    models: list[ModelRegistryEntry]
    default_model: str | None


class RegistryConfigError(Exception):
    """Raised when registry configuration is invalid."""
    pass


def load_registry_config(config_path: Path | str | None = None) -> RegistryConfig:
    """Load and validate the model registry configuration.
    
    Args:
        config_path: Path to the YAML config file. If None, uses default location.
        
    Returns:
        Parsed RegistryConfig
        
    Raises:
        RegistryConfigError: If config file is missing or invalid
    """
    if config_path is None:
        config_path = Path("config/ml/models.yaml")
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        # Return empty config if file doesn't exist (fallback mode)
        return RegistryConfig(models=[], default_model=None)
    
    try:
        content = config_path.read_text(encoding="utf-8")
        if not content.strip():
            return RegistryConfig(models=[], default_model=None)
        
        data = yaml.safe_load(content)
        if data is None:
            return RegistryConfig(models=[], default_model=None)
        
        return _parse_config(data)
        
    except yaml.YAMLError as e:
        raise RegistryConfigError(f"Invalid YAML in {config_path}: {e}")
    except Exception as e:
        raise RegistryConfigError(f"Failed to load registry config: {e}")


def _parse_config(data: dict[str, Any]) -> RegistryConfig:
    """Parse the YAML data into RegistryConfig.
    
    Args:
        data: Parsed YAML dictionary
        
    Returns:
        RegistryConfig
        
    Raises:
        RegistryConfigError: If config structure is invalid
    """
    if not isinstance(data, dict):
        raise RegistryConfigError("Registry config must be a mapping")
    
    default_model = data.get("default_model")
    if default_model is not None and not isinstance(default_model, str):
        raise RegistryConfigError("default_model must be a string")
    
    models_data = data.get("models", [])
    if not isinstance(models_data, list):
        raise RegistryConfigError("models must be a list")
    
    models: list[ModelRegistryEntry] = []
    seen_identifiers: set[str] = set()
    
    for idx, model_data in enumerate(models_data):
        if not isinstance(model_data, dict):
            raise RegistryConfigError(f"Model entry at index {idx} must be a mapping")
        
        try:
            entry = _parse_model_entry(model_data)
            
            if entry.identifier in seen_identifiers:
                raise RegistryConfigError(
                    f"Duplicate model identifier: {entry.identifier}"
                )
            seen_identifiers.add(entry.identifier)
            
            models.append(entry)
            
        except RegistryConfigError as e:
            raise RegistryConfigError(f"Invalid model at index {idx}: {e}")
    
    # Validate default_model exists if specified
    if default_model is not None:
        enabled_identifiers = {m.identifier for m in models if m.enabled}
        if default_model not in enabled_identifiers:
            raise RegistryConfigError(
                f"default_model '{default_model}' not found in enabled models"
            )
    
    return RegistryConfig(models=models, default_model=default_model)


def _parse_model_entry(data: dict[str, Any]) -> ModelRegistryEntry:
    """Parse a single model entry from config.
    
    Args:
        data: Model entry dictionary
        
    Returns:
        ModelRegistryEntry
        
    Raises:
        RegistryConfigError: If entry is invalid
    """
    identifier = data.get("identifier")
    if not identifier or not isinstance(identifier, str):
        raise RegistryConfigError("identifier is required and must be a string")
    
    module_path = data.get("module_path")
    if not module_path or not isinstance(module_path, str):
        raise RegistryConfigError("module_path is required and must be a string")
    
    class_name = data.get("class_name")
    if not class_name or not isinstance(class_name, str):
        raise RegistryConfigError("class_name is required and must be a string")
    
    version = data.get("version", "unknown")
    if not isinstance(version, str):
        raise RegistryConfigError("version must be a string")
    
    name = data.get("name", identifier)
    if not isinstance(name, str):
        raise RegistryConfigError("name must be a string")
    
    description = data.get("description", "")
    if not isinstance(description, str):
        raise RegistryConfigError("description must be a string")
    
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise RegistryConfigError("enabled must be a boolean")
    
    return ModelRegistryEntry(
        identifier=identifier,
        module_path=module_path,
        class_name=class_name,
        version=version,
        name=name,
        description=description,
        enabled=enabled,
    )
