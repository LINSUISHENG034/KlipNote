from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from app.ai_services.enhancement.pipeline import EnhancementPipeline
from app.ai_services.enhancement.segment_splitter import SegmentSplitter
from app.ai_services.enhancement.timestamp_refiner import TimestampRefiner
from app.ai_services.enhancement.vad_manager import VADManager
from app.config import settings

logger = logging.getLogger(__name__)

ComponentFactory = Callable[[], object]


COMPONENT_BUILDERS: Dict[str, ComponentFactory] = {
    "vad": VADManager,
    "refine": TimestampRefiner,
    "split": SegmentSplitter,
}


def create_pipeline(
    pipeline_config: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None
) -> EnhancementPipeline:
    """
    Instantiate an EnhancementPipeline based on configuration.

    Configuration Priority (AC-8):
    1. config_dict (from API)
    2. Environment variables (from settings)
    3. Default values

    Args:
        pipeline_config: Legacy config string (comma-separated component names)
        config_dict: Optional API-provided configuration dictionary

    Returns:
        EnhancementPipeline instance
    """
    # Configuration source tracking
    config_source = "defaults"

    # Determine configuration based on priority: API > env > defaults
    if config_dict:
        config_source = "API"
        pipeline_str = config_dict.get("pipeline", settings.ENHANCEMENT_PIPELINE or "vad,refine,split")

        vad_cfg = config_dict.get("vad", {}) or {}
        vad_config = {
            "enabled": vad_cfg.get("enabled", settings.VAD_ENABLED),
            "aggressiveness": vad_cfg.get("aggressiveness", settings.VAD_WEBRTC_AGGRESSIVENESS),
        }

        refine_cfg = config_dict.get("refine", {}) or {}
        refine_config = {
            "enabled": refine_cfg.get("enabled", settings.REFINE_ENABLED),
            "search_window_ms": refine_cfg.get("search_window_ms", settings.REFINE_SEARCH_WINDOW_MS),
        }

        split_cfg = config_dict.get("split", {}) or {}
        split_config = {
            "enabled": split_cfg.get("enabled", settings.SPLIT_ENABLED),
            "max_duration": split_cfg.get("max_duration", settings.SPLIT_MAX_DURATION),
            "max_chars": split_cfg.get("max_chars", settings.SPLIT_MAX_CHARS),
        }
    else:
        # Use legacy pipeline_config string or fall back to settings
        config_value = (pipeline_config or settings.ENHANCEMENT_PIPELINE or "").strip()
        pipeline_str = config_value if config_value else "vad,refine,split"
        vad_config = {
            "enabled": settings.VAD_ENABLED,
            "aggressiveness": settings.VAD_WEBRTC_AGGRESSIVENESS  # Map to webrtc_aggressiveness
        }
        refine_config = {
            "enabled": settings.REFINE_ENABLED,
            "search_window_ms": settings.REFINE_SEARCH_WINDOW_MS
        }
        split_config = {
            "enabled": settings.SPLIT_ENABLED,
            "max_duration": settings.SPLIT_MAX_DURATION,
            "max_chars": settings.SPLIT_MAX_CHARS
        }
        config_source = "environment"

    # Check global kill switch before processing
    if not settings.ENABLE_ENHANCEMENTS:
        logger.info("Enhancement pipeline disabled globally")
        return EnhancementPipeline([])

    # Handle "none" case
    if pipeline_str.lower() in {"", "none"}:
        logger.info("No enhancement components requested")
        return EnhancementPipeline([])

    logger.info(f"Creating enhancement pipeline (config source: {config_source})")

    # Parse pipeline components
    component_names: List[str] = [
        name.strip().lower()
        for name in pipeline_str.split(",")
        if name.strip()
    ]

    if not component_names:
        return EnhancementPipeline([])

    # Instantiate components with configuration-aware factory
    components: List[object] = []
    for component_name in component_names:
        # Skip components that are disabled
        if component_name == "vad" and not vad_config.get("enabled", True):
            logger.debug("VAD component disabled, skipping")
            continue
        elif component_name == "refine" and not refine_config.get("enabled", True):
            logger.debug("Refine component disabled, skipping")
            continue
        elif component_name == "split" and not split_config.get("enabled", True):
            logger.debug("Split component disabled, skipping")
            continue

        # Get factory function
        factory = COMPONENT_BUILDERS.get(component_name)
        if not factory:
            raise ValueError(
                f"Unknown enhancement component '{component_name}'. "
                f"Valid options: {', '.join(sorted(COMPONENT_BUILDERS.keys()))}"
            )

        # Instantiate with API config (if available) or defaults
        if component_name == "vad":
            # VADManager takes aggressiveness as webrtc_aggressiveness
            components.append(
                factory(webrtc_aggressiveness=vad_config.get("aggressiveness", 3))
            )
            logger.debug(f"Added VAD component (aggressiveness={vad_config.get('aggressiveness', 3)})")

        elif component_name == "refine":
            # TimestampRefiner takes search_window_ms
            components.append(
                factory(search_window_ms=refine_config.get("search_window_ms", 200))
            )
            logger.debug(f"Added Refiner component (window={refine_config.get('search_window_ms', 200)}ms)")

        elif component_name == "split":
            # SegmentSplitter takes max_duration and max_chars
            components.append(
                factory(
                    max_duration=split_config.get("max_duration", 7.0),
                    max_chars=split_config.get("max_chars", 200)
                )
            )
            logger.debug(
                f"Added Splitter component "
                f"(duration={split_config.get('max_duration', 7.0)}s, "
                f"chars={split_config.get('max_chars', 200)})"
            )

    logger.info(f"Enhancement pipeline created with {len(components)} components: {component_names}")
    return EnhancementPipeline(components)
