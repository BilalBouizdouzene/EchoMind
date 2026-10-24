"""Deterministic Unicode normalization for multilingual ASR evaluation."""

from __future__ import annotations

import re
import unicodedata

NORMALIZATION_MODE = "unicode"


def normalize_for_evaluation(text: str, mode: str = NORMALIZATION_MODE) -> str:
    """Normalize case, Unicode variants, diacritics and punctuation.

    The project evaluates English, French and standard Arabic in their native
    scripts. No transliteration is performed, so the normalized metric cannot
    hide a script mismatch between a reference and a hypothesis.
    """
    if mode != NORMALIZATION_MODE:
        raise ValueError(f"Unsupported normalization mode: {mode}")
    value = unicodedata.normalize("NFKC", text or "").casefold().replace("ـ", "")
    value = "".join(
        character for character in value if unicodedata.category(character) != "Mn"
    )
    value = "".join(
        character if character.isalnum() or character.isspace() else " "
        for character in value
    )
    return re.sub(r"\s+", " ", value).strip()
