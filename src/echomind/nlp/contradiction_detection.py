"""Self-correction and contradiction detection kept separate from ASR error risk."""

from __future__ import annotations

import re

from echomind.pipeline.schemas import SelfCorrectionEvent

MARKERS = (
    "je voulais dire",
    "je veux dire",
    "en fait",
    "actually",
    "rather",
    "sorry",
    "pardon",
    "plutôt",
    "non",
    "no",
    "or",
)
MARKER_PATTERN = re.compile(
    rf"\b(?P<marker>{'|'.join(re.escape(item) for item in MARKERS)})\b",
    flags=re.IGNORECASE,
)


def detect_self_correction(text: str) -> SelfCorrectionEvent:
    marker_match = MARKER_PATTERN.search(text)
    if marker_match is None:
        return SelfCorrectionEvent()
    marker = marker_match.group("marker").lower()
    before_text = text[:marker_match.start()].rstrip(" \t,;:")
    after_text = text[marker_match.end():].lstrip(" \t,;:")
    before_parts = [part.strip(" \t,;:") for part in re.split(r"[.!?;…]+", before_text)]
    before = next((part for part in reversed(before_parts) if part), None)
    after = re.split(r"[,.;!?…]+", after_text, maxsplit=1)[0].strip() or None
    has_replacement = bool(before and after)
    category = "generic"
    combined = f"{before or ''} {after or ''}".lower()
    if re.search(
        r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|demain|tomorrow|tonight|ce soir",
        combined,
    ):
        category = "date"
    elif re.search(r"\b\d{1,2}\s*(?:h|heures?|am|pm)?\b|am|pm|fifteen|fifty|dix|onze", combined):
        category = "time"
    return SelfCorrectionEvent(
        detected=True,
        marker=marker,
        replaced_value=before,
        final_value=after,
        category=category,
        confidence=0.80 if has_replacement else 0.55,
    )


def contradiction_reasons(text: str) -> list[str]:
    event = detect_self_correction(text)
    if not event.detected:
        return []
    return [f"explicit self-correction marker: {event.marker}"]
