"""Energy-based timestamp refinement with char/word timing enrichment."""

from __future__ import annotations

import logging
import math
import re
import time
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

try:  # pragma: no cover - imported lazily in environments without librosa
    import librosa  # type: ignore
except ImportError:  # pragma: no cover
    librosa = None  # type: ignore

try:  # pragma: no cover
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    np = None  # type: ignore

from app.ai_services.enhancement.base_refiner import BaseRefiner
from app.ai_services.schema import CharTiming, EnhancedSegment, WordTiming

logger = logging.getLogger(__name__)

CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
WORD_SPLIT_PATTERN = re.compile(r"[^\w']+", re.UNICODE)


class TimestampRefiner(BaseRefiner):
    """Model-agnostic timestamp refinement component (Story 4.3)."""

    alignment_model_name = "timestamp_refiner.librosa"

    def __init__(
        self,
        *,
        search_window_ms: int = 200,
        sample_rate: int = 16000,
        frame_length: int = 2048,
        hop_length: int = 512,
    ) -> None:
        super().__init__()
        self.search_window_ms = max(50, search_window_ms)
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length
        self._analysis_cache: Dict[
            str, Tuple["np.ndarray", int, "np.ndarray", "np.ndarray"]
        ] = {}

    @classmethod
    def is_available(cls) -> bool:  # pragma: no cover - simple import guard
        return librosa is not None and np is not None

    def refine(
        self,
        segments: Sequence[MutableMapping[str, Any]],
        audio_path: str,
        *,
        language: Optional[str] = None,
    ) -> List[EnhancedSegment]:
        """
        Refine timestamps, populate timing arrays, and append metadata.

        Args:
            segments: Raw transcription segments.
            audio_path: Path to source audio.
            language: Optional language hint (iso code).
        """
        if not segments:
            self._reset_metrics()
            self._metrics = {
                "segments_processed": 0,
                "processing_time_ms": 0.0,
                "boundaries_adjusted": 0,
                "chars_populated": 0,
                "words_populated": 0,
            }
            return []

        if not self.is_available():
            logger.warning(
                "TimestampRefiner skipped because librosa/numpy are unavailable."
            )
            return [self._normalize_segment(segment) for segment in segments]

        start_time = time.perf_counter()
        analysis = self._load_analysis(audio_path)
        if analysis is None:
            logger.warning(
                "TimestampRefiner could not load audio (%s); returning original segments",
                audio_path,
            )
            return [self._normalize_segment(segment) for segment in segments]

        waveform, sr, energy, energy_times = analysis
        refined_segments: List[EnhancedSegment] = []
        boundary_adjustments = 0
        total_chars = 0
        total_words = 0

        previous_end = None
        for idx, raw_segment in enumerate(segments):
            segment = self._normalize_segment(raw_segment)
            next_start = (
                float(segments[idx + 1].get("start", segment["end"]))
                if idx + 1 < len(segments)
                else None
            )

            new_start, start_adjusted = self._refine_boundary(
                segment["start"],
                energy,
                energy_times,
                sr,
                previous_end,
                segment["end"],
            )
            new_end, end_adjusted = self._refine_boundary(
                segment["end"],
                energy,
                energy_times,
                sr,
                new_start,
                next_start,
            )

            if start_adjusted or end_adjusted:
                boundary_adjustments += 1

            segment["start"] = new_start
            segment["end"] = max(new_end, new_start)

            lang_hint = self._infer_language(segment["text"], language)
            words = self._populate_word_timings(segment, lang_hint)
            chars = self._populate_char_timings(segment, words, lang_hint)
            total_words += len(words)
            total_chars += len(chars)

            segment["words"] = words
            if chars:
                segment["chars"] = chars
            else:
                segment.pop("chars", None)

            enhancements = segment.setdefault("enhancements_applied", [])
            if "timestamp_refine" not in enhancements:
                enhancements.append("timestamp_refine")

            segment["alignment_model"] = self.alignment_model_name
            refined_segments.append(segment)
            previous_end = segment["end"]

        self._metrics = {
            "segments_processed": len(refined_segments),
            "processing_time_ms": round((time.perf_counter() - start_time) * 1000, 3),
            "boundaries_adjusted": boundary_adjustments,
            "chars_populated": total_chars,
            "words_populated": total_words,
        }
        return refined_segments

    # ------------------------------------------------------------------#
    # Internal helpers
    # ------------------------------------------------------------------#
    def _load_analysis(
        self, audio_path: str
    ) -> Optional[Tuple["np.ndarray", int, "np.ndarray", "np.ndarray"]]:
        if audio_path in self._analysis_cache:
            return self._analysis_cache[audio_path]

        if librosa is None or np is None:  # pragma: no cover - guard
            return None

        # Security: Validate audio path to prevent path traversal attacks
        if not self._validate_audio_path(audio_path):
            logger.warning("Invalid audio path rejected: %s", audio_path)
            return None

        try:
            waveform, sr = librosa.load(
                audio_path, sr=self.sample_rate, mono=True  # type: ignore[arg-type]
            )
        except FileNotFoundError:
            return None
        except Exception as exc:  # pragma: no cover - logging only
            logger.warning("librosa failed to load %s: %s", audio_path, exc)
            return None

        energy = librosa.feature.rms(
            y=waveform, frame_length=self.frame_length, hop_length=self.hop_length
        )[0]
        energy_times = (
            np.arange(len(energy), dtype=float) * (self.hop_length / float(sr))
        )

        self._analysis_cache[audio_path] = (waveform, sr, energy, energy_times)
        return self._analysis_cache[audio_path]

    def _normalize_segment(
        self, raw_segment: MutableMapping[str, Any]
    ) -> EnhancedSegment:
        start = float(raw_segment.get("start", 0.0))
        end = float(raw_segment.get("end", start))
        if end < start:
            end = start
        normalized: EnhancedSegment = EnhancedSegment(
            start=start,
            end=end,
            text=str(raw_segment.get("text", "")).strip(),
            words=list(raw_segment.get("words", [])),
            chars=list(raw_segment.get("chars", [])),
            confidence=raw_segment.get("confidence"),
            no_speech_prob=raw_segment.get("no_speech_prob"),
            avg_logprob=raw_segment.get("avg_logprob"),
            source_model=raw_segment.get("source_model"),
            enhancements_applied=list(raw_segment.get("enhancements_applied", [])),
            speaker=raw_segment.get("speaker"),
        )
        if "alignment_model" in raw_segment:
            normalized["alignment_model"] = raw_segment["alignment_model"]
        return normalized

    def _refine_boundary(
        self,
        target_time: float,
        energy: "np.ndarray",
        energy_times: "np.ndarray",
        sample_rate: int,
        lower_bound: Optional[float],
        upper_bound: Optional[float],
    ) -> Tuple[float, bool]:
        """
        Search ±window for minimum-energy point that respects neighbors.
        """
        if np is None:
            return target_time, False

        window = self.search_window_ms / 1000.0
        start_time = max(target_time - window, lower_bound or 0.0)
        end_time = min(target_time + window, upper_bound or target_time + window)

        mask = (energy_times >= start_time) & (energy_times <= end_time)
        if not np.any(mask):
            return target_time, False

        candidate_times = energy_times[mask]
        candidate_energy = energy[mask]
        idx = int(np.argmin(candidate_energy))
        refined_time = float(candidate_times[idx])

        # clamp to ensure < window deviation and valid ordering
        refined_time = min(max(refined_time, start_time), end_time)
        refined_time = max(refined_time, lower_bound or 0.0)
        if upper_bound is not None:
            refined_time = min(refined_time, upper_bound)

        adjusted = not math.isclose(refined_time, target_time, abs_tol=0.001)
        return refined_time, adjusted

    def _populate_word_timings(
        self,
        segment: EnhancedSegment,
        language_hint: str,
    ) -> List[WordTiming]:
        duration = max(segment["end"] - segment["start"], 0.0)
        existing_words = segment.get("words") or []
        normalized: List[WordTiming] = []

        if existing_words:
            for entry in existing_words:
                word_text = str(entry.get("word") or entry.get("text") or "").strip()
                if not word_text:
                    continue
                start = float(entry.get("start", segment["start"]))
                end = float(entry.get("end", start))
                normalized.append(
                    WordTiming(
                        word=word_text,
                        start=max(segment["start"], start),
                        end=min(segment["end"], max(start, end)),
                        score=float(entry.get("score", 0.95)),
                        language=entry.get("language") or language_hint,
                    )
                )
            if normalized:
                return normalized

        tokens = self._tokenize_words(segment["text"], language_hint)
        if not tokens:
            return normalized

        slice_duration = duration / max(len(tokens), 1) if duration else 0.0
        for idx, token in enumerate(tokens):
            start = segment["start"] + idx * slice_duration
            end = start + slice_duration if slice_duration else segment["end"]
            normalized.append(
                WordTiming(
                    word=token,
                    start=float(start),
                    end=float(end),
                    score=0.95,
                    language=language_hint,
                )
            )
        return normalized

    def _populate_char_timings(
        self,
        segment: EnhancedSegment,
        words: List[WordTiming],
        language_hint: str,
    ) -> List[CharTiming]:
        if language_hint.startswith("zh") is False and not self._contains_chinese(
            segment["text"]
        ):
            return []

        char_timings: List[CharTiming] = []
        chinese_words = [
            word for word in words if self._contains_chinese(word["word"])
        ]
        if chinese_words:
            for word in chinese_words:
                chars = [ch for ch in word["word"] if self._is_cjk(ch)]
                if not chars:
                    continue
                duration = max(word["end"] - word["start"], 0.0)
                slice_duration = duration / len(chars) if duration else 0.0
                for idx, char in enumerate(chars):
                    start = word["start"] + idx * slice_duration
                    end = start + slice_duration if slice_duration else word["end"]
                    char_timings.append(
                        CharTiming(
                            char=char,
                            start=float(start),
                            end=float(end),
                            score=word.get("score", 0.95),
                        )
                    )
        else:
            chars = [ch for ch in segment["text"] if self._is_cjk(ch)]
            if not chars:
                return []
            duration = max(segment["end"] - segment["start"], 0.0)
            slice_duration = duration / len(chars) if duration else 0.0
            for idx, char in enumerate(chars):
                start = segment["start"] + idx * slice_duration
                end = start + slice_duration if slice_duration else segment["end"]
                char_timings.append(
                    CharTiming(char=char, start=float(start), end=float(end), score=0.9)
                )
        return char_timings

    @staticmethod
    def _infer_language(text: str, hint: Optional[str]) -> str:
        if hint:
            return hint.lower()
        if CHINESE_CHAR_PATTERN.search(text):
            return "zh"
        return "en"

    @staticmethod
    def _tokenize_words(text: str, language: str) -> List[str]:
        stripped = text.strip()
        if not stripped:
            return []
        if language.startswith("zh") or CHINESE_CHAR_PATTERN.search(stripped):
            return [char for char in stripped if TimestampRefiner._is_cjk(char)]

        tokens = [token for token in WORD_SPLIT_PATTERN.split(stripped) if token]
        return tokens or [stripped]

    @staticmethod
    def _contains_chinese(text: str) -> bool:
        return bool(CHINESE_CHAR_PATTERN.search(text))

    @staticmethod
    def _is_cjk(char: str) -> bool:
        return bool(CHINESE_CHAR_PATTERN.match(char))

    @staticmethod
    def _validate_audio_path(audio_path: str) -> bool:
        """
        Validate audio file path to prevent path traversal attacks.

        Security checks:
        - Path must exist and be a file
        - Path must be absolute (not relative)
        - No directory traversal sequences (..)

        Args:
            audio_path: Path to audio file

        Returns:
            True if path is valid and safe, False otherwise
        """
        try:
            from pathlib import Path

            path = Path(audio_path)

            # Must be absolute path
            if not path.is_absolute():
                logger.warning("Rejected relative path: %s", audio_path)
                return False

            # Resolve to absolute path (handles symlinks, .., etc.)
            resolved = path.resolve()

            # Path must exist and be a file
            if not resolved.exists() or not resolved.is_file():
                return False

            # Check for path traversal sequences
            if ".." in audio_path:
                logger.warning("Rejected path with traversal sequence: %s", audio_path)
                return False

            return True

        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Path validation failed for %s: %s", audio_path, exc)
            return False
