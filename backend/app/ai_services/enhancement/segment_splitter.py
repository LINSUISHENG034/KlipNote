from __future__ import annotations

import logging
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.ai_services.enhancement.base_segment_splitter import BaseSegmentSplitter
from app.config import settings
from app.ai_services.schema import CharTiming, EnhancedSegment, WordTiming

logger = logging.getLogger(__name__)

CJK_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
PUNCTUATION_PATTERN = re.compile(r"[。！？；，]")
WORD_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


class SegmentSplitter(BaseSegmentSplitter):
    """Split long segments at natural punctuation/pause boundaries."""

    def __init__(
        self,
        *,
        max_duration: float | None = None,
        max_chars: int | None = None,
        char_duration_sec: float | None = None,
        enabled: bool | None = None,
    ) -> None:
        super().__init__()
        self.max_duration = float(max_duration or settings.SEGMENT_SPLITTER_MAX_DURATION)
        self.max_chars = int(max_chars or settings.SEGMENT_SPLITTER_MAX_CHARS)
        self.char_duration_sec = float(
            char_duration_sec or settings.SEGMENT_SPLITTER_CHAR_DURATION_SEC
        )
        self.enabled = settings.SEGMENT_SPLITTER_ENABLED if enabled is None else enabled

    @classmethod
    def is_available(cls) -> bool:
        """Feature flag guard; no optional deps required."""
        return settings.SEGMENT_SPLITTER_ENABLED

    def split(self, segments: List[EnhancedSegment], **kwargs: Any) -> List[EnhancedSegment]:
        """Split segments exceeding duration/character constraints."""
        if not segments:
            self._reset_metrics()
            self._metrics = {
                "segments_in": 0,
                "segments_out": 0,
                "estimated_duration_sum": 0.0,
                "avg_chars_per_segment": 0.0,
            }
            return []

        if not self.enabled:
            logger.info("SegmentSplitter disabled via config; returning original segments")
            self._reset_metrics()
            self._metrics = {
                "segments_in": len(segments),
                "segments_out": len(segments),
                "estimated_duration_sum": 0.0,
                "avg_chars_per_segment": 0.0,
            }
            return list(segments)

        processed: List[EnhancedSegment] = []
        total_chars = 0
        estimated_duration_sum = 0.0
        split_operations = 0
        merge_operations = 0

        for seg in segments:
            text = (seg.get("text") or "").strip()
            char_count = self._count_chinese_characters(text)
            total_chars += char_count
            estimated_duration_sum += self._estimate_duration_from_text(text)

            duration = float(seg.get("end", 0.0)) - float(seg.get("start", 0.0))
            needs_split = duration > self.max_duration or len(text) > self.max_chars

            if needs_split:
                splits = self._split_segment(
                    seg,
                    text,
                    pause_boundaries=kwargs.get("pause_boundaries"),
                )
                if len(splits) > 1:
                    split_operations += len(splits) - 1
                processed.extend(splits)
            else:
                processed.append(seg)

        processed, merge_operations = self._merge_short_segments(processed)
        self._ensure_segment_split_tag(processed)

        average_chars = total_chars / max(len(segments), 1)
        compliance_ratio, compliant_segments = self._compute_compliance(processed)
        self._metrics = {
            "segments_in": len(segments),
            "segments_out": len(processed),
            "estimated_duration_sum": estimated_duration_sum,
            "avg_chars_per_segment": average_chars,
            "max_chars": self.max_chars,
            "split_operations": split_operations,
            "merge_operations": merge_operations,
            "split_count": split_operations,
            "merge_count": merge_operations,
            "compliant_segments": compliant_segments,
            "compliance_ratio": compliance_ratio,
        }
        return processed

    def _count_chinese_characters(self, text: str) -> int:
        """Count characters in the common CJK Unicode block."""
        if not text:
            return 0
        return len(CJK_CHAR_PATTERN.findall(text))

    def _estimate_duration_from_text(self, text: str) -> float:
        """Estimate duration using Chinese heuristics."""
        if not text:
            return 0.0
        char_count = self._count_chinese_characters(text)
        if char_count == 0:
            char_count = len(text)
        return char_count * self.char_duration_sec

    def _split_segment(
        self,
        segment: EnhancedSegment,
        text: str,
        *,
        pause_boundaries: Optional[List[float]] = None,
    ) -> List[EnhancedSegment]:
        """Split a segment using punctuation-first boundaries."""
        candidates = self._find_punctuation_split_points(text)
        if not candidates:
            candidates = self._find_pause_split_points(segment, text, pause_boundaries)
            if not candidates:
                return [segment]

        split_indices = self._choose_split_indices(candidates, len(text))
        if not split_indices:
            return [segment]

        slices: List[Tuple[int, int, str]] = []
        start_idx = 0
        for idx in split_indices:
            part = text[start_idx:idx].strip()
            if part:
                slices.append((start_idx, idx, part))
            start_idx = idx

        if not slices:
            return [segment]

        new_segments: List[EnhancedSegment] = []
        duration = float(segment["end"]) - float(segment["start"])
        total_chars = len(text)

        char_timings = list(segment.get("chars") or [])
        word_timings = list(segment.get("words") or [])

        cursor_time = float(segment["start"])
        char_idx = 0
        word_idx = 0
        for start_idx, end_idx, part_text in slices:
            part_length = end_idx - start_idx
            ratio = part_length / total_chars if total_chars else 0

            char_target = max(len(part_text), 0)
            chars_subset, char_idx = self._extract_timings(
                char_timings, char_idx, char_target
            )

            word_target = max(self._estimate_word_count(part_text), 0)
            words_subset, word_idx = self._extract_timings(
                word_timings, word_idx, word_target
            )

            start_time, end_time = self._derive_segment_bounds(
                cursor_time,
                duration,
                ratio,
                chars_subset,
                words_subset,
            )
            new_segment = self._build_split_segment(
                segment,
                part_text,
                start_time,
                end_time,
                chars_subset,
                words_subset,
            )
            new_segments.append(new_segment)
            cursor_time = end_time

        # Adjust final segment end time exactly to original end timestamp
        if new_segments:
            new_segments[-1]["end"] = float(segment["end"])
            self._append_remaining_timings(
                new_segments[-1],
                char_timings[char_idx:],
                word_timings[word_idx:],
            )
            self._validate_timing_integrity(new_segments)
        return new_segments

    def _find_punctuation_split_points(self, text: str) -> List[int]:
        """Return punctuation indices used as preferred split boundaries."""
        return [match.end() for match in PUNCTUATION_PATTERN.finditer(text)]

    def _find_pause_split_points(
        self,
        segment: EnhancedSegment,
        text: str,
        pause_boundaries: Optional[List[float]],
    ) -> List[int]:
        """
        Map pause boundaries (seconds from segment start) to text indices.

        This provides a lightweight fallback when punctuation is absent. Boundaries
        outside the segment duration are ignored.

        NOTE (Subtask 3.2): Energy-based pause detection via audio analysis
        ================================================================
        Current implementation accepts pre-computed pause boundaries via the
        `pause_boundaries` parameter. This allows separation of concerns:
        - SegmentSplitter focuses on text/metadata processing (no audio file access)
        - Upstream components (VAD, custom analyzers) can compute pauses using
          energy-based analysis with librosa/numpy

        Integration Pattern for Energy-Based Pause Detection:
        ------------------------------------------------------
        To integrate energy-based pause detection (as specified in Story 4.4 AC2),
        callers can compute pause boundaries using TimestampRefiner's approach:

        ```python
        import librosa
        import numpy as np

        def compute_pause_boundaries(audio_path: str, segment: EnhancedSegment) -> List[float]:
            '''Compute pause boundaries using energy-based detection'''
            # Load audio segment
            y, sr = librosa.load(audio_path, sr=16000, offset=segment['start'],
                                duration=segment['end'] - segment['start'])

            # Compute energy (RMS)
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

            # Find low-energy regions (pauses)
            energy_threshold = np.median(rms) * 0.3  # 30% of median energy
            pause_frames = np.where(rms < energy_threshold)[0]

            # Convert frame indices to time offsets within segment
            pause_times = librosa.frames_to_time(pause_frames, sr=sr, hop_length=hop_length)
            return pause_times.tolist()

        # Usage with SegmentSplitter:
        splitter = SegmentSplitter()
        for segment in segments:
            if needs_split(segment):
                pause_boundaries = compute_pause_boundaries(audio_path, segment)
                splits = splitter.split([segment], pause_boundaries=pause_boundaries)
        ```

        Future Enhancement (Deferred):
        ------------------------------
        Full energy-based pause detection could be integrated directly into
        SegmentSplitter by:
        1. Accepting optional audio_path parameter
        2. Computing pause boundaries internally when no punctuation found
        3. Reusing TimestampRefiner's energy analysis utilities

        This would require:
        - Adding librosa dependency to SegmentSplitter (currently only uses stdlib)
        - Audio file access (increases processing time from <2s to potentially >1min for 500 segments)
        - Caching audio waveforms to avoid repeated file I/O

        For MVP (Epic 4), the current lightweight approach is preferred to maintain
        performance (<3 min for 500 segments, AC8) since most Chinese text has
        sufficient punctuation for natural splitting.
        """
        if not pause_boundaries:
            return []
        duration = float(segment.get("end", 0.0)) - float(segment.get("start", 0.0))
        if duration <= 0.0 or not text:
            return []

        indices: List[int] = []
        for boundary in pause_boundaries:
            if boundary <= 0.0 or boundary >= duration:
                continue
            idx = int(round((boundary / duration) * len(text)))
            if 0 < idx < len(text):
                indices.append(idx)

        # Deduplicate and sort
        return sorted(set(indices))

    def _choose_split_indices(self, candidates: List[int], total_len: int) -> List[int]:
        """Pick split indices ensuring minimum chunk size."""
        if not candidates:
            return []
        min_chunk = max(3, total_len // 3)
        split_points: List[int] = []
        last_point = 0

        for idx in candidates:
            if idx - last_point >= min_chunk:
                split_points.append(idx)
                last_point = idx

        if not split_points or split_points[-1] != total_len:
            split_points.append(total_len)

        return split_points

    def _build_split_segment(
        self,
        original: EnhancedSegment,
        text: str,
        start_time: float,
        end_time: float,
        chars: Sequence[CharTiming],
        words: Sequence[WordTiming],
    ) -> EnhancedSegment:
        """Create a new EnhancedSegment and distribute timing arrays."""
        segment_copy: EnhancedSegment = deepcopy(original)
        segment_copy["text"] = text
        segment_copy["start"] = start_time
        segment_copy["end"] = end_time

        segment_copy["chars"] = list(chars)
        segment_copy["words"] = list(words)

        enhancements = list(segment_copy.get("enhancements_applied", []))
        if "segment_split" not in enhancements:
            enhancements.append("segment_split")
        segment_copy["enhancements_applied"] = enhancements

        return segment_copy

    def _extract_timings(
        self,
        timings: List[Dict[str, Any]],
        start_idx: int,
        count: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Copy a slice of timing entries, ensuring bounds safety."""
        if not timings or count <= 0 or start_idx >= len(timings):
            return [], start_idx
        end_idx = min(start_idx + count, len(timings))
        return [dict(t) for t in timings[start_idx:end_idx]], end_idx

    def _estimate_word_count(self, text: str) -> int:
        """Approximate word counts for mapping word timing arrays."""
        if not text:
            return 0
        return len(WORD_PATTERN.findall(text))

    def _derive_segment_bounds(
        self,
        cursor_time: float,
        duration: float,
        ratio: float,
        chars: Sequence[CharTiming],
        words: Sequence[WordTiming],
    ) -> Tuple[float, float]:
        """Prefer timing metadata to compute precise start/end."""
        if chars:
            return float(chars[0]["start"]), float(chars[-1]["end"])
        if words:
            return float(words[0]["start"]), float(words[-1]["end"])
        part_duration = duration * ratio
        return cursor_time, cursor_time + part_duration

    def _append_remaining_timings(
        self,
        final_segment: EnhancedSegment,
        remaining_chars: Sequence[CharTiming],
        remaining_words: Sequence[WordTiming],
    ) -> None:
        """Attach any leftover timing entries to the final segment."""
        if remaining_chars:
            final_segment.setdefault("chars", []).extend(dict(t) for t in remaining_chars)
            final_segment["end"] = float(final_segment["chars"][-1]["end"])
        if remaining_words:
            final_segment.setdefault("words", []).extend(dict(t) for t in remaining_words)

    def _ensure_segment_split_tag(self, segments: Sequence[EnhancedSegment]) -> None:
        """Guarantee enhancements_applied includes segment_split on output segments."""
        for seg in segments:
            enhancements = list(seg.get("enhancements_applied", []))
            if "segment_split" not in enhancements:
                enhancements.append("segment_split")
            seg["enhancements_applied"] = enhancements

    def _merge_short_segments(
        self,
        segments: List[EnhancedSegment],
    ) -> Tuple[List[EnhancedSegment], int]:
        """Merge short segments (<1s) when safe under duration/char constraints."""
        if not segments:
            return [], 0

        merged: List[EnhancedSegment] = []
        i = 0
        merges = 0

        while i < len(segments):
            current = segments[i]
            duration = float(current.get("end", 0.0)) - float(current.get("start", 0.0))

            if duration < 1.0 and i + 1 < len(segments):
                nxt = segments[i + 1]
                combined_duration = float(nxt.get("end", 0.0)) - float(current.get("start", 0.0))
                combined_chars = len((current.get("text") or "")) + len((nxt.get("text") or ""))

                if combined_duration < self.max_duration and combined_chars < self.max_chars:
                    merged.append(self._merge_segments(current, nxt))
                    merges += 1
                    i += 2
                    continue

            merged.append(current)
            i += 1

        return merged, merges

    def _merge_segments(
        self,
        left: EnhancedSegment,
        right: EnhancedSegment,
    ) -> EnhancedSegment:
        """Merge two adjacent segments, concatenating text and timing arrays."""
        merged: EnhancedSegment = deepcopy(left)
        merged["text"] = self._combine_text(left.get("text", ""), right.get("text", ""))
        merged["end"] = float(right.get("end", merged["end"]))

        merged_chars = list(left.get("chars") or [])
        merged_chars.extend(dict(t) for t in right.get("chars") or [])
        merged["chars"] = merged_chars

        merged_words = list(left.get("words") or [])
        merged_words.extend(dict(t) for t in right.get("words") or [])
        merged["words"] = merged_words

        enhancements = set(merged.get("enhancements_applied", []))
        enhancements.update(right.get("enhancements_applied", []))
        enhancements.add("segment_split")
        merged["enhancements_applied"] = list(enhancements)

        return merged

    def _combine_text(self, left: str, right: str) -> str:
        """Combine text fragments with a minimal separator."""
        if not left:
            return right
        if not right:
            return left
        return f"{left.rstrip()} {right.lstrip()}"

    def _validate_timing_integrity(
        self,
        segments: Sequence[EnhancedSegment],
        *,
        epsilon: float = 1e-3,
    ) -> None:
        """Ensure char/word timings stay within their segment bounds."""
        for seg in segments:
            start = float(seg["start"])
            end = float(seg["end"])
            for timing in seg.get("chars", []):
                timing["start"] = max(start, float(timing["start"]))
                timing["end"] = min(end, float(timing["end"]))
            for timing in seg.get("words", []):
                timing["start"] = max(start, float(timing["start"]))
                timing["end"] = min(end, float(timing["end"]))

    def _compute_compliance(
        self,
        segments: Sequence[EnhancedSegment],
    ) -> Tuple[float, int]:
        """Calculate compliance ratio for duration and character constraints."""
        if not segments:
            return 0.0, 0
        compliant = sum(1 for seg in segments if self._is_compliant(seg))
        return compliant / len(segments), compliant

    def _is_compliant(self, segment: EnhancedSegment) -> bool:
        """Check duration and character-count constraints."""
        duration = float(segment.get("end", 0.0)) - float(segment.get("start", 0.0))
        if duration < 1.0 or duration > self.max_duration:
            return False
        text = (segment.get("text") or "").strip()
        return len(text) <= self.max_chars
