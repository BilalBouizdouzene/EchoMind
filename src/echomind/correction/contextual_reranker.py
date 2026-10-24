"""Grounded reranking: compare candidates, never synthesize a new transcript."""

from __future__ import annotations

import re

from echomind.pipeline.schemas import Candidate


def rerank_candidates(
    candidates: list[Candidate],
    context: str = "",
    vocabulary: list[str] | None = None,
) -> Candidate | None:
    if not candidates:
        return None
    vocabulary = [word.lower() for word in (vocabulary or [])]
    context_words = set(re.findall(r"[\wÀ-ÿ']+", context.lower()))
    scored: list[Candidate] = []
    for candidate in candidates:
        words = set(re.findall(r"[\wÀ-ÿ']+", candidate.text.lower()))
        overlap = len(words & context_words) / max(1, len(words)) if context_words else 0.0
        candidate_tokens = set(re.findall(r"[\wÀ-ÿ']+", candidate.text.lower()))
        vocab = sum(
            bool(set(re.findall(r"[\wÀ-ÿ']+", term)) & candidate_tokens)
            for term in vocabulary
        ) / max(1, len(vocabulary))
        length_penalty = 0.15 if len(candidate.text.strip()) < 2 else 0.0
        grounding = overlap * 0.25 + vocab * 0.10 - length_penalty
        evidence = list(candidate.evidence)
        if overlap:
            evidence.append(f"context token overlap={overlap:.2f}")
        if vocab:
            evidence.append("verified domain vocabulary overlap")
        scored.append(candidate.model_copy(update={"score": candidate.score + grounding, "evidence": evidence}))
    return max(scored, key=lambda item: item.score)


def accept_alternative(original: Candidate, selected: Candidate, minimum_margin: float = 0.10) -> bool:
    """Require independent acoustic agreement or a material grounding margin."""
    confidence_improved = (
        original.mean_word_probability is not None
        and selected.mean_word_probability is not None
        and selected.mean_word_probability >= original.mean_word_probability + 0.05
    )
    has_acoustic_support = selected.agreement_count >= 2 and confidence_improved
    has_grounding = any(
        evidence.startswith("context token overlap=")
        or evidence == "verified domain vocabulary overlap"
        for evidence in selected.evidence
    ) and selected.score - original.score >= minimum_margin
    return (
        selected.source != "baseline"
        and (has_acoustic_support or has_grounding)
        and selected.score - original.score >= minimum_margin
        and bool(selected.text.strip())
    )
