"""Heuristic baseline and optional learned estimator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from echomind.pipeline.schemas import UncertaintyFeatures


@dataclass
class Score:
    raw: float
    reasons: list[str]


class HeuristicUncertaintyEstimator:
    """Interpretable risk score; it is deliberately not called a probability."""

    def __init__(self, medium: float = 0.20, high: float = 0.30) -> None:
        self.medium = medium
        self.high = high

    def score(self, features: UncertaintyFeatures) -> Score:
        value = 0.10
        reasons: list[str] = []
        if features.avg_logprob is not None and features.avg_logprob < -1.0:
            value += 0.25
            reasons.append("low decoder log probability")
        if features.mean_word_probability is not None:
            if features.mean_word_probability < 0.55:
                value += 0.18
                reasons.append("low mean word probability")
            elif features.mean_word_probability < 0.75:
                value += 0.10
                reasons.append("reduced mean word probability")
        if features.low_word_probability_ratio > 0.35:
            value += 0.15
            reasons.append("many low-confidence words")
        if features.no_speech_prob is not None and features.no_speech_prob > 0.45:
            value += 0.18
            reasons.append("elevated no-speech probability")
        if features.compression_ratio is not None and features.compression_ratio > 2.4:
            value += 0.12
            reasons.append("unusual compression ratio")
        if features.clipping_ratio > 0.01:
            value += 0.18
            reasons.append("possible clipping")
        if features.silence_proximity > 0.75:
            value += 0.12
            reasons.append("speech is near mostly-silent audio")
        if features.text_instability:
            value += features.text_instability * 0.20
            reasons.append("text instability heuristic")
        if features.language_switch:
            value += 0.10
            reasons.append("possible language transition")
        if features.semantic_inconsistency:
            value += features.semantic_inconsistency
            reasons.append("context mismatch heuristic")
        return Score(raw=float(min(1.0, value)), reasons=reasons)


class LearnedUncertaintyEstimator:
    """Optional sklearn logistic regression wrapper with explicit fit/validation separation."""

    def __init__(self) -> None:
        self._model = None
        self.feature_names = [
            "duration", "rms", "clipping_ratio", "silence_proximity", "avg_logprob",
            "mean_word_probability", "low_word_probability_ratio",
            "no_speech_prob", "compression_ratio", "text_instability", "language_switch",
            "semantic_inconsistency",
        ]

    def fit(self, features: list[UncertaintyFeatures], labels: list[int]) -> None:
        from sklearn.linear_model import LogisticRegression

        x = np.nan_to_num(np.asarray([self._vector(item) for item in features], dtype=float))
        self._model = LogisticRegression(max_iter=500, class_weight="balanced").fit(x, labels)

    def predict_probability(self, features: UncertaintyFeatures) -> float:
        if self._model is None:
            raise RuntimeError("Learned estimator has not been fitted")
        return float(self._model.predict_proba([self._vector(features)])[0, 1])

    def _vector(self, item: UncertaintyFeatures) -> list[float]:
        return [
            item.duration, item.rms, item.clipping_ratio, item.silence_proximity,
            item.avg_logprob if item.avg_logprob is not None else 0.0,
            item.mean_word_probability if item.mean_word_probability is not None else 0.0,
            item.low_word_probability_ratio,
            item.no_speech_prob if item.no_speech_prob is not None else 0.0,
            item.compression_ratio if item.compression_ratio is not None else 0.0,
            item.text_instability, item.language_switch, item.semantic_inconsistency,
        ]
