from echomind.pipeline.schemas import DecoderStats, TranscriptionResult, TranscriptionSegment
from echomind.uncertainty.detector import assess_transcription
from echomind.uncertainty.estimator import HeuristicUncertaintyEstimator


def test_raw_uncertainty_is_not_labelled_calibrated():
    result = TranscriptionResult(
        text="bonjour",
        language="fr",
        model_name="test",
        backend="mock",
        segments=[TranscriptionSegment(id=0, start=0, end=1, text="bonjour", decoder_stats=DecoderStats(avg_logprob=-2.0))],
    )
    assessments = assess_transcription(result)
    assert assessments[0].raw_score > 0
    assert assessments[0].calibrated_probability is None
    assert assessments[0].band in {"low", "medium", "high"}


def test_low_decoder_log_probability_reaches_redecode_band():
    result = TranscriptionResult(
        text="possibly wrong",
        language="en",
        model_name="test",
        backend="mock",
        segments=[
            TranscriptionSegment(
                id=0,
                start=0,
                end=1,
                text="possibly wrong",
                decoder_stats=DecoderStats(avg_logprob=-2.0),
            )
        ],
    )

    assessment = assess_transcription(result, estimator=HeuristicUncertaintyEstimator())[0]

    assert assessment.raw_score >= 0.30
    assert assessment.band == "high"
