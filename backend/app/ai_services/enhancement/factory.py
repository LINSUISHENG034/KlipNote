from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

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


def create_pipeline(pipeline_config: Optional[str] = None) -> EnhancementPipeline:
    """Instantiate an EnhancementPipeline based on configuration."""
    config_value = (pipeline_config or settings.ENHANCEMENT_PIPELINE or "").strip()

    if not settings.ENABLE_ENHANCEMENTS or config_value.lower() in {"", "none"}:
        logger.info("Enhancement pipeline disabled (config=%s)", config_value or "none")
        return EnhancementPipeline([])

    component_names: List[str] = [
        name.strip().lower()
        for name in config_value.split(",")
        if name.strip()
    ]

    if not component_names:
        return EnhancementPipeline([])

    components: List[object] = []
    for name in component_names:
        factory = COMPONENT_BUILDERS.get(name)
        if not factory:
            raise ValueError(
                f"Unknown enhancement component '{name}'. "
                f"Valid options: {', '.join(sorted(COMPONENT_BUILDERS.keys()))}"
            )
        components.append(factory())

    return EnhancementPipeline(components)
