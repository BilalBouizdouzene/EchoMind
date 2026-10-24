"""Lazy faster-whisper adapter with an honest no-model fallback."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from echomind.audio.loader import load_audio, to_mono
from echomind.audio.preprocessing import resample_audio
from echomind.pipeline.schemas import DecoderStats, TranscriptionResult, TranscriptionSegment


@dataclass
class DecodingConfig:
    model_name: str = "tiny"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 1
    temperature: float = 0.0
    language: str | None = None
    word_timestamps: bool = True
    cpu_threads: int = 4
    vad_filter: bool = False
    local_files_only: bool = True


class WhisperEngine:
    """A single lazy model instance; model weights are never downloaded implicitly."""

    def __init__(self, config: DecodingConfig | None = None) -> None:
        self.config = config or DecodingConfig()
        self._model: Any | None = None
        self._load_error: str | None = None
        self._inference_lock = threading.RLock()

    @property
    def available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def load(self) -> Any:
        with self._inference_lock:
            if self._model is not None:
                return self._model
            if self._load_error:
                raise RuntimeError(self._load_error)
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.config.model_name,
                    device=self.config.device,
                    compute_type=self.config.compute_type,
                    cpu_threads=self.config.cpu_threads,
                    local_files_only=self.config.local_files_only,
                )
                return self._model
            except Exception as error:
                self._load_error = (
                    "faster-whisper is unavailable or the model is not installed locally: "
                    f"{error}"
                )
                raise RuntimeError(self._load_error) from error

    def unload(self) -> None:
        with self._inference_lock:
            self._model = None
            self._load_error = None

    def transcribe(
        self,
        audio: np.ndarray | str | Path,
        sample_rate: int = 16000,
        language_hint: str | None = None,
        config: DecodingConfig | None = None,
    ) -> TranscriptionResult:
        active = config or self.config
        started = time.perf_counter()
        if not self.available:
            return TranscriptionResult(
                model_name=active.model_name,
                backend="faster-whisper",
                latency_ms=(time.perf_counter() - started) * 1000,
                warnings=[
                    "faster-whisper is not installed. Install the optional ASR extra and download a model locally."
                ],
            )
        try:
            with self._inference_lock:
                model = self.load()
                source: Any = audio
                if isinstance(audio, (str, Path)):
                    loaded, loaded_rate, _ = load_audio(audio)
                    source = resample_audio(to_mono(loaded), loaded_rate, 16000)
                segments, info = model.transcribe(
                    source,
                    language=language_hint or active.language,
                    beam_size=active.beam_size,
                    temperature=active.temperature,
                    word_timestamps=active.word_timestamps,
                    vad_filter=active.vad_filter,
                )
                parsed: list[TranscriptionSegment] = []
                for index, item in enumerate(segments):
                    stats = DecoderStats(
                        avg_logprob=_optional_float(item, "avg_logprob"),
                        no_speech_prob=_optional_float(item, "no_speech_prob"),
                        compression_ratio=_optional_float(item, "compression_ratio"),
                        beam_size=active.beam_size,
                        temperature=active.temperature,
                        source="faster-whisper segment metadata",
                    )
                    words = None
                    if getattr(item, "words", None) is not None:
                        words = [
                            {"word": word.word, "start": word.start, "end": word.end, "probability": getattr(word, "probability", None)}
                            for word in item.words
                        ]
                    parsed.append(
                        TranscriptionSegment(
                            id=index,
                            start=float(item.start),
                            end=max(float(item.end), float(item.start) + 0.001),
                            text=str(item.text).strip(),
                            language=getattr(info, "language", None),
                            decoder_stats=stats,
                            words=words,
                        )
                    )
            return TranscriptionResult(
                text=" ".join(segment.text for segment in parsed).strip(),
                language=getattr(info, "language", None),
                language_probability=_optional_float(info, "language_probability"),
                segments=parsed,
                model_name=active.model_name,
                backend="faster-whisper",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as error:
            return TranscriptionResult(
                model_name=active.model_name,
                backend="faster-whisper",
                latency_ms=(time.perf_counter() - started) * 1000,
                warnings=[f"ASR failed: {error}"],
            )


def _optional_float(obj: Any, name: str) -> float | None:
    value = getattr(obj, name, None)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
