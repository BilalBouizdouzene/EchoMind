"""End-to-end EchoMind pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from echomind.asr.whisper_engine import DecodingConfig, WhisperEngine
from echomind.audio.loader import load_audio
from echomind.audio.preprocessing import preprocess_audio
from echomind.correction.acoustic_redecoder import RedecodeConfig, redecode_regions
from echomind.correction.correction_engine import resolve_correction
from echomind.nlp.clarification import clarification_question
from echomind.nlp.contradiction_detection import contradiction_reasons, detect_self_correction
from echomind.nlp.intent_extraction import extract_semantics
from echomind.pipeline.decision_engine import decide
from echomind.pipeline.schemas import DecisionTrace, PipelineMetrics, PipelineResult
from echomind.uncertainty.detector import assess_transcription


@dataclass
class PipelineOptions:
    model_name: str = "tiny"
    language_hint: str | None = None
    enable_uncertainty: bool = True
    enable_selective_correction: bool = True
    enable_contextual_nlp: bool = True
    max_redecode_regions: int = 2
    max_redecode_fraction: float = 0.25
    cpu_threads: int = 4
    max_audio_seconds: float = 180.0
    max_audio_bytes: int = 16 * 1024 * 1024
    beam_size: int = 1
    vocabulary: list[str] = field(default_factory=list)


class EchoMindPipeline:
    def __init__(self, options: PipelineOptions | None = None, engine: WhisperEngine | None = None) -> None:
        self.options = options or PipelineOptions()
        self.engine = engine or WhisperEngine(
            DecodingConfig(
                model_name=self.options.model_name,
                language=self.options.language_hint,
                beam_size=self.options.beam_size,
                cpu_threads=self.options.cpu_threads,
            )
        )

    def process(self, source, context: str = "") -> PipelineResult:
        started = time.perf_counter()
        warnings: list[str] = []
        try:
            raw_audio, source_rate, _ = load_audio(
                source,
                max_bytes=self.options.max_audio_bytes,
                max_duration_seconds=self.options.max_audio_seconds,
            )
            audio, metadata = preprocess_audio(raw_audio, source_rate)
        except Exception as error:
            return PipelineResult(warnings=[f"Audio preprocessing failed: {error}"], provenance=["pipeline stopped before ASR"])
        if metadata.duration_seconds <= 0.01:
            return PipelineResult(audio=metadata, warnings=["Audio is empty or too short"], provenance=["empty audio guard"])
        baseline = self.engine.transcribe(audio, sample_rate=metadata.sample_rate, language_hint=self.options.language_hint)
        warnings.extend(baseline.warnings)
        original = baseline.text.strip()
        if not original:
            total_ms = (time.perf_counter() - started) * 1000
            if not warnings:
                warnings.append("No speech transcript was produced; check the recording and microphone level.")
            trace = DecisionTrace(
                action="CLARIFY",
                reasons=["no transcript was produced; the input cannot be accepted as analyzed"],
            )
            return PipelineResult(
                language=baseline.language,
                audio=metadata,
                baseline=baseline,
                decision=trace.action,
                decision_trace=trace,
                clarification_question=(
                    "I couldn't detect clear speech. Please check the recording and try again."
                    if not baseline.warnings else None
                ),
                metrics=PipelineMetrics(
                    asr_latency_ms=baseline.latency_ms,
                    total_latency_ms=total_ms,
                    real_time_factor=total_ms / 1000 / metadata.duration_seconds if metadata.duration_seconds else None,
                ),
                warnings=warnings,
                provenance=["audio kept local", "ASR returned no transcript"],
            )
        uncertain = assess_transcription(baseline, metadata, context) if self.options.enable_uncertainty else []
        semantic = extract_semantics(original) if self.options.enable_contextual_nlp else extract_semantics("")
        semantic = semantic.model_copy(update={
            "self_correction": detect_self_correction(original),
            "contradictions": contradiction_reasons(original),
        })
        if semantic.intent == "booking_cancellation" and semantic.self_correction.detected:
            semantic = semantic.model_copy(update={
                "ambiguities": ["cancellation versus booking-date modification remains unresolved"],
                "grounding_notes": [*semantic.grounding_notes, "critical intent ambiguity requires user confirmation"],
            })
        trace = decide(uncertain, semantic, self.options.enable_selective_correction)
        corrections = []
        segment_replacements: dict[int, str] = {}
        final_text = original
        correction_latency = 0.0
        if self.options.enable_selective_correction and trace.action == "REDECODE" and baseline.segments:
            records, candidates, correction_latency = redecode_regions(
                self.engine,
                audio,
                metadata.sample_rate,
                baseline,
                uncertain,
                metadata.duration_seconds,
                self.engine.config,
                RedecodeConfig(
                    max_regions=self.options.max_redecode_regions,
                    max_fraction=self.options.max_redecode_fraction,
                ),
            )
            for record in records:
                local_candidates = [item for item in candidates if item.start <= record.region_end and item.end >= record.region_start]
                resolved, replacement = resolve_correction(
                    record,
                    local_candidates,
                    context=context,
                    vocabulary=self.options.vocabulary,
                )
                corrections.append(resolved)
                if resolved.decision == "accepted_alternative":
                    segment_replacements[resolved.segment_id] = replacement
            if segment_replacements:
                final_text = " ".join(
                    segment_replacements.get(segment.id, segment.text).strip()
                    for segment in baseline.segments
                ).strip()
            if not corrections:
                trace = trace.model_copy(update={"action": "ACCEPT", "reasons": ["no bounded region met the re-decode budget"]})
            elif not segment_replacements:
                trace = trace.model_copy(
                    update={"action": "ACCEPT", "reasons": ["no alternative met the evidence threshold; original transcript retained"]}
                )
        if semantic.ambiguities:
            trace = trace.model_copy(update={"action": "CLARIFY"})
        clarification = clarification_question(semantic) if trace.action == "CLARIFY" else None
        total_ms = (time.perf_counter() - started) * 1000
        rtf = total_ms / 1000 / metadata.duration_seconds if metadata.duration_seconds else None
        fraction = sum(item.region_end - item.region_start for item in corrections) / max(0.001, metadata.duration_seconds)
        return PipelineResult(
            language=baseline.language,
            original_transcript=original,
            final_transcript=final_text,
            audio=metadata,
            baseline=baseline,
            uncertain_segments=uncertain,
            corrections=corrections,
            semantic_interpretation=semantic,
            decision=trace.action,
            decision_trace=trace,
            clarification_question=clarification,
            metrics=PipelineMetrics(
                asr_latency_ms=baseline.latency_ms,
                correction_latency_ms=correction_latency,
                total_latency_ms=total_ms,
                fraction_audio_redecoded=min(1.0, fraction) if corrections else 0.0,
                real_time_factor=rtf,
            ),
            warnings=warnings,
            provenance=[
                "audio kept local",
                "baseline transcript preserved",
                "raw heuristic scores are not calibrated probabilities",
            ],
        )
