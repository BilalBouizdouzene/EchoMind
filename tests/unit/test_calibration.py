from echomind.uncertainty.calibration import brier_score, expected_calibration_error


def test_calibration_metrics_are_bounded():
    probs = [0.1, 0.9, 0.8, 0.2]
    labels = [0, 1, 1, 0]
    assert 0 <= expected_calibration_error(probs, labels) <= 1
    assert 0 <= brier_score(probs, labels) <= 1
