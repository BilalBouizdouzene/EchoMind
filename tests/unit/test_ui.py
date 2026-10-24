from echomind.pipeline.schemas import (
    AudioMetadata,
    PipelineResult,
    TranscriptionResult,
    TranscriptionSegment,
    UncertaintyAssessment,
    UncertaintyFeatures,
)
from echomind.ui.components import timeline_html


def test_timeline_color_uses_assessed_band_not_old_hardcoded_threshold():
    result = PipelineResult(
        audio=AudioMetadata(sample_rate=16000, duration_seconds=1),
        baseline=TranscriptionResult(
            text="uncertain",
            model_name="test",
            backend="mock",
            segments=[TranscriptionSegment(id=0, start=0, end=1, text="uncertain")],
        ),
        uncertain_segments=[
            UncertaintyAssessment(
                segment_id=0,
                raw_score=0.35,
                band="high",
                features=UncertaintyFeatures(),
            )
        ],
    )

    rendered = timeline_html(result)

    assert "background:#fb7185" in rendered
    assert "high · raw risk 0.35" in rendered
