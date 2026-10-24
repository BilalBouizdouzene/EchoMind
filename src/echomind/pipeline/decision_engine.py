"""Decision policy wrapper."""

from echomind.nlp.clarification import choose_action
from echomind.pipeline.schemas import DecisionTrace, SemanticInterpretation, UncertaintyAssessment


def decide(assessments: list[UncertaintyAssessment], semantic: SemanticInterpretation, correction_enabled: bool) -> DecisionTrace:
    return choose_action(assessments, semantic, has_redecode_budget=correction_enabled)
