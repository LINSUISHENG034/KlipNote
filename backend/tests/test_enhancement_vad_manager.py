from unittest.mock import MagicMock, patch

from app.ai_services.enhancement.vad_manager import VADManager


def test_vad_manager_prefers_silero_when_available():
    mgr = VADManager(engine="auto")
    with patch.object(mgr, "_engine_order", return_value=["silero", "webrtc"]):
        with patch("app.ai_services.enhancement.vad_engines.silero_vad.SileroVAD.is_available", return_value=True):
            engine = mgr._select_engine()
            assert engine is not None
            assert engine.name == "silero"


def test_vad_manager_falls_back_to_webrtc():
    mgr = VADManager(engine="auto")
    with patch.object(mgr, "_engine_order", return_value=["silero", "webrtc"]):
        with patch("app.ai_services.enhancement.vad_engines.silero_vad.SileroVAD.is_available", return_value=False):
            with patch("app.ai_services.enhancement.vad_engines.webrtc_vad.WebRTCVAD.is_available", return_value=True):
                engine = mgr._select_engine()
                assert engine is not None
                assert engine.name == "webrtc"


def test_vad_manager_process_segments_returns_original_on_no_engine():
    mgr = VADManager(engine="auto")
    with patch.object(mgr, "_select_engine", return_value=None):
        segments, engine = mgr.process_segments(
            segments=[{"start": 0.0, "end": 1.0, "text": "hello"}],
            audio_path="dummy.wav",
        )
        assert engine is None
        assert len(segments) == 1


def test_vad_manager_filters_with_engine():
    mgr = VADManager(engine="auto")
    fake_engine = MagicMock()
    fake_engine.name = "silero"
    fake_engine.is_available.return_value = True
    fake_engine.detect_speech.return_value = [(0.0, 0.5)]
    fake_engine.filter_segments.return_value = [{"start": 0.0, "end": 0.5, "text": "speech"}]

    with patch.object(mgr, "_select_engine", return_value=fake_engine):
        segments, engine = mgr.process_segments(
            segments=[{"start": 0.0, "end": 1.0, "text": "speech"}],
            audio_path="dummy.wav",
        )
        assert engine == "silero"
        assert len(segments) == 1
        assert segments[0]["end"] == 0.5
