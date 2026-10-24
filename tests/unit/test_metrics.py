from echomind.evaluation.dataset import speaker_aware_split
from echomind.evaluation.metrics import (
    cer,
    corpus_cer,
    corpus_wer,
    correction_outcome,
    correction_summary,
    error_detection_metrics,
    normalized_cer,
    normalized_wer,
    percentile,
    sentence_error_rate,
    wer,
)


def test_reference_metrics():
    assert wer("a b", "a b") == 0
    assert cer("abc", "abc") == 0
    assert sentence_error_rate(["hello", "world"], ["hello", "there"]) == 0.5


def test_corpus_metrics_micro_average_by_reference_length():
    references = ["a", "a b c d e"]
    hypotheses = ["x", "a b c d e"]
    assert corpus_wer(references, hypotheses) == 1 / 6
    assert corpus_cer(references, hypotheses) == 1 / 10


def test_unicode_normalization_handles_case_diacritics_and_punctuation():
    assert normalized_wer("Bonjour !", "bonjour") == 0.0
    assert normalized_cer("مَرْحَبًا", "مرحبا") == 0.0


def test_error_metrics():
    metrics = error_detection_metrics([0, 1, 1, 0], [0.1, 0.8, 0.7, 0.2])
    assert metrics["f1"] == 1.0
    assert metrics["auroc"] == 1.0


def test_correction_outcomes_keep_harmful_denominator_explicit():
    assert correction_outcome(0.5, 0.2, True) == "improved"
    assert correction_outcome(0.2, 0.5, True) == "harmful"
    summary = correction_summary(["improved", "harmful", "not_applied"])
    assert summary["correction_rate"] == 2 / 3
    assert summary["harmful_correction_rate"] == 0.5


def test_percentile_is_deterministic_without_numpy():
    assert percentile([10, 20, 30, 40], 50) == 25


def test_speaker_split_refuses_unknown_speaker_ids():
    try:
        speaker_aware_split([{"id": "one", "speaker_id": "unknown"}])
    except ValueError as error:
        assert "no verified speaker_id" in str(error)
    else:
        raise AssertionError("unknown speaker IDs must not be treated as a valid split")


def test_speaker_split_keeps_utterances_from_each_speaker_together():
    rows = [
        {"id": "a1", "speaker_id": "speaker-a"},
        {"id": "a2", "speaker_id": "speaker-a"},
        {"id": "b1", "speaker_id": "speaker-b"},
        {"id": "c1", "speaker_id": "speaker-c"},
        {"id": "d1", "speaker_id": "speaker-d"},
    ]

    split = speaker_aware_split(rows, seed=3, test_fraction=0.25)
    train_speakers = {row["speaker_id"] for row in split["train"]}
    test_speakers = {row["speaker_id"] for row in split["test"]}

    assert train_speakers.isdisjoint(test_speakers)
