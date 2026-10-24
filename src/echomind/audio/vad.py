"""Energy VAD fallback; Silero can be added without changing pipeline contracts."""

from __future__ import annotations

import numpy as np


def energy_vad(
    audio: np.ndarray,
    sample_rate: int,
    frame_ms: int = 30,
    hop_ms: int = 15,
    threshold_db: float = -42.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return a boolean frame mask and RMS energy per frame.

    The threshold is relative to the median non-silent frame, which is more stable
    than a hard amplitude threshold for microphone recordings.
    """
    audio = np.asarray(audio, dtype=np.float32)
    frame = max(1, int(sample_rate * frame_ms / 1000))
    hop = max(1, int(sample_rate * hop_ms / 1000))
    if audio.size == 0:
        return np.zeros(0, dtype=bool), np.zeros(0, dtype=np.float32)
    if audio.size < frame:
        padded = np.pad(audio, (0, frame - audio.size))
        frames = padded[None, :]
    else:
        count = 1 + max(0, (audio.size - frame) // hop)
        frames = np.stack([audio[i * hop : i * hop + frame] for i in range(count)])
    rms = np.sqrt(np.mean(np.square(frames), axis=1) + 1e-12)
    db = 20 * np.log10(np.maximum(rms, 1e-7))
    reference = float(np.percentile(db, 75)) if db.size else threshold_db
    dynamic_threshold = max(threshold_db, reference - 35.0)
    mask = db >= dynamic_threshold
    if np.any(mask):
        mask = _fill_short_gaps(mask, max(1, int(0.12 / (hop_ms / 1000))))
    return mask, rms.astype(np.float32)


def _fill_short_gaps(mask: np.ndarray, max_gap: int) -> np.ndarray:
    result = mask.copy()
    false_runs: list[tuple[int, int]] = []
    start = None
    for index, value in enumerate(mask):
        if not value and start is None:
            start = index
        if value and start is not None:
            false_runs.append((start, index))
            start = None
    if start is not None:
        false_runs.append((start, len(mask)))
    for left, right in false_runs:
        if left > 0 and right < len(mask) and right - left <= max_gap:
            result[left:right] = True
    return result
