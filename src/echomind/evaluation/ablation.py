"""Run E0-E3 conditions with the same manifest."""

from __future__ import annotations

import time
from dataclasses import replace

from echomind.asr.whisper_engine import DecodingConfig, WhisperEngine
from echomind.evaluation.benchmark import run_benchmark
from echomind.pipeline.orchestrator import EchoMindPipeline, PipelineOptions


def run_ablation(manifest_path: str, base_options: PipelineOptions | None = None) -> dict:
    base_options = base_options or PipelineOptions()
    conditions = {
        "E0_baseline_asr": replace(base_options, enable_uncertainty=False, enable_selective_correction=False, enable_contextual_nlp=False),
        "E1_contextual_correction": replace(base_options, enable_uncertainty=False, enable_selective_correction=False, enable_contextual_nlp=True),
        "E2_selective_redecode": replace(base_options, enable_uncertainty=True, enable_selective_correction=True, enable_contextual_nlp=False),
        "E3_complete_echomind": replace(base_options, enable_uncertainty=True, enable_selective_correction=True, enable_contextual_nlp=True),
    }
    shared_engine = WhisperEngine(
        DecodingConfig(
            model_name=base_options.model_name,
            language=base_options.language_hint,
            beam_size=base_options.beam_size,
            cpu_threads=base_options.cpu_threads,
        )
    )
    load_started = time.perf_counter()
    try:
        shared_engine.load()
        model_loaded = True
    except RuntimeError:
        # Keep the normal benchmark's explicit ASR-unavailable result behavior.
        model_loaded = False
    model_load_ms = (time.perf_counter() - load_started) * 1000

    output = {}
    for name, options in conditions.items():
        pipeline = EchoMindPipeline(options=options, engine=shared_engine)
        report = run_benchmark(manifest_path, pipeline=pipeline)
        output[name] = {
            **report["metrics"],
            "model": base_options.model_name,
            "model_load_ms_excluded_from_condition_latency": model_load_ms,
            "model_loaded_before_conditions": model_loaded,
            "correction_examples": [
                row for row in report["rows"] if row.get("correction_applied")
            ],
        }
    return output
