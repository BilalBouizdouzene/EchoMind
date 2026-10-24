import numpy as np
import soundfile as sf

from echomind.asr.whisper_engine import DecodingConfig
from echomind.pipeline.orchestrator import EchoMindPipeline, PipelineOptions
from echomind.pipeline.schemas import DecoderStats, TranscriptionResult, TranscriptionSegment


class FakeEngine:
    config = DecodingConfig(model_name="fake")

    def transcribe(self, audio, sample_rate=16000, language_hint=None, config=None):
        return TranscriptionResult(
            text="Schedule it for Thursday, no, Friday.",
            language="en",
            model_name="fake",
            backend="mock",
            segments=[TranscriptionSegment(id=0, start=0, end=0.5, text="Schedule it for Thursday, no, Friday.", decoder_stats=DecoderStats(avg_logprob=-0.2))],
        )


def test_pipeline_produces_structured_result(tmp_path):
    path = tmp_path / "sample.wav"
    sf.write(path, np.zeros(16000, dtype=np.float32), 16000)
    result = EchoMindPipeline(PipelineOptions(enable_selective_correction=False), engine=FakeEngine()).process(path)
    assert result.audio is not None
    assert result.original_transcript.startswith("Schedule")
    assert result.semantic_interpretation.self_correction.detected
    assert result.model_dump(mode="json")["decision"] in {"ACCEPT", "REDECODE", "CLARIFY"}


class SelectiveFakeEngine:
    config = DecodingConfig(model_name="fake")

    def transcribe(self, audio, sample_rate=16000, language_hint=None, config=None):
        if config is None:
            return TranscriptionResult(
                text="repeat phrase repeat phrase",
                language="en",
                model_name="fake",
                backend="mock",
                segments=[
                    TranscriptionSegment(
                        id=0,
                        start=0.5,
                        end=1.5,
                        text="repeat phrase",
                        decoder_stats=DecoderStats(avg_logprob=-0.1),
                        words=[
                            {"word": " repeat", "start": 0.5, "end": 0.9, "probability": 0.95},
                            {"word": " phrase", "start": 0.9, "end": 1.3, "probability": 0.95},
                        ],
                    ),
                    TranscriptionSegment(
                        id=1,
                        start=2.5,
                        end=3.5,
                        text="repeat phrase",
                        decoder_stats=DecoderStats(avg_logprob=-2.0),
                        words=[
                            {"word": " repeat", "start": 2.5, "end": 2.9, "probability": 0.20},
                            {"word": " phrase", "start": 2.9, "end": 3.3, "probability": 0.20},
                        ],
                    ),
                ],
            )
        return TranscriptionResult(
            text="correct phrase",
            language="en",
            model_name="fake",
            backend="mock",
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=1.0,
                    end=1.7,
                    text="correct phrase",
                    words=[
                        {"word": " correct", "start": 1.0, "end": 1.3, "probability": 0.95},
                        {"word": " phrase", "start": 1.3, "end": 1.7, "probability": 0.95},
                    ],
                )
            ],
        )


def test_pipeline_applies_grounded_correction_to_the_selected_segment_only(tmp_path):
    path = tmp_path / "repeated.wav"
    sf.write(path, np.zeros(4 * 16000, dtype=np.float32), 16000)

    result = EchoMindPipeline(
        PipelineOptions(
            enable_contextual_nlp=False,
            max_redecode_regions=1,
            max_redecode_fraction=1.0,
        ),
        engine=SelectiveFakeEngine(),
    ).process(path)

    assert result.original_transcript == "repeat phrase repeat phrase"
    assert result.final_transcript == "repeat phrase correct phrase"
    assert len(result.corrections) == 1
    assert result.corrections[0].segment_id == 1
    assert result.corrections[0].decision == "accepted_alternative"
    assert result.metrics.fraction_audio_redecoded > 0
