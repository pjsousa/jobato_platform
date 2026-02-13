from app.services.metrics import calculate_classification_counts, calculate_metrics


def test_calculate_metrics_returns_expected_values() -> None:
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 1, 0]

    metrics = calculate_metrics(y_true, y_pred)

    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["accuracy"] == 0.5


def test_zero_denominator_metrics_fall_back_to_zero() -> None:
    y_true = [0, 0, 0]
    y_pred = [0, 0, 0]

    metrics = calculate_metrics(y_true, y_pred)

    assert metrics == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "accuracy": 1.0,
    }


def test_counts_reject_non_binary_values() -> None:
    try:
        calculate_classification_counts([1, 2], [1, 0])
        raised = False
    except ValueError:
        raised = True

    assert raised
