"""Timestamped speech-region construction."""

from __future__ import annotations

import numpy as np

from echomind.pipeline.schemas import AudioSegment


def segments_from_mask(mask: np.ndarray, hop_seconds: float, audio: np.ndarray, sample_rate: int) -> list[AudioSegment]:
    if mask.size == 0:
        return []
    regions: list[tuple[int, int]] = []
    start = None
    for index, active in enumerate(mask):
        if active and start is None:
            start = index
        elif not active and start is not None:
            regions.append((start, index))
            start = None
    if start is not None:
        regions.append((start, len(mask)))
    result = []
    for left, right in regions:
        start_sec = left * hop_seconds
        end_sec = min(len(audio) / sample_rate, max(start_sec + hop_seconds, right * hop_seconds))
        sample_left = min(len(audio), int(start_sec * sample_rate))
        sample_right = min(len(audio), max(sample_left + 1, int(end_sec * sample_rate)))
        energy = float(np.sqrt(np.mean(np.square(audio[sample_left:sample_right])) + 1e-12))
        result.append(AudioSegment(start=start_sec, end=end_sec, energy=energy))
    return result


def merge_regions(regions: list[tuple[float, float]], gap_seconds: float = 0.2) -> list[tuple[float, float]]:
    if not regions:
        return []
    ordered = sorted((float(a), float(b)) for a, b in regions)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        old_start, old_end = merged[-1]
        if start <= old_end + gap_seconds:
            merged[-1] = (old_start, max(old_end, end))
        else:
            merged.append((start, end))
    return merged
