"""Benchmark runner for local CSV/JSONL corpora."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from echomind.evaluation.dataset import validate_manifest
from echomind.evaluation.metrics import (
    cer,
    classification_accuracy,
    corpus_cer,
    corpus_wer,
    correction_outcome,
    correction_summary,
    error_detection_metrics,
    mean,
    normalized_cer,
    normalized_wer,
    percentile,
    sentence_error_rate,
    wer,
)
from echomind.evaluation.text_normalization import NORMALIZATION_MODE, normalize_for_evaluation
from echomind.pipeline.orchestrator import EchoMindPipeline
from echomind.uncertainty.calibration import brier_score, expected_calibration_error


def load_manifest(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _resolve_audio_path(audio_path: str, manifest_path: Path) -> Path:
    path = Path(audio_path)
    if not path.is_absolute():
        # Prefer the repository working directory for manifests that already
        # contain repo-relative paths, then fall back to manifest-relative paths.
        candidates = [Path.cwd() / path, manifest_path.parent / path]
        path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    return path.resolve()


def _as_bool(value: object) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "oui"}


def _group_summary(rows: list[dict], field: str) -> dict[str, dict[str, float | int | None]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = str(row.get(field) or "unknown")
        groups.setdefault(key, []).append(row)
    return {key: _summarize_rows(group) for key, group in sorted(groups.items())}


def _summarize_rows(rows: list[dict]) -> dict[str, float | int | None]:
    outcomes = [row["correction_outcome"] for row in rows]
    summary = correction_summary(outcomes)
    references = [str(row.get("reference_text") or "") for row in rows]
    baseline_hypotheses = [str(row.get("baseline_hypothesis") or "") for row in rows]
    final_hypotheses = [str(row.get("hypothesis") or "") for row in rows]
    normalized_references = [normalize_for_evaluation(item) for item in references]
    normalized_baseline = [normalize_for_evaluation(item) for item in baseline_hypotheses]
    normalized_final = [normalize_for_evaluation(item) for item in final_hypotheses]
    summary.update({
        "evaluated_examples": len(rows),
        "baseline_wer": corpus_wer(references, baseline_hypotheses),
        "final_wer": corpus_wer(references, final_hypotheses),
        "baseline_cer": corpus_cer(references, baseline_hypotheses),
        "final_cer": corpus_cer(references, final_hypotheses),
        "baseline_wer_normalized": corpus_wer(normalized_references, normalized_baseline),
        "final_wer_normalized": corpus_wer(normalized_references, normalized_final),
        "baseline_cer_normalized": corpus_cer(normalized_references, normalized_baseline),
        "final_cer_normalized": corpus_cer(normalized_references, normalized_final),
        "baseline_wer_macro": mean(row.get("baseline_wer") for row in rows),
        "final_wer_macro": mean(row.get("final_wer") for row in rows),
        "baseline_cer_macro": mean(row.get("baseline_cer") for row in rows),
        "final_cer_macro": mean(row.get("final_cer") for row in rows),
        "baseline_wer_normalized_macro": mean(row.get("baseline_wer_normalized") for row in rows),
        "final_wer_normalized_macro": mean(row.get("final_wer_normalized") for row in rows),
        "baseline_cer_normalized_macro": mean(row.get("baseline_cer_normalized") for row in rows),
        "final_cer_normalized_macro": mean(row.get("final_cer_normalized") for row in rows),
        "mean_latency_ms": mean(row.get("latency_ms") for row in rows),
        "p50_latency_ms": percentile((row.get("latency_ms") for row in rows), 50),
        "p95_latency_ms": percentile((row.get("latency_ms") for row in rows), 95),
        "mean_real_time_factor": mean(row.get("real_time_factor") for row in rows),
        "mean_fraction_audio_redecoded": mean(row.get("fraction_audio_redecoded") for row in rows),
    })
    return summary


def run_benchmark(manifest_path: str | Path, pipeline: EchoMindPipeline | None = None) -> dict:
    manifest_path = Path(manifest_path).resolve()
    pipeline = pipeline or EchoMindPipeline()
    rows = load_manifest(manifest_path)
    errors = validate_manifest(rows, check_files=True, base_dir=manifest_path.parent)
    if errors:
        raise ValueError("Invalid evaluation manifest:\n" + "\n".join(errors[:20]))
    results = []
    for row in rows:
        audio_path = _resolve_audio_path(row["audio_path"], manifest_path)
        output = pipeline.process(audio_path, context=row.get("context", ""))
        reference = row.get("reference_text", "")
        baseline_text = output.original_transcript
        asr_unavailable = bool(output.baseline and not baseline_text.strip() and output.baseline.warnings)
        reference_available = bool(str(reference).strip()) and not asr_unavailable
        baseline_wer = wer(reference, baseline_text) if reference_available else None
        final_wer = wer(reference, output.final_transcript) if reference_available else None
        baseline_cer = cer(reference, baseline_text) if reference_available else None
        final_cer = cer(reference, output.final_transcript) if reference_available else None
        baseline_wer_normalized = (
            normalized_wer(reference, baseline_text) if reference_available else None
        )
        final_wer_normalized = (
            normalized_wer(reference, output.final_transcript) if reference_available else None
        )
        baseline_cer_normalized = (
            normalized_cer(reference, baseline_text) if reference_available else None
        )
        final_cer_normalized = (
            normalized_cer(reference, output.final_transcript) if reference_available else None
        )
        applied = baseline_text.strip() != output.final_transcript.strip()
        outcome = (
            correction_outcome(baseline_wer_normalized, final_wer_normalized, applied)
            if reference_available
            else "not_measured"
        )
        uncertainty_score = max((item.raw_score for item in output.uncertain_segments), default=0.0)
        results.append({
            "id": row.get("id", row["audio_path"]),
            "language": row.get("language", "unknown"),
            "speaker_id": row.get("speaker_id", "unknown"),
            "condition": row.get("condition", "unknown"),
            "source_dataset": row.get("source_dataset", "unknown"),
            "reference_text": reference,
            "baseline_hypothesis": baseline_text,
            "hypothesis": output.final_transcript,
            "baseline_wer": baseline_wer,
            "final_wer": final_wer,
            "wer": final_wer,
            "baseline_cer": baseline_cer,
            "final_cer": final_cer,
            "cer": final_cer,
            "baseline_wer_normalized": baseline_wer_normalized,
            "final_wer_normalized": final_wer_normalized,
            "wer_normalized": final_wer_normalized,
            "baseline_cer_normalized": baseline_cer_normalized,
            "final_cer_normalized": final_cer_normalized,
            "cer_normalized": final_cer_normalized,
            "correction_applied": applied,
            "correction_outcome": outcome,
            "correction_count": len(output.corrections),
            "corrections": [item.model_dump(mode="json") for item in output.corrections],
            "decision_trace": output.decision_trace.model_dump(mode="json"),
            "uncertainty_score": uncertainty_score,
            "latency_ms": output.metrics.total_latency_ms,
            "real_time_factor": output.metrics.real_time_factor,
            "fraction_audio_redecoded": output.metrics.fraction_audio_redecoded,
            "decision": output.decision,
            "backend": output.baseline.backend if output.baseline else "unavailable",
            "model": output.baseline.model_name if output.baseline else None,
            "evaluation_status": (
                "measured"
                if reference_available
                else "not_measured_asr_unavailable"
                if asr_unavailable
                else "not_measured_missing_reference"
            ),
            "warnings": output.warnings,
            "intent_reference": row.get("intent") or None,
            "intent_prediction": output.semantic_interpretation.intent,
            "self_correction_reference": _as_bool(row.get("self_correction")),
            "self_correction_prediction": output.semantic_interpretation.self_correction.detected,
        })
    measured = [result for result in results if result["final_wer"] is not None]
    references = [result["reference_text"] for result in measured]
    hypotheses = [result["hypothesis"] for result in measured]
    normalized_references = [normalize_for_evaluation(item) for item in references]
    normalized_hypotheses = [normalize_for_evaluation(item) for item in hypotheses]
    intent_rows = [result for result in results if result["intent_reference"]]
    self_correction_rows = [result for result in results if result["self_correction_reference"] is not None]
    detection_labels = [int((item["baseline_wer"] or 0.0) > 0) for item in measured]
    detection_scores = [item["uncertainty_score"] for item in measured]
    summary = _summarize_rows(measured) if measured else {
        **correction_summary([]),
        "evaluated_examples": len(results),
        "baseline_wer": None,
        "final_wer": None,
        "baseline_cer": None,
        "final_cer": None,
        "mean_latency_ms": mean(item.get("latency_ms") for item in results),
        "p50_latency_ms": percentile((item.get("latency_ms") for item in results), 50),
        "p95_latency_ms": percentile((item.get("latency_ms") for item in results), 95),
        "mean_real_time_factor": mean(item.get("real_time_factor") for item in results),
        "mean_fraction_audio_redecoded": mean(item.get("fraction_audio_redecoded") for item in results),
    }
    summary.update({
        "sentence_error_rate": sentence_error_rate(references, hypotheses) if measured else None,
        "sentence_error_rate_normalized": (
            sentence_error_rate(normalized_references, normalized_hypotheses) if measured else None
        ),
        "wer": summary["final_wer"],
        "cer": summary["final_cer"],
        "wer_normalized": summary["final_wer_normalized"],
        "cer_normalized": summary["final_cer_normalized"],
        "intent_accuracy": classification_accuracy(
            [item["intent_reference"] for item in intent_rows],
            [item["intent_prediction"] for item in intent_rows],
        ) if intent_rows else None,
        "self_correction_accuracy": classification_accuracy(
            [str(item["self_correction_reference"]) for item in self_correction_rows],
            [str(item["self_correction_prediction"]) for item in self_correction_rows],
        ) if self_correction_rows else None,
        "error_detection": error_detection_metrics(detection_labels, detection_scores) if measured else None,
        "raw_score_calibration": {
            "ece": expected_calibration_error(detection_scores, detection_labels) if measured else None,
            "brier": brier_score(detection_scores, detection_labels) if measured else None,
            "note": "These scores evaluate the raw uncertainty heuristic; they are not calibrated probabilities.",
        },
        "groups": {
            "language": _group_summary(measured, "language") if measured else {},
            "condition": _group_summary(measured, "condition") if measured else {},
        },
        "normalization": {
            "mode": NORMALIZATION_MODE,
            "note": "WER/CER are corpus micro-averages over reference words/characters; *_macro fields are arithmetic means over utterances.",
        },
    })
    return {
        "evaluated_examples": len(results),
        "manifest": str(manifest_path),
        "model": getattr(getattr(pipeline, "options", None), "model_name", None),
        "metrics": {**summary, "note": "Metrics are measured from the supplied manifest; missing labels remain null."},
        "rows": results,
    }
