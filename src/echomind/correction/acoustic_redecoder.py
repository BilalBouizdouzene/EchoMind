"""Budget-constrained region selection and local re-decoding."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from echomind.asr.whisper_engine import DecodingConfig, WhisperEngine
from echomind.correction.candidate_generator import generate_candidates
from echomind.pipeline.schemas import (
    Candidate,
    CorrectionRecord,
    TranscriptionResult,
    UncertaintyAssessment,
)


@dataclass
class RedecodeConfig:
    max_regions: int = 2
    max_fraction: float = 0.25
    context_seconds: float = 1.0


def select_regions(
    transcription: TranscriptionResult,
    assessments: list[UncertaintyAssessment],
    duration_seconds: float,
    config: RedecodeConfig | None = None,
) -> list[tuple[int, float, float]]:
    config = config or RedecodeConfig()
    by_id = {assessment.segment_id: assessment for assessment in assessments}
    eligible = [
        segment for segment in transcription.segments
        if by_id.get(segment.id) and by_id[segment.id].band == "high"
    ]
    eligible.sort(key=lambda segment: by_id[segment.id].raw_score, reverse=True)
    budget = max(0.0, duration_seconds * config.max_fraction)
    picked: list[tuple[int, float, float]] = []
    picked_intervals: list[tuple[float, float]] = []
    spent = 0.0
    for segment in eligible:
        if len(picked) >= config.max_regions:
            break
        start = max(0.0, segment.start - config.context_seconds)
        end = min(duration_seconds, segment.end + config.context_seconds)
        cost = end - start
        overlaps_selected = any(start < picked_end and end > picked_start for picked_start, picked_end in picked_intervals)
        if cost <= 0 or cost > budget or spent + cost > budget or overlaps_selected:
            continue
        picked.append((segment.id, start, end))
        picked_intervals.append((start, end))
        spent += cost
    return picked


def redecode_regions(
    engine: WhisperEngine,
    audio: np.ndarray,
    sample_rate: int,
    transcription: TranscriptionResult,
    assessments: list[UncertaintyAssessment],
    duration_seconds: float,
    base_config: DecodingConfig,
    config: RedecodeConfig | None = None,
) -> tuple[list[CorrectionRecord], list[Candidate], float]:
    started = time.perf_counter()
    config = config or RedecodeConfig()
    selected = select_regions(transcription, assessments, duration_seconds, config)
    records: list[CorrectionRecord] = []
    all_candidates: list[Candidate] = []
    for segment_id, start, end in selected:
        segment = next((item for item in transcription.segments if item.id == segment_id), None)
        if segment is None:
            continue
        generated = generate_candidates(
            engine,
            audio,
            sample_rate,
            segment,
            base_config,
            decode_start=start,
            decode_end=end,
        )
        all_candidates.extend(generated.candidates)
        records.append(
            CorrectionRecord(
                segment_id=segment_id,
                original_text=segment.text,
                alternative_text=next((c.text for c in generated.candidates if c.source == "redecode"), None),
                region_start=start,
                region_end=end,
                reason=generated.reason,
                confidence_evidence=[
                    *[
                        assessment_reason
                        for item in assessments
                        if item.segment_id == segment_id
                        for assessment_reason in item.reasons
                    ],
                    *generated.reason,
                ],
                decision="unresolved",
                additional_latency_ms=0.0,
            )
        )
    latency = (time.perf_counter() - started) * 1000
    for record in records:
        record.additional_latency_ms = latency / max(1, len(records))
    return records, all_candidates, latency
