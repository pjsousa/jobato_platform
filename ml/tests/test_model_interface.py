"""Tests for model interface contract."""

from __future__ import annotations

import pytest

from app.registry.model_interface import (
    ModelInterface,
    ModelValidationError,
    is_model_instance,
    validate_model_interface,
)


class _FakeMatrix:
    def __init__(self, rows: int) -> None:
        self.shape = (rows, 1)


class ValidModel(ModelInterface):
    def fit(self, X, y):
        return self

    def predict(self, X):
        size = X.shape[0] if hasattr(X, "shape") else len(X)
        return [0.0 for _ in range(size)]


class MissingFitMethod:
    def predict(self, X):
        return [0.0]


class MissingPredictMethod:
    def fit(self, X, y):
        return self


class TestModelInterface:
    def test_valid_model_implements_fit_and_predict(self):
        model = ValidModel()
        assert callable(model.fit)
        assert callable(model.predict)

    def test_fit_returns_self(self):
        model = ValidModel()
        result = model.fit(_FakeMatrix(3), [1, 0, 1])
        assert result is model

    def test_predict_returns_one_score_per_row(self):
        model = ValidModel()
        predictions = model.predict(_FakeMatrix(3))
        assert len(predictions) == 3
        assert all(-1.0 <= value <= 1.0 for value in predictions)


class TestValidateModelInterface:
    def test_valid_model_passes_validation(self):
        validate_model_interface(ValidModel)

    def test_missing_fit_method_fails(self):
        with pytest.raises(ModelValidationError) as exc_info:
            validate_model_interface(MissingFitMethod)
        assert "fit" in str(exc_info.value)

    def test_missing_predict_method_fails(self):
        with pytest.raises(ModelValidationError) as exc_info:
            validate_model_interface(MissingPredictMethod)
        assert "predict" in str(exc_info.value)


class TestIsModelInstance:
    def test_model_interface_instance_returns_true(self):
        assert is_model_instance(ValidModel()) is True

    def test_non_model_instance_returns_false(self):
        assert is_model_instance("string") is False


class TestModelInterfaceAbstract:
    def test_cannot_instantiate_abstract_interface(self):
        with pytest.raises(TypeError):
            ModelInterface()

    def test_subclass_must_implement_predict(self):
        class PartialImplementation(ModelInterface):
            def fit(self, X, y):
                return self

        with pytest.raises(TypeError):
            PartialImplementation()
