"""Validated, serialisable data contracts shared by every pipeline stage."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DecisionAction = Literal["ACCEPT", "REDECODE", "CLARIFY"]


class EchoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AudioSegment(EchoModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    kind: Literal["speech", "silence"] = "speech"
    energy: float = Field(default=0.0, ge=0)


class AudioQuality(EchoModel):
    rms: float = Field(default=0.0, ge=0)
    peak: float = Field(default=0.0, ge=0)
    clipping_ratio: float = Field(default=0.0, ge=0, le=1)
    silence_ratio: float = Field(default=1.0, ge=0, le=1)
    estimated_snr_db: float | None = None
    quality_label: Literal["good", "fair", "poor", "unknown"] = "unknown"
    notes: list[str] = Field(default_factory=list)


class AudioMetadata(EchoModel):
    sample_rate: int = Field(gt=0)
    channels: int = Field(default=1, gt=0)
    duration_seconds: float = Field(default=0.0, ge=0)
    speech_duration_seconds: float = Field(default=0.0, ge=0)
    segments: list[AudioSegment] = Field(default_factory=list)
    quality: AudioQuality = Field(default_factory=AudioQuality)
    processing_time_ms: float = Field(default=0.0, ge=0)


class DecoderStats(EchoModel):
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    compression_ratio: float | None = None
    beam_size: int | None = None
    temperature: float | None = None
    source: str = "unavailable"
    warnings: list[str] = Field(default_factory=list)


class TranscriptionSegment(EchoModel):
    id: int = 0
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str
    language: str | None = None
    decoder_stats: DecoderStats = Field(default_factory=DecoderStats)
    words: list[dict[str, Any]] | None = None


class TranscriptionResult(EchoModel):
    text: str = ""
    language: str | None = None
    language_probability: float | None = None
    segments: list[TranscriptionSegment] = Field(default_factory=list)
    model_name: str
    backend: str
    latency_ms: float = Field(default=0.0, ge=0)
    warnings: list[str] = Field(default_factory=list)


class UncertaintyFeatures(EchoModel):
    duration: float = 0.0
    rms: float = 0.0
    clipping_ratio: float = 0.0
    silence_proximity: float = 0.0
    avg_logprob: float | None = None
    mean_word_probability: float | None = Field(default=None, ge=0, le=1)
    low_word_probability_ratio: float = Field(default=0.0, ge=0, le=1)
    no_speech_prob: float | None = None
    compression_ratio: float | None = None
    text_instability: float = 0.0
    language_switch: float = 0.0
    semantic_inconsistency: float = 0.0


class UncertaintyAssessment(EchoModel):
    segment_id: int
    raw_score: float = Field(ge=0, le=1)
    calibrated_probability: float | None = Field(default=None, ge=0, le=1)
    band: Literal["low", "medium", "high"]
    features: UncertaintyFeatures
    reasons: list[str] = Field(default_factory=list)


class Candidate(EchoModel):
    text: str
    start: float
    end: float
    source: Literal["baseline", "redecode", "rule"]
    score: float = 0.0
    agreement_count: int = Field(default=1, ge=1)
    mean_word_probability: float | None = Field(default=None, ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class CorrectionRecord(EchoModel):
    segment_id: int
    original_text: str
    alternative_text: str | None = None
    region_start: float
    region_end: float
    reason: list[str] = Field(default_factory=list)
    confidence_evidence: list[str] = Field(default_factory=list)
    decision: Literal["kept_original", "accepted_alternative", "unresolved"]
    additional_latency_ms: float = 0.0


class SelfCorrectionEvent(EchoModel):
    detected: bool = False
    marker: str | None = None
    replaced_value: str | None = None
    final_value: str | None = None
    category: Literal["date", "time", "entity", "intent", "generic", "none"] = "none"
    confidence: float = 0.0


class SemanticInterpretation(EchoModel):
    intent: str = "unknown"
    intent_confidence: float = 0.0
    entities: dict[str, list[str]] = Field(default_factory=dict)
    possible_languages: list[str] = Field(default_factory=list)
    code_switching: Literal["no", "possible", "mixed", "unknown"] = "unknown"
    self_correction: SelfCorrectionEvent = Field(default_factory=SelfCorrectionEvent)
    contradictions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    grounding_notes: list[str] = Field(default_factory=list)


class DecisionTrace(EchoModel):
    action: DecisionAction
    reasons: list[str] = Field(default_factory=list)
    expected_latency_ms: float = 0.0
    critical_information: bool = False


class PipelineMetrics(EchoModel):
    asr_latency_ms: float = 0.0
    correction_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    fraction_audio_redecoded: float = 0.0
    real_time_factor: float | None = None


class PipelineResult(EchoModel):
    language: str | None = None
    original_transcript: str = ""
    final_transcript: str = ""
    audio: AudioMetadata | None = None
    baseline: TranscriptionResult | None = None
    uncertain_segments: list[UncertaintyAssessment] = Field(default_factory=list)
    corrections: list[CorrectionRecord] = Field(default_factory=list)
    semantic_interpretation: SemanticInterpretation = Field(default_factory=SemanticInterpretation)
    decision: DecisionAction = "ACCEPT"
    decision_trace: DecisionTrace = Field(default_factory=lambda: DecisionTrace(action="ACCEPT"))
    clarification_question: str | None = None
    metrics: PipelineMetrics = Field(default_factory=PipelineMetrics)
    warnings: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
