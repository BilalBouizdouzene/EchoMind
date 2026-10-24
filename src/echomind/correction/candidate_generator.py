"""Candidate generation from bounded alternative decodes."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from echomind.asr.decoding import alternative_config
from echomind.asr.whisper_engine import DecodingConfig, WhisperEngine
from echomind.pipeline.schemas import Candidate, TranscriptionSegment


@dataclass
class GeneratedCandidates:
    candidates: list[Candidate]
    reason: list[str]


def generate_candidates(
    engine: WhisperEngine,
    audio: np.ndarray,
    sample_rate: int,
    segment: TranscriptionSegment,
    base_config: DecodingConfig,
    attempt: int = 1,
    decode_start: float | None = None,
    decode_end: float | None = None,
) -> GeneratedCandidates:
    crop_start = max(0.0, segment.start if decode_start is None else decode_start)
    crop_end = min(
        len(audio) / sample_rate,
        segment.end if decode_end is None else decode_end,
    )
    start = max(0, int(crop_start * sample_rate))
    end = min(len(audio), max(start + 1, int(crop_end * sample_rate)))
    crop_start = start / sample_rate
    local = audio[start:end]
    baseline_probabilities = _word_probabilities(segment.words)
    candidates = [
        Candidate(
            text=segment.text,
            start=segment.start,
            end=segment.end,
            source="baseline",
            score=0.0,
            mean_word_probability=(
                sum(baseline_probabilities) / len(baseline_probabilities)
                if baseline_probabilities
                else None
            ),
            evidence=["baseline hypothesis retained for comparison"],
        )
    ]
    hypotheses: dict[str, dict[str, object]] = {}
    attempts = (attempt, attempt + 1)
    for decode_attempt in attempts:
        result = engine.transcribe(
            local,
            sample_rate=sample_rate,
            language_hint=segment.language,
            config=alternative_config(base_config, decode_attempt),
        )
        text, mean_probability = _text_inside_target(result, crop_start, crop_end, segment)
        key = _normalise(text)
        if not key or key == _normalise(segment.text):
            continue
        hypothesis = hypotheses.setdefault(key, {"text": text, "attempts": 0, "probabilities": []})
        hypothesis["attempts"] = int(hypothesis["attempts"]) + 1
        if mean_probability is not None:
            probabilities = hypothesis["probabilities"]
            assert isinstance(probabilities, list)
            probabilities.append(mean_probability)

    for hypothesis in hypotheses.values():
        agreement_count = int(hypothesis["attempts"])
        evidence = ["bounded local alternative decode"]
        score = 0.0
        if agreement_count >= 2:
            evidence.append("two alternative decoding configurations agree on this alternative")
            score = 0.20
        probabilities = hypothesis["probabilities"]
        assert isinstance(probabilities, list)
        alternative_probability = sum(probabilities) / len(probabilities) if probabilities else None
        baseline_probability = candidates[0].mean_word_probability
        if alternative_probability is not None and baseline_probability is not None:
            delta = alternative_probability - baseline_probability
            evidence.append(f"target-region mean word confidence delta={delta:+.3f}")
        candidates.append(
            Candidate(
                text=str(hypothesis["text"]),
                start=segment.start,
                end=segment.end,
                source="redecode",
                score=score,
                agreement_count=agreement_count,
                mean_word_probability=alternative_probability,
                evidence=evidence,
            )
        )
    reason = ["two bounded local decoding configurations were compared"]
    if any(candidate.agreement_count >= 2 for candidate in candidates if candidate.source == "redecode"):
        reason.append("both alternative decoding passes agree")
    else:
        reason.append("alternative decoding passes did not agree; no acoustic consensus")
    return GeneratedCandidates(candidates=candidates, reason=reason)


def _text_inside_target(
    result,
    crop_start: float,
    crop_end: float,
    target: TranscriptionSegment,
) -> tuple[str, float | None]:
    selected_words: list[tuple[float, str, float | None]] = []
    selected_segments: list[tuple[float, str]] = []
    for decoded in result.segments:
        for word in decoded.words or []:
            text = str(word.get("word", ""))
            try:
                word_start = crop_start + float(word["start"])
                word_end = crop_start + float(word["end"])
            except (KeyError, TypeError, ValueError):
                continue
            midpoint = (word_start + word_end) / 2
            if target.start <= midpoint <= target.end and text.strip():
                probability = word.get("probability")
                selected_words.append(
                    (
                        word_start,
                        text,
                        float(probability)
                        if isinstance(probability, (int, float)) and 0 <= probability <= 1
                        else None,
                    )
                )
        midpoint = crop_start + (decoded.start + decoded.end) / 2
        if target.start <= midpoint <= target.end and decoded.text.strip():
            selected_segments.append((midpoint, decoded.text.strip()))

    if selected_words:
        ordered_words = sorted(selected_words)
        probabilities = [probability for _, _, probability in ordered_words if probability is not None]
        text = "".join(word_text for _, word_text, _ in ordered_words).strip()
        mean_probability = sum(probabilities) / len(probabilities) if probabilities else None
        return text, mean_probability
    if selected_segments:
        return " ".join(text for _, text in sorted(selected_segments)).strip(), None
    exact_target_crop = abs(crop_start - target.start) <= 0.02 and abs(crop_end - target.end) <= 0.02
    if not result.segments and exact_target_crop:
        return result.text.strip(), None
    return "", None


def _word_probabilities(words: list[dict] | None) -> list[float]:
    return [
        float(probability)
        for word in words or []
        if isinstance((probability := word.get("probability")), (int, float))
        and 0 <= probability <= 1
    ]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.casefold(), flags=re.UNICODE)).strip()
