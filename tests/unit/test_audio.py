import numpy as np

from echomind.audio.preprocessing import preprocess_audio, resample_audio, safe_normalize


def test_resample_and_normalize_fallback_contract():
    source = np.sin(np.linspace(0, 2 * np.pi, 800, dtype=np.float32))
    converted = resample_audio(source, 8000, 16000)
    assert 1590 <= len(converted) <= 1610
    normalized = safe_normalize(converted)
    assert np.max(np.abs(normalized)) <= 0.95001


def test_preprocess_detects_speech_region():
    audio = np.concatenate([np.zeros(1600), np.ones(3200, dtype=np.float32) * 0.1, np.zeros(1600)])
    processed, metadata = preprocess_audio(audio, 16000)
    assert len(processed) == len(audio)
    assert metadata.duration_seconds == 0.4
    assert metadata.speech_duration_seconds > 0
    assert metadata.quality.silence_ratio < 1
