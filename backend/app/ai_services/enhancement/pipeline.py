from __future__ import annotations

import logging
import time
from typing import Any, Dict, Iterable, List, Sequence, Tuple, cast

from app.ai_services.enhancement import (
    BaseRefiner,
    BaseSegmentSplitter,
    VADManager,
)
from app.ai_services.schema import BaseSegment, EnhancedSegment

logger = logging.getLogger(__name__)


class EnhancementPipeline:
    """Composable enhancement pipeline orchestrating VAD/refinement/splitting."""

    def __init__(self, components: Sequence[object] | None = None) -> None:
        self.components: List[object] = list(components or [])

    def is_empty(self) -> bool:
        """Return True when no components are configured."""
        return len(self.components) == 0

    def process(
        self,
        segments: Sequence[BaseSegment],
        audio_path: str,
        **kwargs: Any,
    ) -> Tuple[List[EnhancedSegment], Dict[str, Any]]:
        """Chain configured enhancement components.

        Args:
            segments: Base transcription segments.
            audio_path: Path to the audio file (passed to components such as VAD/refiner).
            **kwargs: Additional options forwarded to components (language hints, etc.).

        Returns:
            Tuple of (enhanced_segments, aggregated_metrics).
        """
        current = self._normalize_segments(segments)
        metrics: Dict[str, Any] = {
            "components_configured": len(self.components),
            "component_metrics": [],
        }
        pipeline_start = time.perf_counter()

        for component in self.components:
            name = component.__class__.__name__
            component_start = time.perf_counter()
            before_count = len(current)
            try:
                next_segments, component_meta = self._execute_component(
                    component, current, audio_path, **kwargs
                )
                current = self._normalize_segments(next_segments)
                elapsed_ms = (time.perf_counter() - component_start) * 1000
                entry: Dict[str, Any] = {
                    "component": name,
                    "segments_in": before_count,
                    "segments_out": len(current),
                    "processing_time_ms": elapsed_ms,
                }
                if component_meta:
                    entry["details"] = component_meta
                metrics["component_metrics"].append(entry)
            except Exception as exc:  # pragma: no cover - defensive
                elapsed_ms = (time.perf_counter() - component_start) * 1000
                logger.error(
                    "Enhancement component %s failed: %s", name, exc, exc_info=True
                )
                metrics["component_metrics"].append(
                    {
                        "component": name,
                        "error": str(exc),
                        "processing_time_ms": elapsed_ms,
                    }
                )
                # Graceful degradation: continue with previous segments unchanged.
                continue

        metrics["components_executed"] = sum(
            1 for entry in metrics["component_metrics"] if "error" not in entry
        )
        metrics["total_pipeline_time_ms"] = (
            time.perf_counter() - pipeline_start
        ) * 1000
        metrics["pipeline_config"] = [c.__class__.__name__ for c in self.components]
        metrics["applied_enhancements"] = self._collect_enhancements(current)
        return current, metrics

    def _execute_component(
        self,
        component: object,
        segments: Sequence[EnhancedSegment],
        audio_path: str,
        **kwargs: Any,
    ) -> Tuple[Sequence[BaseSegment], Dict[str, Any]]:
        """Execute a single component and return its output + telemetry."""
        if isinstance(component, VADManager):
            filtered, engine = component.process_segments(
                segments=list(segments),
                audio_path=audio_path,
            )
            if engine:
                tag = f"vad:{engine}"
                for segment in filtered:
                    enhancements = segment.setdefault("enhancements_applied", [])
                    if tag not in enhancements:
                        enhancements.append(tag)
            return filtered, {"engine": engine}

        if isinstance(component, BaseRefiner):
            refined = component.refine(segments, audio_path, **kwargs)
            return refined, component.get_metrics()

        if isinstance(component, BaseSegmentSplitter):
            split_segments = component.split(list(segments), **kwargs)
            return split_segments, component.get_metrics()

        if hasattr(component, "process"):
            processed = component.process(segments, audio_path, **kwargs)  # type: ignore[attr-defined]
            details = self._safe_metrics(component)
            return processed, details

        raise TypeError(f"Unsupported enhancement component: {component!r}")

    @staticmethod
    def _collect_enhancements(segments: Sequence[EnhancedSegment]) -> List[str]:
        """Aggregate enhancement labels from all segments."""
        labels: List[str] = []
        for segment in segments:
            for label in segment.get("enhancements_applied", []) or []:
                if label not in labels:
                    labels.append(label)
        return labels

    @staticmethod
    def _safe_metrics(component: object) -> Dict[str, Any]:
        """Best-effort metrics hook for arbitrary component types."""
        if hasattr(component, "get_metrics"):
            try:
                data = component.get_metrics()  # type: ignore[attr-defined]
                return data or {}
            except Exception:  # pragma: no cover - defensive
                logger.debug("Failed to fetch metrics from %s", component, exc_info=True)
        return {}

    @staticmethod
    def _normalize_segments(
        segments: Sequence[BaseSegment],
    ) -> List[EnhancedSegment]:
        normalized: List[EnhancedSegment] = []
        for segment in segments:
            # Copy segment to avoid mutating upstream references.
            normalized.append(cast(EnhancedSegment, dict(segment)))
        return normalized
