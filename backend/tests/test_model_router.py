from unittest.mock import MagicMock

from app.ai_services.model_router import (
    DetectionResult,
    RouterConfig,
    select_engine,
)


def _mock_detection(language: str, status: str = "completed") -> DetectionResult:
    return DetectionResult(
        language=language,
        confidence=0.97,
        duration_ms=120.0,
        status=status,
        error=None if status == "completed" else status,
    )


def test_select_engine_honors_mandarin_hint(mocker):
    mock_belle2 = MagicMock()
    mocker.patch("app.ai_services.model_router.Belle2Service", return_value=mock_belle2)
    config = RouterConfig()

    service, engine, details = select_engine(
        job_id="job-1",
        audio_path="tests/data/sample.wav",
        language_hint="zh-CN",
        config=config,
    )

    assert service is mock_belle2
    assert engine == "belle2"
    assert details["selection_reason"] == "user_hint_zh-cn"
    assert details["detected_language"] == "zh-cn"


def test_select_engine_honors_non_mandarin_hint(mocker):
    mock_whisperx = MagicMock()
    mocker.patch(
        "app.ai_services.model_router.WhisperXService", return_value=mock_whisperx
    )

    service, engine, details = select_engine(
        job_id="job-2",
        audio_path="tests/data/sample.wav",
        language_hint="en",
        config=RouterConfig(),
    )

    assert service is mock_whisperx
    assert engine == "whisperx"
    assert details["selection_reason"] == "user_hint_en"


def test_select_engine_routes_to_belle2_on_detection(mocker):
    mock_belle2 = MagicMock()
    mocker.patch("app.ai_services.model_router.Belle2Service", return_value=mock_belle2)
    mocker.patch(
        "app.ai_services.model_router.LanguageDetector.detect",
        return_value=_mock_detection("zh"),
    )

    service, engine, details = select_engine(
        job_id="job-3",
        audio_path="tests/data/sample.wav",
        language_hint=None,
        config=RouterConfig(),
    )

    assert service is mock_belle2
    assert engine == "belle2"
    assert details["selection_reason"] == "detected_zh"
    assert details["detected_language"] == "zh"


def test_select_engine_routes_to_whisperx_on_non_chinese_detection(mocker):
    mock_whisperx = MagicMock()
    mocker.patch(
        "app.ai_services.model_router.WhisperXService", return_value=mock_whisperx
    )
    mocker.patch(
        "app.ai_services.model_router.LanguageDetector.detect",
        return_value=_mock_detection("en"),
    )

    service, engine, details = select_engine(
        job_id="job-4",
        audio_path="tests/data/sample.wav",
        language_hint=None,
        config=RouterConfig(),
    )

    assert service is mock_whisperx
    assert engine == "whisperx"
    assert details["selection_reason"] == "detected_en"


def test_select_engine_falls_back_on_detection_timeout(mocker):
    mock_whisperx = MagicMock()
    mocker.patch(
        "app.ai_services.model_router.WhisperXService", return_value=mock_whisperx
    )
    timeout_result = DetectionResult(
        language=None,
        confidence=None,
        duration_ms=5000.0,
        status="timeout",
        error="detection_timeout",
    )
    mocker.patch(
        "app.ai_services.model_router.LanguageDetector.detect",
        return_value=timeout_result,
    )

    service, engine, details = select_engine(
        job_id="job-5",
        audio_path="tests/data/sample.wav",
        language_hint=None,
        config=RouterConfig(),
    )

    assert service is mock_whisperx
    assert engine == "whisperx"
    assert details["selection_reason"] == "detection_timeout"
    assert details["fallback_reason"] == "detection_timeout"
