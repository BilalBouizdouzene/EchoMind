"""Feature extraction for segment-level ASR error risk."""

from __future__ import annotations

import re

from echomind.pipeline.schemas import (
    AudioMetadata,
    TranscriptionSegment,
    UncertaintyFeatures,
)


def extract_features(
    segment: TranscriptionSegment,
    audio: AudioMetadata | None = None,
    context_text: str = "",
) -> UncertaintyFeatures:
    stats = segment.decoder_stats
    quality = audio.quality if audio else None
    text = segment.text.strip()
    instability = _text_instability(text)
    language_switch = _language_switch_indicator(text)
    semantic_inconsistency = 0.15 if context_text and _looks_unrelated(text, context_text) else 0.0
    word_probabilities = [
        float(word["probability"])
        for word in (segment.words or [])
        if isinstance(word.get("probability"), (int, float))
    ]
    return UncertaintyFeatures(
        duration=max(0.0, segment.end - segment.start),
        rms=quality.rms if quality else 0.0,
        clipping_ratio=quality.clipping_ratio if quality else 0.0,
        silence_proximity=quality.silence_ratio if quality else 0.0,
        avg_logprob=stats.avg_logprob,
        mean_word_probability=(sum(word_probabilities) / len(word_probabilities)) if word_probabilities else None,
        low_word_probability_ratio=(
            sum(probability < 0.55 for probability in word_probabilities) / len(word_probabilities)
            if word_probabilities else 0.0
        ),
        no_speech_prob=stats.no_speech_prob,
        compression_ratio=stats.compression_ratio,
        text_instability=instability,
        language_switch=language_switch,
        semantic_inconsistency=semantic_inconsistency,
    )


def _text_instability(text: str) -> float:
    if not text:
        return 1.0
    repeated = len(re.findall(r"\b(\w+)\s+\1\b", text.lower()))
    odd_symbols = sum(character in "�□" for character in text)
    return min(1.0, repeated * 0.25 + odd_symbols * 0.4 + (0.2 if len(text) < 2 else 0.0))


def _language_switch_indicator(text: str) -> float:
    lower = text.lower()
    french = {"bonjour", "rendez-vous", "demain", "pour", "avec", "je", "veux"}
    english = {"hello", "tomorrow", "meeting", "book", "cancel", "please", "the"}
    arabic = {"مرحبا", "غدا", "موعد", "أريد", "إلغاء", "الحجز"}
    hits = [bool(set(lower.split()) & words) for words in (french, english, arabic)]
    return 0.7 if sum(hits) >= 2 else 0.0


def _looks_unrelated(text: str, context: str) -> bool:
    left = set(re.findall(r"\w+", text.lower()))
    right = set(re.findall(r"\w+", context.lower()))
    return bool(left) and not (left & right)
