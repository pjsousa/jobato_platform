from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ClassificationCounts:
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int


def calculate_classification_counts(y_true: Iterable[int], y_pred: Iterable[int]) -> ClassificationCounts:
    true_values = [int(value) for value in y_true]
    pred_values = [int(value) for value in y_pred]
    if len(true_values) != len(pred_values):
        raise ValueError("y_true and y_pred must have equal length")

    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for actual, predicted in zip(true_values, pred_values, strict=True):
        if actual not in (0, 1) or predicted not in (0, 1):
            raise ValueError("classification inputs must be binary values 0 or 1")
        if actual == 1 and predicted == 1:
            tp += 1
        elif actual == 0 and predicted == 0:
            tn += 1
        elif actual == 0 and predicted == 1:
            fp += 1
        else:
            fn += 1

    return ClassificationCounts(
        true_positive=tp,
        true_negative=tn,
        false_positive=fp,
        false_negative=fn,
    )


def calculate_metrics(y_true: Iterable[int], y_pred: Iterable[int]) -> dict[str, float]:
    counts = calculate_classification_counts(y_true, y_pred)
    total = counts.true_positive + counts.true_negative + counts.false_positive + counts.false_negative
    precision_denominator = counts.true_positive + counts.false_positive
    recall_denominator = counts.true_positive + counts.false_negative

    precision = counts.true_positive / precision_denominator if precision_denominator else 0.0
    recall = counts.true_positive / recall_denominator if recall_denominator else 0.0
    f1_denominator = precision + recall
    f1 = (2 * precision * recall / f1_denominator) if f1_denominator else 0.0
    accuracy = (counts.true_positive + counts.true_negative) / total if total else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }
