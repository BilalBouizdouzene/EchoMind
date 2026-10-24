from echomind.nlp.clarification import clarification_question
from echomind.nlp.contradiction_detection import detect_self_correction
from echomind.nlp.intent_extraction import extract_semantics
from echomind.nlp.language_detection import detect_languages
from echomind.pipeline.schemas import SemanticInterpretation


def test_self_correction_preserves_final_value():
    event = detect_self_correction("Schedule it for Thursday, no, Friday.")
    assert event.detected
    assert event.final_value is not None
    assert "Friday" in event.final_value


def test_arabic_french_code_switch_is_marked_experimental_mixed():
    languages, mode = detect_languages("Bonjour, أريد تغيير le rendez-vous")
    assert "fr" in languages
    assert "ar" in languages
    assert mode == "mixed"


def test_intent_extraction_is_grounded():
    semantic = extract_semantics("Bonjour, أريد تغيير le rendez-vous pour demain")
    assert semantic.intent == "appointment_rescheduling"
    assert semantic.entities["date"] == ["demain"]


def test_clarification_is_targeted_for_critical_intent_ambiguity():
    semantic = SemanticInterpretation(ambiguities=["cancellation versus booking-date modification remains unresolved"])
    assert clarification_question(semantic) == "Do you want to cancel the booking or change its date?"
