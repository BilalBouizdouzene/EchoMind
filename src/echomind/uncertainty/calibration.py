"""Calibration helpers that keep raw risk and calibrated probability distinct."""

from __future__ import annotations

import numpy as np


def expected_calibration_error(probabilities: list[float], labels: list[int], bins: int = 10) -> float:
    if not probabilities:
        return 0.0
    probs = np.asarray(probabilities, dtype=float)
    y = np.asarray(labels, dtype=float)
    total = len(probs)
    error = 0.0
    for left, right in zip(np.linspace(0, 1, bins, endpoint=False), np.linspace(0, 1, bins + 1)[1:]):
        mask = (probs >= left) & (probs < right if right < 1 else probs <= right)
        if np.any(mask):
            error += float(np.sum(mask) / total) * abs(float(np.mean(probs[mask])) - float(np.mean(y[mask])))
    return error


def brier_score(probabilities: list[float], labels: list[int]) -> float:
    if not probabilities:
        return 0.0
    probs = np.asarray(probabilities, dtype=float)
    y = np.asarray(labels, dtype=float)
    return float(np.mean((probs - y) ** 2))


class PlattCalibrator:
    """Small optional calibrator; fit only on a validation split."""

    def __init__(self) -> None:
        self._model = None

    def fit(self, raw_scores: list[float], labels: list[int]) -> None:
        from sklearn.linear_model import LogisticRegression

        self._model = LogisticRegression().fit(np.asarray(raw_scores).reshape(-1, 1), labels)

    def predict(self, raw_score: float) -> float:
        if self._model is None:
            raise RuntimeError("Calibrator has not been fitted")
        return float(self._model.predict_proba([[raw_score]])[0, 1])
