"""Tests for model registry.

Validates registry loading, error isolation, and model discovery.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from app.registry import (
    ModelRegistry,
    initialize_registry,
    get_registry,
    load_registry_config,
    ModelRegistryEntry,
    RegistryConfig,
)
from app.registry.config_loader import RegistryConfigError
from app.registry.model_interface import ModelValidationError


class TestConfigLoader:
    """Tests for registry configuration loading."""

    def test_load_empty_config(self):
        """AC2: Empty config returns empty registry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            config_path = f.name
        
        try:
            config = load_registry_config(config_path)
            assert config.models == []
            assert config.default_model is None
        finally:
            os.unlink(config_path)

    def test_load_valid_config(self):
        """AC2: Valid config loads all models."""
        config_data = {
            'default_model': 'test-model',
            'models': [
                {
                    'identifier': 'test-model',
                    'module_path': 'app.models.test',
                    'class_name': 'TestModel',
                    'version': '1.0.0',
                    'name': 'Test Model',
                    'description': 'A test model',
                    'enabled': True,
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_registry_config(config_path)
            assert len(config.models) == 1
            assert config.default_model == 'test-model'
            
            model = config.models[0]
            assert model.identifier == 'test-model'
            assert model.module_path == 'app.models.test'
            assert model.class_name == 'TestModel'
            assert model.version == '1.0.0'
            assert model.name == 'Test Model'
            assert model.description == 'A test model'
            assert model.enabled is True
        finally:
            os.unlink(config_path)

    def test_missing_config_returns_empty(self):
        """Missing config file returns empty config."""
        config = load_registry_config('/nonexistent/path/models.yaml')
        assert config.models == []
        assert config.default_model is None

    def test_disabled_models_not_loaded(self):
        """Disabled models are still parsed but flagged."""
        config_data = {
            'models': [
                {
                    'identifier': 'enabled-model',
                    'module_path': 'app.models.enabled',
                    'class_name': 'EnabledModel',
                    'version': '1.0',
                    'name': 'Enabled',
                    'enabled': True,
                },
                {
                    'identifier': 'disabled-model',
                    'module_path': 'app.models.disabled',
                    'class_name': 'DisabledModel',
                    'version': '1.0',
                    'name': 'Disabled',
                    'enabled': False,
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_registry_config(config_path)
            assert len(config.models) == 2
            assert config.models[0].enabled is True
            assert config.models[1].enabled is False
        finally:
            os.unlink(config_path)

    def test_duplicate_identifiers_raise_error(self):
        """Duplicate model identifiers raise config error."""
        config_data = {
            'models': [
                {
                    'identifier': 'duplicate',
                    'module_path': 'app.models.a',
                    'class_name': 'ModelA',
                    'version': '1.0',
                    'name': 'Model A',
                },
                {
                    'identifier': 'duplicate',
                    'module_path': 'app.models.b',
                    'class_name': 'ModelB',
                    'version': '1.0',
                    'name': 'Model B',
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            with pytest.raises(RegistryConfigError) as exc_info:
                load_registry_config(config_path)
            assert "Duplicate" in str(exc_info.value) or "duplicate" in str(exc_info.value)
        finally:
            os.unlink(config_path)

    def test_invalid_default_model_raises_error(self):
        """Invalid default_model raises config error."""
        config_data = {
            'default_model': 'nonexistent',
            'models': [
                {
                    'identifier': 'exists',
                    'module_path': 'app.models.exists',
                    'class_name': 'ExistsModel',
                    'version': '1.0',
                    'name': 'Exists',
                    'enabled': True,
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            with pytest.raises(RegistryConfigError) as exc_info:
                load_registry_config(config_path)
            assert "default_model" in str(exc_info.value)
        finally:
            os.unlink(config_path)


class TestModelRegistry:
    """Tests for ModelRegistry."""

    def test_registry_initializes_empty(self):
        """New registry starts empty and uninitialized."""
        registry = ModelRegistry()
        
        assert not registry.is_initialized
        assert registry.get_available_models() == []
        assert registry.load_errors == []
        assert registry.get_default_model() is None

    def test_registry_loads_baseline_model(self, tmp_path):
        """AC1, AC2: Registry loads baseline model from config."""
        # Create config with baseline model
        config_data = {
            'default_model': 'baseline',
            'models': [
                {
                    'identifier': 'baseline',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0.0',
                    'name': 'Baseline Model',
                    'description': 'Default fallback',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert registry.is_initialized
        assert registry.has_model('baseline')
        assert len(registry.get_available_models()) == 1
        
        model_info = registry.get_available_models()[0]
        assert model_info['identifier'] == 'baseline'
        assert model_info['name'] == 'Baseline Model'

    def test_registry_returns_model_instance(self, tmp_path):
        """AC1: get_model returns model instance."""
        config_data = {
            'models': [
                {
                    'identifier': 'baseline',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Baseline',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        model = registry.get_model('baseline')
        assert model is not None
        
        # Verify it has the interface
        assert hasattr(model, 'fit')
        assert hasattr(model, 'predict')
        assert hasattr(model, 'version')
        assert hasattr(model, 'name')

    def test_registry_returns_none_for_missing_model(self, tmp_path):
        """get_model returns None for non-existent model."""
        config_data = {'models': []}
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert registry.get_model('nonexistent') is None

    def test_has_model_returns_false_for_missing(self, tmp_path):
        """has_model returns False for non-existent model."""
        config_data = {'models': []}
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert not registry.has_model('nonexistent')

    def test_disabled_models_not_loaded(self, tmp_path):
        """AC3: Disabled models are not loaded."""
        config_data = {
            'models': [
                {
                    'identifier': 'enabled',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Enabled',
                    'enabled': True,
                },
                {
                    'identifier': 'disabled',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Disabled',
                    'enabled': False,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert registry.has_model('enabled')
        assert not registry.has_model('disabled')
        assert len(registry.get_available_models()) == 1


class TestRegistryErrorIsolation:
    """Tests that invalid models don't block valid ones (AC3)."""

    def test_invalid_module_does_not_block_valid(self, tmp_path):
        """AC3: Invalid module doesn't block valid models."""
        config_data = {
            'models': [
                {
                    'identifier': 'valid',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Valid',
                    'enabled': True,
                },
                {
                    'identifier': 'invalid',
                    'module_path': 'nonexistent.module',
                    'class_name': 'NonExistentModel',
                    'version': '1.0',
                    'name': 'Invalid',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        # Valid model should still be loaded
        assert registry.has_model('valid')
        assert not registry.has_model('invalid')
        
        # Error should be recorded
        assert len(registry.load_errors) == 1
        assert registry.load_errors[0].identifier == 'invalid'

    def test_invalid_class_does_not_block_valid(self, tmp_path):
        """AC3: Missing class doesn't block valid models."""
        config_data = {
            'models': [
                {
                    'identifier': 'valid',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Valid',
                    'enabled': True,
                },
                {
                    'identifier': 'bad-class',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'NonExistentClass',
                    'version': '1.0',
                    'name': 'Bad Class',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert registry.has_model('valid')
        assert not registry.has_model('bad-class')
        assert len(registry.load_errors) == 1
        assert registry.load_errors[0].identifier == 'bad-class'

    def test_invalid_interface_does_not_block_valid(self, tmp_path):
        """AC3: Class without proper interface doesn't block valid models."""
        # Create a module with invalid model (missing methods)
        invalid_module = tmp_path / "invalid_model.py"
        invalid_module.write_text("""
class InvalidModel:
    # Missing fit and predict
    @property
    def version(self):
        return "1.0"
    
    @property
    def name(self):
        return "Invalid"
""")
        
        config_data = {
            'models': [
                {
                    'identifier': 'valid',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Valid',
                    'enabled': True,
                },
                {
                    'identifier': 'bad-interface',
                    'module_path': 'invalid_model',
                    'class_name': 'InvalidModel',
                    'version': '1.0',
                    'name': 'Bad Interface',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Add tmp_path to Python path so we can import
        import sys
        sys.path.insert(0, str(tmp_path))
        
        try:
            registry = ModelRegistry()
            registry.load_from_config(config_path)
            
            assert registry.has_model('valid')
            assert not registry.has_model('bad-interface')
            assert len(registry.load_errors) == 1
            assert registry.load_errors[0].identifier == 'bad-interface'
        finally:
            sys.path.pop(0)

    def test_multiple_errors_tracked(self, tmp_path):
        """AC3: Multiple invalid models are all tracked."""
        config_data = {
            'models': [
                {
                    'identifier': 'bad-1',
                    'module_path': 'nonexistent.one',
                    'class_name': 'Model1',
                    'version': '1.0',
                    'name': 'Bad 1',
                    'enabled': True,
                },
                {
                    'identifier': 'bad-2',
                    'module_path': 'nonexistent.two',
                    'class_name': 'Model2',
                    'version': '1.0',
                    'name': 'Bad 2',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert len(registry.load_errors) == 2
        error_ids = {e.identifier for e in registry.load_errors}
        assert error_ids == {'bad-1', 'bad-2'}


class TestDefaultModel:
    """Tests for default model handling."""

    def test_default_model_returned(self, tmp_path):
        """get_default_model returns the configured default."""
        config_data = {
            'default_model': 'baseline',
            'models': [
                {
                    'identifier': 'baseline',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Baseline',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        default = registry.get_default_model()
        assert default is not None
        assert default.name == "Baseline Model"

    def test_no_default_returns_none(self, tmp_path):
        """No default configured returns None."""
        config_data = {
            'models': [
                {
                    'identifier': 'only',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Only',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry = ModelRegistry()
        registry.load_from_config(config_path)
        
        assert registry.get_default_model() is None
        assert registry.get_default_model_identifier() is None


class TestSingletonRegistry:
    """Tests for singleton registry instance."""

    def test_get_registry_returns_same_instance(self):
        """get_registry returns singleton instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        
        assert reg1 is reg2

    def test_initialize_registry_loads_config(self, tmp_path):
        """initialize_registry loads config and returns registry."""
        config_data = {
            'models': [
                {
                    'identifier': 'test',
                    'module_path': 'app.models.stub_model',
                    'class_name': 'BaselineModel',
                    'version': '1.0',
                    'name': 'Test',
                    'enabled': True,
                }
            ]
        }
        
        config_path = tmp_path / "models.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Reset singleton for test
        import app.registry.model_registry as registry_module
        registry_module._registry_instance = None
        
        registry = initialize_registry(config_path)
        
        assert registry.is_initialized
        assert registry.has_model('test')
