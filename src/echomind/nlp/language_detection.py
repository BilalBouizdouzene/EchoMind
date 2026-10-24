"""Honest experimental language and code-switch indicators."""

from __future__ import annotations

import re

LEXICONS = {
    "fr": {"bonjour", "demain", "rendez-vous", "je", "veux", "pour", "annuler", "réserver", "non"},
    "en": {"hello", "tomorrow", "meeting", "book", "cancel", "schedule", "please", "no", "change"},
    "ar": {"مرحبا", "غدا", "موعد", "أريد", "إلغاء", "الحجز", "لا"},
}


def detect_languages(text: str) -> tuple[list[str], str]:
    tokens = set(re.findall(r"[\wÀ-ÿ؀-ۿ'-]+", text.lower()))
    hits = {language: len(tokens & words) for language, words in LEXICONS.items()}
    present = [language for language, count in hits.items() if count > 0]
    if len(present) >= 2:
        return present, "mixed"
    if present:
        return present, present[0]
    return [], "unknown"
