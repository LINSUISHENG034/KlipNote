from __future__ import annotations

from app.ai_services.enhancement.segment_splitter import SegmentSplitter
from app.config import settings


def test_default_configuration_applied() -> None:
    splitter = SegmentSplitter()
    assert splitter.max_chars == settings.SEGMENT_SPLITTER_MAX_CHARS
    assert splitter.char_duration_sec == settings.SEGMENT_SPLITTER_CHAR_DURATION_SEC


def test_count_chinese_characters_detects_cjk_only() -> None:
    splitter = SegmentSplitter()
    assert splitter._count_chinese_characters("你好world再见") == 4


def test_estimate_duration_uses_char_duration_for_cjk() -> None:
    splitter = SegmentSplitter(char_duration_sec=0.5)
    assert splitter._estimate_duration_from_text("你好世界") == 4 * 0.5


def test_estimate_duration_fallbacks_to_text_length_when_no_cjk() -> None:
    splitter = SegmentSplitter(char_duration_sec=0.3)
    assert splitter._estimate_duration_from_text("hello") == 5 * 0.3
