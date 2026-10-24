"""Named decoding alternatives used by selective re-decoding."""

from __future__ import annotations

from dataclasses import replace

from echomind.asr.whisper_engine import DecodingConfig


def alternative_config(base: DecodingConfig, attempt: int = 1) -> DecodingConfig:
    """Create a bounded alternative without pretending it is an ensemble."""
    if attempt % 2:
        return replace(base, beam_size=max(2, base.beam_size + 1), temperature=0.0)
    return replace(base, beam_size=1, temperature=0.2)
