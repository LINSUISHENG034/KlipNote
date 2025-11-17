import numpy as np
import pytest

from app.ai_services.enhancement.timestamp_refiner import TimestampRefiner


def _mock_analysis():
    waveform = np.zeros(16000, dtype=float)
    energy = np.linspace(1.0, 0.1, 16)
    times = np.linspace(0.0, 2.0, 16)
    return waveform, 16000, energy, times


def test_char_timing_population_chinese(monkeypatch):
    refiner = TimestampRefiner()
    monkeypatch.setattr(
        TimestampRefiner,
        "is_available",
        classmethod(lambda cls: True),
    )
    monkeypatch.setattr(refiner, "_load_analysis", lambda _: _mock_analysis())

    segments = [
        {
            "start": 0.0,
            "end": 2.0,
            "text": "这是测试",
            "source_model": "belle2",
        }
    ]

    refined = refiner.refine(segments, "test.wav", language="zh")
    seg = refined[0]

    assert len(seg["chars"]) == 4
    assert seg["chars"][0]["char"] == "这"
    assert "timestamp_refine" in seg["enhancements_applied"]
    assert seg["alignment_model"] == TimestampRefiner.alignment_model_name
    assert all(char["end"] <= seg["end"] for char in seg["chars"])


def test_word_timing_population_english(monkeypatch):
    refiner = TimestampRefiner()
    monkeypatch.setattr(
        TimestampRefiner,
        "is_available",
        classmethod(lambda cls: True),
    )
    monkeypatch.setattr(refiner, "_load_analysis", lambda _: _mock_analysis())

    segments = [
        {
            "start": 1.0,
            "end": 3.0,
            "text": "Hello world from KlipNote",
            "source_model": "whisperx",
        }
    ]

    refined = refiner.refine(segments, "test.wav", language="en")
    seg = refined[0]
    assert len(seg["words"]) == 4
    assert seg["words"][0]["word"] == "Hello"
    assert seg["words"][-1]["word"] == "KlipNote"
    assert all(word["language"] == "en" for word in seg["words"])


def test_boundary_refinement_prefers_low_energy(monkeypatch):
    refiner = TimestampRefiner(search_window_ms=200)
    monkeypatch.setattr(
        TimestampRefiner,
        "is_available",
        classmethod(lambda cls: True),
    )

    waveform = np.zeros(16000, dtype=float)
    energy = np.array([1.0, 0.2, 0.9, 1.0, 1.0])
    times = np.linspace(0.8, 1.2, len(energy))
    monkeypatch.setattr(
        refiner,
        "_load_analysis",
        lambda _: (waveform, 16000, energy, times),
    )

    segments = [{"start": 1.0, "end": 1.5, "text": "Test"}]
    refined = refiner.refine(segments, "dummy.wav", language="en")
    seg = refined[0]
    assert seg["start"] != pytest.approx(1.0)
    assert seg["start"] == pytest.approx(times[1])


def test_refiner_handles_missing_audio(monkeypatch):
    refiner = TimestampRefiner()
    monkeypatch.setattr(
        TimestampRefiner,
        "is_available",
        classmethod(lambda cls: True),
    )
    monkeypatch.setattr(refiner, "_load_analysis", lambda _: None)

    segments = [{"start": 0.0, "end": 1.0, "text": "Hello"}]
    refined = refiner.refine(segments, "missing.wav", language="en")
    assert refined[0]["text"] == "Hello"
    assert "alignment_model" not in refined[0]


def test_refiner_reads_real_audio(tmp_path):
    refiner = TimestampRefiner()
    if not refiner.is_available():  # pragma: no cover - dependency guard
        pytest.skip("librosa is not installed")

    import soundfile as sf  # type: ignore

    audio_path = tmp_path / "tone.wav"
    waveform = np.zeros(32000, dtype=float)
    sf.write(audio_path, waveform, 16000)

    segments = [{"start": 0.0, "end": 2.0, "text": "hello world"}]
    refined = refiner.refine(segments, str(audio_path), language="en")
    assert refined[0]["words"], "Word timing array should be populated"


def test_refiner_rejects_path_traversal_attack(monkeypatch):
    """Test that path traversal attempts are blocked (security fix)"""
    refiner = TimestampRefiner()
    monkeypatch.setattr(
        TimestampRefiner,
        "is_available",
        classmethod(lambda cls: True),
    )

    # Attempt path traversal attack
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/tmp/../../etc/passwd",
    ]

    for malicious_path in malicious_paths:
        segments = [{"start": 0.0, "end": 1.0, "text": "test"}]
        refined = refiner.refine(segments, malicious_path, language="en")

        # Should return original segments without refinement (graceful degradation)
        assert refined[0]["text"] == "test"
        assert "alignment_model" not in refined[0], \
            f"Should reject malicious path: {malicious_path}"


def test_refiner_rejects_relative_paths(monkeypatch):
    """Test that relative paths are rejected (security fix)"""
    refiner = TimestampRefiner()
    monkeypatch.setattr(
        TimestampRefiner,
        "is_available",
        classmethod(lambda cls: True),
    )

    # Relative paths should be rejected
    relative_paths = [
        "audio.wav",
        "./audio.wav",
        "test/audio.wav",
    ]

    for relative_path in relative_paths:
        segments = [{"start": 0.0, "end": 1.0, "text": "test"}]
        refined = refiner.refine(segments, relative_path, language="en")

        # Should return original segments without refinement
        assert refined[0]["text"] == "test"
        assert "alignment_model" not in refined[0], \
            f"Should reject relative path: {relative_path}"

