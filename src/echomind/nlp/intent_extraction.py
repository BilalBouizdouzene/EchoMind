"""Transparent multilingual intent and entity extraction."""

from __future__ import annotations

import re

from echomind.nlp.language_detection import detect_languages
from echomind.pipeline.schemas import SemanticInterpretation

INTENT_PATTERNS = {
    "appointment_rescheduling": ["rendez-vous", "meeting", "schedule", "change", "bghit", "نبدل"],
    "booking_cancellation": ["cancel", "annuler", "cancel my booking"],
    "booking_creation": ["book", "réserver", "reserve", "appointment", "موعد"],
}


def extract_semantics(text: str) -> SemanticInterpretation:
    lower = text.lower()
    languages, language_mode = detect_languages(text)
    scores = {intent: sum(1 for token in words if token in lower) for intent, words in INTENT_PATTERNS.items()}
    intent, count = max(scores.items(), key=lambda item: item[1])
    if count == 0:
        intent = "unknown"
        confidence = 0.0
    else:
        confidence = min(0.95, 0.45 + 0.15 * count)
    entities = {}
    dates = re.findall(r"\b(?:today|tomorrow|demain|après-demain|after tomorrow|monday|tuesday|wednesday|thursday|friday|samedi|Saturday|vendredi)\b", text, flags=re.I)
    times = re.findall(r"\b(?:\d{1,2}(?::\d{2})?\s?(?:am|pm|AM|PM)?|fifteen|fifty|dix|onze)\b", text)
    if dates:
        entities["date"] = dates
    if times:
        entities["time"] = times
    return SemanticInterpretation(
        intent=intent,
        intent_confidence=confidence,
        entities=entities,
        possible_languages=languages,
        code_switching="mixed" if language_mode == "mixed" else "no" if language_mode != "unknown" else "unknown",
        grounding_notes=["rule-based extraction from transcript; no new facts generated"],
    )
