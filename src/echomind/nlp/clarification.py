"""Risk-sensitive clarification policy."""

from __future__ import annotations

from echomind.pipeline.schemas import (
    DecisionTrace,
    SemanticInterpretation,
    UncertaintyAssessment,
)


def choose_action(
    assessments: list[UncertaintyAssessment],
    semantic: SemanticInterpretation,
    has_redecode_budget: bool,
    max_latency_ms: float = 30000,
) -> DecisionTrace:
    has_high_risk = any(item.band == "high" for item in assessments)
    critical = bool(semantic.entities.get("date") or semantic.entities.get("time"))
    if semantic.ambiguities and critical:
        return DecisionTrace(action="CLARIFY", reasons=["critical entity remains semantically ambiguous"], critical_information=True)
    if has_high_risk and has_redecode_budget:
        return DecisionTrace(
            action="REDECODE",
            reasons=["segment-level uncertainty reached the selective re-decode threshold"],
            expected_latency_ms=min(max_latency_ms, 30000),
        )
    if semantic.self_correction.detected and semantic.self_correction.confidence >= 0.75:
        return DecisionTrace(action="ACCEPT", reasons=["speaker self-correction has an explicit final value"], critical_information=critical)
    return DecisionTrace(action="ACCEPT", reasons=["no unresolved high-risk ambiguity"], critical_information=critical)


def clarification_question(semantic: SemanticInterpretation) -> str | None:
    if not semantic.ambiguities:
        return None
    if any("cancellation" in item for item in semantic.ambiguities):
        return "Do you want to cancel the booking or change its date?"
    if semantic.entities.get("time") and len(semantic.entities["time"]) >= 2:
        return f"Did you mean {semantic.entities['time'][0]} or {semantic.entities['time'][-1]}?"
    if semantic.entities.get("date") and len(semantic.entities["date"]) >= 2:
        return f"Did you mean {semantic.entities['date'][0]} or {semantic.entities['date'][-1]}?"
    return "Could you clarify the information that should be used?"
