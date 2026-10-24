"""Audio quality indicators used as uncertainty evidence."""

from __future__ import annotations

import numpy as np

from echomind.pipeline.schemas import AudioQuality


def quality_indicators(
    audio: np.ndarray,
    sample_rate: int,
    vad_mask: np.ndarray | None = None,
    frame_energy: np.ndarray | None = None,
) -> AudioQuality:
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0:
        return AudioQuality(quality_label="unknown", notes=["empty audio"])
    abs_audio = np.abs(audio)
    rms = float(np.sqrt(np.mean(np.square(audio)) + 1e-12))
    peak = float(np.max(abs_audio))
    clipping = float(np.mean(abs_audio >= 0.999))
    silence = float(np.mean(abs_audio < max(1e-4, peak * 0.01)))
    if vad_mask is not None and vad_mask.size:
        silence = float(1.0 - np.mean(vad_mask))
    snr = _estimate_snr_db(frame_energy)
    notes = []
    if clipping > 0.01:
        notes.append("possible clipping")
    if silence > 0.8:
        notes.append("mostly silent")
    if rms < 0.005:
        notes.append("low signal energy")
    if snr is not None and snr < 8:
        notes.append("low estimated SNR")
    penalty = min(1.0, clipping * 10 + max(0, silence - 0.65) + (0.2 if rms < 0.005 else 0))
    label = "good" if penalty < 0.2 else "fair" if penalty < 0.5 else "poor"
    return AudioQuality(
        rms=rms,
        peak=peak,
        clipping_ratio=clipping,
        silence_ratio=min(1.0, max(0.0, silence)),
        estimated_snr_db=snr,
        quality_label=label,
        notes=notes,
    )


def _estimate_snr_db(frame_energy: np.ndarray | None) -> float | None:
    if frame_energy is None or len(frame_energy) < 2:
        return None
    values = np.asarray(frame_energy, dtype=np.float32)
    noise = float(np.percentile(values, 20))
    signal = float(np.percentile(values, 80))
    if noise <= 1e-8:
        return 60.0 if signal > 1e-5 else 0.0
    return float(20 * np.log10(max(signal, 1e-8) / noise))
