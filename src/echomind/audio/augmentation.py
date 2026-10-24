"""Reproducible local audio augmentation for evaluation experiments."""

from __future__ import annotations

import numpy as np

from echomind.audio.preprocessing import resample_audio


def augment_audio(
    audio: np.ndarray,
    sample_rate: int,
    *,
    seed: int = 0,
    noise_std: float = 0.0,
    speed: float = 1.0,
    gain_db: float = 0.0,
    reverb_decay: float = 0.0,
) -> np.ndarray:
    """Apply modest, deterministic perturbations without changing speaker identity.

    Augmented files must retain the source recording/speaker IDs in the manifest.
    """
    rng = np.random.default_rng(seed)
    result = np.asarray(audio, dtype=np.float32).copy()
    if speed <= 0:
        raise ValueError("speed must be positive")
    if speed != 1.0 and result.size:
        result = resample_audio(result, sample_rate, max(1, round(sample_rate / speed)))
        result = resample_audio(result, max(1, round(sample_rate / speed)), sample_rate)
    if gain_db:
        result *= float(10 ** (gain_db / 20))
    if noise_std:
        result += rng.normal(0.0, noise_std, size=result.shape).astype(np.float32)
    if reverb_decay:
        if not 0 <= reverb_decay < 1:
            raise ValueError("reverb_decay must be in [0, 1)")
        delay = max(1, int(sample_rate * 0.04))
        echoed = np.zeros_like(result)
        if result.size > delay:
            echoed[delay:] = result[:-delay] * reverb_decay
        result += echoed
    return np.clip(result, -1.0, 1.0).astype(np.float32)
