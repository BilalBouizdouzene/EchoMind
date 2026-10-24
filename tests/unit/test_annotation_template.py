from scripts.create_error_annotation_template import build_annotation_record


def test_annotation_template_keeps_system_evidence_separate_from_review_labels():
    record = build_annotation_record(
        {
            "id": "clip-1",
            "audio_path": "audio/clip-1.wav",
            "language": "fr",
            "reference_text": "phrase de référence",
        },
        {
            "baseline_hypothesis": "hypothèse initiale",
            "hypothesis": "hypothèse corrigée",
            "correction_applied": True,
            "correction_outcome": "improved",
            "corrections": [{"reason": ["two decoding passes agreed"]}],
        },
    )

    assert record["baseline_hypothesis"] == "hypothèse initiale"
    assert record["final_hypothesis"] == "hypothèse corrigée"
    assert record["automatic_correction_outcome"] == "improved"
    assert record["system_corrections"][0]["reason"] == ["two decoding passes agreed"]
    assert record["status"] == "unreviewed"
    assert record["segments"] == []
