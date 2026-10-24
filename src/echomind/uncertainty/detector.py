"""Segment-level uncertainty assessment."""

from __future__ import annotations

from echomind.pipeline.schemas import AudioMetadata, TranscriptionResult, UncertaintyAssessment
from echomind.uncertainty.estimator import HeuristicUncertaintyEstimator
from echomind.uncertainty.features import extract_features


def assess_transcription(
    result: TranscriptionResult,
    audio: AudioMetadata | None = None,
    context_text: str = "",
    estimator: HeuristicUncertaintyEstimator | None = None,
    calibrator=None,
) -> list[UncertaintyAssessment]:
    estimator = estimator or HeuristicUncertaintyEstimator()
    assessments = []
    for segment in result.segments:
        features = extract_features(segment, audio, context_text)
        score = estimator.score(features)
        calibrated = calibrator.predict(score.raw) if calibrator else None
        comparable = calibrated if calibrated is not None else score.raw
        band = "high" if comparable >= estimator.high else "medium" if comparable >= estimator.medium else "low"
        assessments.append(
            UncertaintyAssessment(
                segment_id=segment.id,
                raw_score=score.raw,
                calibrated_probability=calibrated,
                band=band,
                features=features,
                reasons=score.reasons,
            )
        )
    return assessments
