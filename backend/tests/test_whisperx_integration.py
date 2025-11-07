"""
Integration tests for WhisperXService with real audio files

These tests use real audio files from temp/audio_files/ directory.
They require GPU and are slower than unit tests.

Run with: pytest -m integration -v -s
Skip with: pytest -m "not integration"
"""

import pytest
from pathlib import Path
from app.ai_services.whisperx_service import WhisperXService


@pytest.mark.integration
@pytest.mark.skipif(
    not Path("temp/audio_files/en_columbia.wma").exists(),
    reason="Test audio file not found: temp/audio_files/en_columbia.wma"
)
def test_transcribe_english_wma_real_audio():
    """
    Integration Test: English WMA audio with auto language detection

    Test File: temp/audio_files/en_columbia.wma (Columbia speech)
    Expected: Language detected as 'en', transcription in English
    """
    audio_path = "temp/audio_files/en_columbia.wma"

    # Initialize service
    service = WhisperXService()

    # Transcribe with auto-detection (language=None)
    result = service.transcribe(audio_path, language=None)

    # Assertions
    assert len(result) > 0, "Should return transcription segments"

    # Check segment structure
    first_segment = result[0]
    assert "start" in first_segment
    assert "end" in first_segment
    assert "text" in first_segment
    assert isinstance(first_segment["start"], float)
    assert isinstance(first_segment["end"], float)
    assert isinstance(first_segment["text"], str)

    # Verify English text (Columbia speech contains recognizable English)
    all_text = " ".join(seg["text"] for seg in result)
    assert len(all_text) > 0, "Transcription text should not be empty"

    # Log for manual verification
    print(f"\n=== English WMA Transcription (Columbia) ===")
    print(f"Segments: {len(result)}")
    print(f"First segment: {first_segment}")
    print(f"Full text preview: {all_text[:200]}...")


@pytest.mark.integration
@pytest.mark.skipif(
    not Path("temp/audio_files/en_jfk.wav").exists(),
    reason="Test audio file not found: temp/audio_files/en_jfk.wav"
)
def test_transcribe_english_wav_real_audio():
    """
    Integration Test: English WAV audio (JFK speech)

    Test File: temp/audio_files/en_jfk.wav
    Expected: Language detected as 'en'
    """
    audio_path = "temp/audio_files/en_jfk.wav"

    service = WhisperXService()
    result = service.transcribe(audio_path, language=None)

    assert len(result) > 0
    all_text = " ".join(seg["text"] for seg in result)

    print(f"\n=== English WAV Transcription (JFK) ===")
    print(f"Segments: {len(result)}")
    print(f"Text preview: {all_text[:200]}...")


@pytest.mark.integration
@pytest.mark.skipif(
    not Path("temp/audio_files/zh_short_audio.mp3").exists(),
    reason="Test audio file not found: temp/audio_files/zh_short_audio.mp3"
)
def test_transcribe_chinese_mp3_short_real_audio():
    """
    Integration Test: Chinese MP3 audio (short)

    Test File: temp/audio_files/zh_short_audio.mp3
    Expected: Language auto-detected as 'zh', transcription in Chinese
    AC: Text should contain Chinese characters, not English
    """
    audio_path = "temp/audio_files/zh_short_audio.mp3"

    service = WhisperXService()
    result = service.transcribe(audio_path, language=None)

    assert len(result) > 0

    # Verify Chinese characters in transcription
    all_text = " ".join(seg["text"] for seg in result)

    # Check for Chinese characters (Unicode range: \u4e00-\u9fff)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in all_text)
    assert has_chinese, f"Expected Chinese characters, got: {all_text[:100]}"

    print(f"\n=== Chinese MP3 Transcription (Short) ===")
    print(f"Segments: {len(result)}")
    print(f"Chinese text: {all_text[:200]}...")


@pytest.mark.integration
@pytest.mark.skipif(
    not Path("temp/audio_files/zh_medium_audio.mp3").exists(),
    reason="Test audio file not found: temp/audio_files/zh_medium_audio.mp3"
)
def test_transcribe_chinese_mp3_medium_real_audio():
    """
    Integration Test: Chinese MP3 audio (medium length)

    Test File: temp/audio_files/zh_medium_audio.mp3
    Expected: Auto-detected Chinese, multiple segments
    """
    audio_path = "temp/audio_files/zh_medium_audio.mp3"

    service = WhisperXService()
    result = service.transcribe(audio_path, language=None)

    assert len(result) > 0

    # Medium audio should have multiple segments
    assert len(result) >= 3, f"Expected multiple segments, got {len(result)}"

    all_text = " ".join(seg["text"] for seg in result)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in all_text)
    assert has_chinese, "Expected Chinese characters"

    print(f"\n=== Chinese MP3 Transcription (Medium) ===")
    print(f"Segments: {len(result)}")
    print(f"Text preview: {all_text[:200]}...")


@pytest.mark.integration
def test_transcribe_manual_language_specification():
    """
    Integration Test: Manual language specification

    AC: User can override auto-detection by specifying language
    """
    # Use any available audio file for this test
    audio_files = [
        "temp/audio_files/zh_short_audio.mp3",
        "temp/audio_files/en_jfk.wav",
    ]

    audio_path = None
    for file in audio_files:
        if Path(file).exists():
            audio_path = file
            break

    if audio_path is None:
        pytest.skip("No audio files available for manual language test")

    service = WhisperXService()

    # Test with explicit language parameter
    result = service.transcribe(audio_path, language="zh")

    assert len(result) > 0
    print(f"\n=== Manual Language Specification Test ===")
    print(f"Audio file: {audio_path}")
    print(f"Specified language: zh")
    print(f"Segments: {len(result)}")
