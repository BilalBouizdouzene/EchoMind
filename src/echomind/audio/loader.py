"""Safe local audio loading with a small dependency footprint."""

from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import BinaryIO

import numpy as np

SUPPORTED_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3"}
MAX_AUDIO_BYTES = 16 * 1024 * 1024
MAX_AUDIO_SECONDS = 300.0


class AudioLoadError(RuntimeError):
    """Raised when audio cannot be decoded locally."""


def _from_wave(path: Path) -> tuple[np.ndarray, int, int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        sample_width = handle.getsampwidth()
        frames = handle.readframes(handle.getnframes())
    if sample_width == 2:
        data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 1:
        data = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128) / 128.0
    elif sample_width == 4:
        data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise AudioLoadError(f"Unsupported WAV sample width: {sample_width} bytes")
    return data, sample_rate, channels


def load_audio(
    source: str | Path | BinaryIO | np.ndarray,
    sample_rate: int | None = None,
    max_bytes: int = MAX_AUDIO_BYTES,
    max_duration_seconds: float = MAX_AUDIO_SECONDS,
) -> tuple[np.ndarray, int, int]:
    """Load audio as float32 samples in [-1, 1].

    MP3 support depends on the local libsndfile/FFmpeg setup. No remote service is used.
    """
    if isinstance(source, np.ndarray):
        data = np.asarray(source, dtype=np.float32)
        effective_rate = sample_rate or 16000
        if data.ndim == 1:
            if data.size / effective_rate > max_duration_seconds:
                raise AudioLoadError(f"Audio exceeds the {max_duration_seconds:g}s duration limit")
            return data, effective_rate, 1
        if data.ndim == 2:
            if data.shape[0] / effective_rate > max_duration_seconds:
                raise AudioLoadError(f"Audio exceeds the {max_duration_seconds:g}s duration limit")
            return data, effective_rate, data.shape[1]
        raise AudioLoadError("Audio array must be one- or two-dimensional")
    path = Path(source) if isinstance(source, (str, Path)) else None
    if path and path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise AudioLoadError(f"Unsupported audio extension: {path.suffix or '<none>'}")
    if path:
        if not path.is_file():
            raise AudioLoadError(f"Audio file does not exist: {path}")
        if path.stat().st_size > max_bytes:
            raise AudioLoadError(f"Audio file exceeds the {max_bytes // (1024 * 1024)} MB size limit")
    elif hasattr(source, "seek") and hasattr(source, "tell"):
        current = source.tell()
        source.seek(0, 2)
        size = source.tell()
        source.seek(current)
        if size > max_bytes:
            raise AudioLoadError(f"Audio stream exceeds the {max_bytes // (1024 * 1024)} MB size limit")
    try:
        import soundfile as sf

        if path:
            data, rate = sf.read(path, dtype="float32", always_2d=False)
        else:
            data, rate = sf.read(source, dtype="float32", always_2d=False)
        channels = 1 if data.ndim == 1 else data.shape[1]
        data = np.asarray(data, dtype=np.float32)
        duration = data.shape[0] / int(rate) if int(rate) > 0 else 0.0
        if duration > max_duration_seconds:
            raise AudioLoadError(f"Audio exceeds the {max_duration_seconds:g}s duration limit")
        return data, int(rate), channels
    except Exception as soundfile_error:
        if path and path.suffix.lower() == ".wav":
            try:
                data, rate, channels = _from_wave(path)
                if data.shape[0] / rate > max_duration_seconds:
                    raise AudioLoadError(f"Audio exceeds the {max_duration_seconds:g}s duration limit")
                return data, rate, channels
            except Exception as wave_error:
                raise AudioLoadError(str(wave_error)) from wave_error
        if path is None and hasattr(source, "seek"):
            try:
                source.seek(0)
                data, rate, channels = _from_wave_bytes(source)
                if data.shape[0] / rate > max_duration_seconds:
                    raise AudioLoadError(f"Audio exceeds the {max_duration_seconds:g}s duration limit")
                return data, rate, channels
            except Exception:
                pass
        raise AudioLoadError(
            f"Could not decode audio locally. Install soundfile/FFmpeg support. Details: {soundfile_error}"
        ) from soundfile_error


def _from_wave_bytes(source: BinaryIO) -> tuple[np.ndarray, int, int]:
    with wave.open(source if isinstance(source, io.BufferedIOBase) else source, "rb") as handle:
        channels = handle.getnchannels()
        rate = handle.getframerate()
        width = handle.getsampwidth()
        frames = handle.readframes(handle.getnframes())
    if width != 2:
        raise AudioLoadError("Only 16-bit WAV byte streams are supported by fallback decoder")
    data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return data, rate, channels


def to_mono(data: np.ndarray) -> np.ndarray:
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 1:
        return data
    return np.mean(data, axis=1, dtype=np.float32)
