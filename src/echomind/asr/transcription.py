"""Helpers for normalising transcript output."""

from __future__ import annotations

import re

from echomind.pipeline.schemas import TranscriptionResult


def clean_transcript(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def transcript_language(result: TranscriptionResult) -> str:
    if result.language:
        return result.language
    return "unknown"
