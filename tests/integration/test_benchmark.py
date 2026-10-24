import csv

from echomind.evaluation.benchmark import run_benchmark
from echomind.pipeline.schemas import (
    CorrectionRecord,
    DecoderStats,
    PipelineMetrics,
    PipelineResult,
    SemanticInterpretation,
    TranscriptionResult,
    TranscriptionSegment,
    UncertaintyAssessment,
    UncertaintyFeatures,
)


class StubPipeline:
    def process(self, source, context=""):
        return PipelineResult(
            original_transcript="hello world",
            final_transcript="hello brave world",
            baseline=TranscriptionResult(
                text="hello world",
                model_name="stub",
                backend="stub",
                segments=[
                    TranscriptionSegment(
                        id=0,
                        start=0,
                        end=1,
                        text="hello world",
                        decoder_stats=DecoderStats(avg_logprob=-0.3),
                    )
                ],
            ),
            uncertain_segments=[
                UncertaintyAssessment(
                    segment_id=0,
                    raw_score=0.8,
                    band="high",
                    features=UncertaintyFeatures(),
                )
            ],
            corrections=[
                CorrectionRecord(
                    segment_id=0,
                    original_text="hello world",
                    alternative_text="hello brave world",
                    region_start=0,
                    region_end=1,
                    decision="accepted_alternative",
                )
            ],
            semantic_interpretation=SemanticInterpretation(intent="unknown"),
            metrics=PipelineMetrics(total_latency_ms=12, real_time_factor=0.2, fraction_audio_redecoded=0.1),
            decision="REDECODE",
        )


def test_benchmark_reports_baseline_final_and_outcome(tmp_path):
    audio_path = tmp_path / "clip.wav"
    audio_path.write_bytes(b"stub")
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "audio_path", "reference_text", "language"])
        writer.writeheader()
        writer.writerow({"id": "1", "audio_path": "clip.wav", "reference_text": "hello brave world", "language": "en"})

    report = run_benchmark(manifest, pipeline=StubPipeline())

    row = report["rows"][0]
    assert row["baseline_wer"] > row["final_wer"]
    assert row["correction_outcome"] == "improved"
    assert report["metrics"]["improvement_rate_all"] == 1.0
    assert report["metrics"]["p50_latency_ms"] == 12
