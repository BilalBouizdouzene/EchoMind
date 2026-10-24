"""Deterministic CPU-friendly audio preprocessing."""

from __future__ import annotations

import time

import numpy as np

from echomind.audio.features import quality_indicators
from echomind.audio.loader import to_mono
from echomind.audio.segmentation import segments_from_mask
from echomind.audio.vad import energy_vad
from echomind.pipeline.schemas import AudioMetadata


def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int = 16000) -> np.ndarray:
    """Resample with SciPy when available and linear interpolation otherwise."""
    if source_rate == target_rate:
        return np.asarray(audio, dtype=np.float32)
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("Sample rates must be positive")
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0:
        return audio.copy()
    try:
        from math import gcd

        from scipy.signal import resample_poly

        divisor = gcd(source_rate, target_rate)
        return np.asarray(resample_poly(audio, target_rate // divisor, source_rate // divisor), dtype=np.float32)
    except ImportError:
        old_times = np.arange(audio.size, dtype=np.float64) / source_rate
        new_length = max(1, int(round(audio.size * target_rate / source_rate)))
        new_times = np.arange(new_length, dtype=np.float64) / target_rate
        return np.interp(new_times, old_times, audio).astype(np.float32)


def safe_normalize(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0:
        return audio.copy()
    peak = float(np.max(np.abs(audio)))
    if peak <= 1e-8 or not np.isfinite(peak):
        return np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
    return np.clip(audio * min(1.0, target_peak / peak), -1.0, 1.0)


def preprocess_audio(
    audio: np.ndarray,
    source_rate: int,
    target_rate: int = 16000,
    frame_ms: int = 30,
    hop_ms: int = 15,
) -> tuple[np.ndarray, AudioMetadata]:
    started = time.perf_counter()
    mono = to_mono(audio)
    converted = resample_audio(mono, source_rate, target_rate)
    normalized = safe_normalize(converted)
    mask, frame_energy = energy_vad(normalized, target_rate, frame_ms=frame_ms, hop_ms=hop_ms)
    segments = segments_from_mask(mask, hop_ms / 1000.0, normalized, target_rate)
    quality = quality_indicators(normalized, target_rate, mask, frame_energy)
    duration = len(normalized) / target_rate if target_rate else 0.0
    speech_duration = sum(item.end - item.start for item in segments)
    metadata = AudioMetadata(
        sample_rate=target_rate,
        channels=1,
        duration_seconds=duration,
        speech_duration_seconds=min(duration, speech_duration),
        segments=segments,
        quality=quality,
        processing_time_ms=(time.perf_counter() - started) * 1000,
    )
    return normalized, metadata
