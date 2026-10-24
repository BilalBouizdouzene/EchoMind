"""Reference-based metrics with no fabricated defaults."""

from __future__ import annotations

import re
from collections.abc import Iterable

from echomind.evaluation.text_normalization import (
    NORMALIZATION_MODE,
    normalize_for_evaluation,
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, ref in enumerate(reference, 1):
        current = [i]
        for j, hyp in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (ref != hyp)))
        previous = current
    return previous[-1]


def wer(reference: str, hypothesis: str) -> float:
    ref, hyp = _tokens(reference), _tokens(hypothesis)
    return _edit_distance(ref, hyp) / max(1, len(ref))


def cer(reference: str, hypothesis: str) -> float:
    ref, hyp = list((reference or "").lower()), list((hypothesis or "").lower())
    return _edit_distance(ref, hyp) / max(1, len(ref))


def corpus_wer(references: Iterable[str], hypotheses: Iterable[str]) -> float:
    """Micro-average word errors over all utterances in a corpus."""
    pairs = list(zip(references, hypotheses))
    errors = sum(_edit_distance(_tokens(reference), _tokens(hypothesis)) for reference, hypothesis in pairs)
    words = sum(len(_tokens(reference)) for reference, _ in pairs)
    return errors / max(1, words)


def corpus_cer(references: Iterable[str], hypotheses: Iterable[str]) -> float:
    """Micro-average character errors over all utterances in a corpus."""
    pairs = list(zip(references, hypotheses))
    errors = sum(
        _edit_distance(list((reference or "").lower()), list((hypothesis or "").lower()))
        for reference, hypothesis in pairs
    )
    characters = sum(len(reference or "") for reference, _ in pairs)
    return errors / max(1, characters)


def normalized_wer(reference: str, hypothesis: str, mode: str = NORMALIZATION_MODE) -> float:
    """WER after the explicitly reported evaluation normalization."""
    return wer(normalize_for_evaluation(reference, mode), normalize_for_evaluation(hypothesis, mode))


def normalized_cer(reference: str, hypothesis: str, mode: str = NORMALIZATION_MODE) -> float:
    """CER after the explicitly reported evaluation normalization."""
    return cer(normalize_for_evaluation(reference, mode), normalize_for_evaluation(hypothesis, mode))


def sentence_error_rate(references: Iterable[str], hypotheses: Iterable[str]) -> float:
    pairs = list(zip(references, hypotheses))
    if not pairs:
        return 0.0
    return sum(reference.strip().lower() != hypothesis.strip().lower() for reference, hypothesis in pairs) / len(pairs)


def classification_accuracy(labels: Iterable[str], predictions: Iterable[str]) -> float:
    pairs = list(zip(labels, predictions))
    return sum(label == prediction for label, prediction in pairs) / len(pairs) if pairs else 0.0


def mean(values: Iterable[float | int | None]) -> float | None:
    """Return a mean while ignoring missing values.

    Evaluation reports use ``None`` when a metric has no valid observations. This
    is deliberately different from zero, which is a measured value.
    """
    usable = [float(value) for value in values if value is not None]
    return sum(usable) / len(usable) if usable else None


def percentile(values: Iterable[float | int | None], percentage: float) -> float | None:
    """Compute a small dependency-free linear percentile."""
    usable = sorted(float(value) for value in values if value is not None)
    if not usable:
        return None
    if not 0 <= percentage <= 100:
        raise ValueError("percentage must be between 0 and 100")
    if len(usable) == 1:
        return usable[0]
    position = (len(usable) - 1) * percentage / 100
    lower = int(position)
    upper = min(lower + 1, len(usable) - 1)
    weight = position - lower
    return usable[lower] + (usable[upper] - usable[lower]) * weight


def correction_outcome(
    baseline_reference_error: float,
    final_reference_error: float,
    correction_applied: bool,
) -> str:
    """Classify the effect of a correction against a reference transcript."""
    if not correction_applied:
        return "not_applied"
    if final_reference_error < baseline_reference_error:
        return "improved"
    if final_reference_error > baseline_reference_error:
        return "harmful"
    return "unchanged"


def correction_summary(outcomes: Iterable[str]) -> dict[str, float | int | None]:
    """Summarise selective-correction outcomes without hiding the denominator."""
    values = list(outcomes)
    applied = sum(value != "not_applied" for value in values)
    improved = sum(value == "improved" for value in values)
    harmful = sum(value == "harmful" for value in values)
    unchanged = sum(value == "unchanged" for value in values)
    total = len(values)
    return {
        "correction_rate": applied / total if total else None,
        "improvement_rate_all": improved / total if total else None,
        "harmful_correction_rate": harmful / applied if applied else None,
        "harmful_correction_rate_all": harmful / total if total else None,
        "corrections_applied": applied,
        "improved_corrections": improved,
        "harmful_corrections": harmful,
        "unchanged_corrections": unchanged,
    }


def error_detection_metrics(labels: list[int], scores: list[float], threshold: float = 0.5) -> dict[str, float | None]:
    if not labels:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "auroc": None, "auprc": None}
    predicted = [int(score >= threshold) for score in scores]
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predicted))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predicted))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predicted))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    auroc = _rank_auc(labels, scores) if len(set(labels)) == 2 else None
    positives = sum(labels)
    if positives:
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        hit = 0
        area = 0.0
        for rank, index in enumerate(order, 1):
            if labels[index]:
                hit += 1
                area += hit / rank
        auprc = area / positives
    else:
        auprc = None
    return {"precision": precision, "recall": recall, "f1": f1, "auroc": auroc, "auprc": auprc}


def _rank_auc(labels: list[int], scores: list[float]) -> float:
    positives = [score for score, label in zip(scores, labels) if label]
    negatives = [score for score, label in zip(scores, labels) if not label]
    if not positives or not negatives:
        return 0.5
    wins = sum(1.0 if positive > negative else 0.5 if positive == negative else 0.0 for positive in positives for negative in negatives)
    return wins / (len(positives) * len(negatives))
