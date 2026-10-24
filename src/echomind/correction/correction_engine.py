"""Apply only provenance-backed candidate decisions."""

from __future__ import annotations

from echomind.correction.contextual_reranker import accept_alternative, rerank_candidates
from echomind.pipeline.schemas import Candidate, CorrectionRecord


def resolve_correction(
    record: CorrectionRecord,
    candidates: list[Candidate],
    context: str = "",
    vocabulary: list[str] | None = None,
) -> tuple[CorrectionRecord, str]:
    baseline = next((item for item in candidates if item.source == "baseline"), None)
    if baseline is None:
        return record.model_copy(update={"decision": "unresolved"}), record.original_text
    selected = rerank_candidates(candidates, context=context, vocabulary=vocabulary)
    if selected and accept_alternative(baseline, selected):
        confidence_improved = (
            baseline.mean_word_probability is not None
            and selected.mean_word_probability is not None
            and selected.mean_word_probability >= baseline.mean_word_probability + 0.05
        )
        rationale = (
            "accepted because two alternative decodes agreed and target-region word confidence improved"
            if selected.agreement_count >= 2 and confidence_improved
            else "accepted because verified context materially supported the alternative"
        )
        return record.model_copy(
            update={
                "alternative_text": selected.text,
                "decision": "accepted_alternative",
                "confidence_evidence": [*record.confidence_evidence, *selected.evidence, rationale],
            }
        ), selected.text
    has_alternative = any(item.source != "baseline" for item in candidates)
    rationale = (
        "alternative did not clear the consensus, confidence, or grounding gate; original retained"
        if has_alternative
        else "no usable alternative was produced; original retained"
    )
    return record.model_copy(
        update={
            "alternative_text": selected.text if selected and selected.source != "baseline" else record.alternative_text,
            "decision": "kept_original",
            "confidence_evidence": [*record.confidence_evidence, rationale],
        }
    ), record.original_text
