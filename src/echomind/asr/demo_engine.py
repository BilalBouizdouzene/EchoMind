"""Deterministic model-free scenarios for portfolio demonstrations.

This engine is intentionally labelled as simulated. It demonstrates the decision
and provenance UX without pretending that a tone waveform contains speech.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from echomind.asr.whisper_engine import DecodingConfig
from echomind.pipeline.schemas import DecoderStats, TranscriptionResult, TranscriptionSegment


@dataclass(frozen=True)
class DemoScenario:
    baseline: str
    alternative: str
    language: str
    baseline_stats: DecoderStats


SCENARIOS = {
    "selective_correction": DemoScenario(
        baseline="Schedule the meeting Thursday.",
        alternative="Schedule the meeting for Friday.",
        language="en",
        baseline_stats=DecoderStats(avg_logprob=-1.8, no_speech_prob=0.6, compression_ratio=2.7, source="simulated demo metadata"),
    ),
    "self_correction": DemoScenario(
        baseline="I want to cancel my booking Monday, no Tuesday.",
        alternative="I want to cancel my booking Monday, no Tuesday.",
        language="en",
        baseline_stats=DecoderStats(avg_logprob=-0.2, no_speech_prob=0.04, source="simulated demo metadata"),
    ),
    "multilingual": DemoScenario(
        baseline="Bonjour, I want to change le rendez-vous pour demain.",
        alternative="Bonjour, I want to change le rendez-vous pour demain.",
        language="fr",
        baseline_stats=DecoderStats(avg_logprob=-0.3, no_speech_prob=0.03, source="simulated demo metadata"),
    ),
}


def demo_audio(sample_rate: int = 16000, duration_seconds: float = 2.2) -> np.ndarray:
    """Return a harmless local tone used only to drive the demo pipeline."""
    time = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    envelope = np.minimum(1.0, time * 8) * np.minimum(1.0, (duration_seconds - time) * 8)
    return (0.08 * envelope * np.sin(2 * np.pi * 220 * time)).astype(np.float32)


class DemoEngine:
    is_demo = True

    def __init__(self, scenario: str = "selective_correction") -> None:
        self.scenario_name = scenario if scenario in SCENARIOS else "selective_correction"
        self.scenario = SCENARIOS[self.scenario_name]
        self.config = DecodingConfig(model_name="demo", beam_size=1)

    def transcribe(self, audio, sample_rate=16000, language_hint=None, config=None) -> TranscriptionResult:
        is_alternative = config is not None
        text = self.scenario.alternative if is_alternative else self.scenario.baseline
        stats = DecoderStats(
            avg_logprob=-0.15 if is_alternative else self.scenario.baseline_stats.avg_logprob,
            no_speech_prob=0.03 if is_alternative else self.scenario.baseline_stats.no_speech_prob,
            compression_ratio=1.7 if is_alternative else self.scenario.baseline_stats.compression_ratio,
            beam_size=config.beam_size if config else 1,
            temperature=config.temperature if config else 0.0,
            source="simulated demo metadata",
        )
        duration = max(0.8, len(audio) / sample_rate) if hasattr(audio, "__len__") else 2.2
        segment = TranscriptionSegment(
            id=0,
            start=0.0,
            end=min(duration, 2.0),
            text=text,
            language=self.scenario.language,
            decoder_stats=stats,
        )
        return TranscriptionResult(
            text=text,
            language=self.scenario.language,
            language_probability=0.99,
            segments=[segment],
            model_name="demo-simulator",
            backend="simulated-demo",
            latency_ms=18.0 if is_alternative else 12.0,
            warnings=["Synthetic demo mode: transcript and decoder statistics are simulated."],
        )
