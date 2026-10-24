import numpy as np

from echomind.asr.whisper_engine import DecodingConfig
from echomind.correction.acoustic_redecoder import RedecodeConfig, select_regions
from echomind.correction.candidate_generator import generate_candidates
from echomind.correction.correction_engine import resolve_correction
from echomind.pipeline.schemas import (
    Candidate,
    CorrectionRecord,
    TranscriptionResult,
    TranscriptionSegment,
    UncertaintyAssessment,
    UncertaintyFeatures,
)


class AgreeingDecoder:
    def transcribe(self, audio, sample_rate=16000, language_hint=None, config=None):
        return TranscriptionResult(
            text="nine",
            language="en",
            model_name="test",
            backend="mock",
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.6,
                    end=0.9,
                    text="nine",
                    words=[{"word": " nine", "start": 0.6, "end": 0.9, "probability": 0.9}],
                )
            ],
        )


def test_select_regions_obeys_budget():
    transcript = TranscriptionResult(
        text="one two",
        model_name="test",
        backend="mock",
        segments=[
            TranscriptionSegment(id=0, start=0, end=1, text="one"),
            TranscriptionSegment(id=1, start=3, end=4, text="two"),
        ],
    )
    assessments = [
        UncertaintyAssessment(segment_id=0, raw_score=0.9, band="high", features=UncertaintyFeatures()),
        UncertaintyAssessment(segment_id=1, raw_score=0.8, band="high", features=UncertaintyFeatures()),
    ]
    regions = select_regions(transcript, assessments, 10, RedecodeConfig(max_regions=1, max_fraction=0.2, context_seconds=0))
    assert len(regions) == 1
    assert regions[0][0] == 0


def test_select_regions_skips_region_that_exceeds_total_budget():
    transcript = TranscriptionResult(
        text="one",
        model_name="test",
        backend="mock",
        segments=[TranscriptionSegment(id=0, start=0, end=3, text="one")],
    )
    assessments = [
        UncertaintyAssessment(segment_id=0, raw_score=0.9, band="high", features=UncertaintyFeatures()),
    ]
    regions = select_regions(transcript, assessments, 3, RedecodeConfig(max_fraction=0.25, context_seconds=0))
    assert regions == []


def test_redecode_compares_two_configs_and_trims_context_to_target_segment():
    target = TranscriptionSegment(id=0, start=1, end=2, text="for")

    generated = generate_candidates(
        AgreeingDecoder(),
        np.zeros(4 * 16000, dtype=np.float32),
        16000,
        target,
        DecodingConfig(model_name="test"),
        decode_start=0.5,
        decode_end=2.5,
    )

    alternative = next(candidate for candidate in generated.candidates if candidate.source == "redecode")
    assert alternative.text == "nine"
    assert alternative.agreement_count == 2
    assert any("agree" in item for item in generated.reason)


def test_unconfirmed_alternative_is_not_accepted_without_context():
    record = CorrectionRecord(
        segment_id=0,
        original_text="four",
        alternative_text="five",
        region_start=0,
        region_end=1,
        decision="unresolved",
    )
    candidates = [
        Candidate(text="four", start=0, end=1, source="baseline", mean_word_probability=0.60),
        Candidate(text="five", start=0, end=1, source="redecode", agreement_count=1),
    ]

    resolved, final = resolve_correction(record, candidates)

    assert resolved.decision == "kept_original"
    assert final == "four"
    assert any("did not clear" in item for item in resolved.confidence_evidence)


def test_independently_agreed_alternative_is_accepted_with_provenance():
    record = CorrectionRecord(
        segment_id=0,
        original_text="four",
        alternative_text="five",
        region_start=0,
        region_end=1,
        decision="unresolved",
    )
    candidates = [
        Candidate(text="four", start=0, end=1, source="baseline", mean_word_probability=0.60),
        Candidate(
            text="five",
            start=0,
            end=1,
            source="redecode",
            score=0.20,
            agreement_count=2,
            mean_word_probability=0.85,
            evidence=["two alternative decoding configurations agree on this alternative"],
        ),
    ]

    resolved, final = resolve_correction(record, candidates)

    assert resolved.decision == "accepted_alternative"
    assert final == "five"
    assert any("target-region word confidence improved" in item for item in resolved.confidence_evidence)


def test_consensus_alternative_with_lower_word_confidence_is_rejected():
    record = CorrectionRecord(
        segment_id=0,
        original_text="four",
        alternative_text="five",
        region_start=0,
        region_end=1,
        decision="unresolved",
    )
    candidates = [
        Candidate(text="four", start=0, end=1, source="baseline", mean_word_probability=0.65),
        Candidate(
            text="five",
            start=0,
            end=1,
            source="redecode",
            score=0.20,
            agreement_count=2,
            mean_word_probability=0.55,
        ),
    ]

    resolved, final = resolve_correction(record, candidates)

    assert resolved.decision == "kept_original"
    assert final == "four"
