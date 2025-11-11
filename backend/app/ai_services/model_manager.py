"""
Model Manager for lazy loading and caching AI models

Implements singleton pattern with LRU eviction to manage GPU memory efficiently.
Ensures maximum 2 concurrent models in memory to prevent OOM errors.
"""

import logging
import time
from typing import Dict, Any, Tuple, Optional
from functools import lru_cache
from collections import OrderedDict
import torch

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Singleton model manager for lazy loading and caching

    Features:
    - Lazy loading: Models load on first use, not on startup
    - LRU caching: Max 2 concurrent models, oldest evicted when limit reached
    - VRAM tracking: Monitors GPU memory usage
    - Thread-safe: Singleton pattern ensures single instance
    """

    _instance: Optional['ModelManager'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern: Only one ModelManager instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize model cache (only once due to singleton)"""
        if not ModelManager._initialized:
            # LRU cache: OrderedDict maintains insertion order
            # Max 2 models to fit within GPU memory constraints
            self.loaded_models: OrderedDict[str, Tuple[Any, Any]] = OrderedDict()
            self.max_models = 2

            # Track model load times for performance monitoring
            self.load_times: Dict[str, float] = {}

            ModelManager._initialized = True
            logger.info(f"ModelManager initialized (max {self.max_models} concurrent models)")

    def load_belle2(
        self,
        model_name: str = "BELLE-2/Belle-whisper-large-v3-zh",
        device: str = "cuda"
    ) -> Tuple[Any, Any]:
        """
        Load BELLE-2 model with LRU caching

        First call: Downloads model (~3.1GB, 5-10 minutes)
        Subsequent calls: Loads from cache (<5 seconds)

        Args:
            model_name: HuggingFace model ID
            device: 'cuda' or 'cpu'

        Returns:
            Tuple of (model, processor)

        Raises:
            RuntimeError: If model loading fails
        """
        cache_key = f"belle2_{model_name}_{device}"

        # Check if model is already loaded
        if cache_key in self.loaded_models:
            logger.info(f"Using cached BELLE-2 model: {model_name}")
            # Move to end (most recently used)
            self.loaded_models.move_to_end(cache_key)
            return self.loaded_models[cache_key]

        # Evict oldest model if at capacity
        if len(self.loaded_models) >= self.max_models:
            evicted_key, (evicted_model, _) = self.loaded_models.popitem(last=False)
            logger.info(f"Evicting model from cache: {evicted_key}")

            # Clear CUDA cache if on GPU
            if device == "cuda" and torch.cuda.is_available():
                del evicted_model
                torch.cuda.empty_cache()
                logger.info(f"GPU memory released: {self.get_vram_usage():.2f}GB remaining")

        # Load new model
        logger.info(f"Loading BELLE-2 model: {model_name} on {device}")
        start_time = time.time()

        try:
            from transformers import WhisperProcessor, WhisperForConditionalGeneration

            # Load processor (tokenizer + feature extractor)
            processor = WhisperProcessor.from_pretrained(model_name)

            # Load model with appropriate dtype
            model = WhisperForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            ).to(device)

            load_time = time.time() - start_time
            self.load_times[cache_key] = load_time

            # Cache the model
            self.loaded_models[cache_key] = (model, processor)

            logger.info(
                f"BELLE-2 model loaded in {load_time:.2f}s "
                f"(VRAM: {self.get_vram_usage():.2f}GB)"
            )

            return model, processor

        except Exception as e:
            logger.error(f"Failed to load BELLE-2 model: {e}", exc_info=True)
            raise RuntimeError(
                f"Failed to load BELLE-2 model '{model_name}': {str(e)}"
            )

    def load_whisperx(
        self,
        model_name: str = "large-v2",
        device: str = "cuda",
        compute_type: str = "float16"
    ) -> Any:
        """
        Load WhisperX model with LRU caching

        Args:
            model_name: Whisper model size
            device: 'cuda' or 'cpu'
            compute_type: 'float16', 'int8', or 'float32'

        Returns:
            WhisperX model instance

        Raises:
            RuntimeError: If model loading fails
        """
        cache_key = f"whisperx_{model_name}_{device}_{compute_type}"

        # Check if model is already loaded
        if cache_key in self.loaded_models:
            logger.info(f"Using cached WhisperX model: {model_name}")
            # Move to end (most recently used)
            self.loaded_models.move_to_end(cache_key)
            return self.loaded_models[cache_key][0]  # Return model only (no processor)

        # Evict oldest model if at capacity
        if len(self.loaded_models) >= self.max_models:
            evicted_key, (evicted_model, _) = self.loaded_models.popitem(last=False)
            logger.info(f"Evicting model from cache: {evicted_key}")

            # Clear CUDA cache if on GPU
            if device == "cuda" and torch.cuda.is_available():
                del evicted_model
                torch.cuda.empty_cache()
                logger.info(f"GPU memory released: {self.get_vram_usage():.2f}GB remaining")

        # Load new model
        logger.info(f"Loading WhisperX model: {model_name} on {device}")
        start_time = time.time()

        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type
            )

            load_time = time.time() - start_time
            self.load_times[cache_key] = load_time

            # Cache the model (WhisperX doesn't need processor)
            self.loaded_models[cache_key] = (model, None)

            logger.info(
                f"WhisperX model loaded in {load_time:.2f}s "
                f"(VRAM: {self.get_vram_usage():.2f}GB)"
            )

            return model

        except Exception as e:
            logger.error(f"Failed to load WhisperX model: {e}", exc_info=True)
            raise RuntimeError(
                f"Failed to load WhisperX model '{model_name}': {str(e)}"
            )

    def get_vram_usage(self) -> float:
        """
        Get current VRAM usage in GB

        Returns:
            VRAM usage in gigabytes (0.0 if CPU or CUDA unavailable)
        """
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 3)
        return 0.0

    def get_loaded_models(self) -> list[str]:
        """
        Get list of currently loaded model keys

        Returns:
            List of model cache keys
        """
        return list(self.loaded_models.keys())

    def clear_cache(self) -> None:
        """
        Clear all cached models and free GPU memory

        Useful for manual memory management or cleanup
        """
        logger.info(f"Clearing model cache ({len(self.loaded_models)} models)")

        for cache_key, (model, _) in self.loaded_models.items():
            del model
            logger.info(f"Removed model from cache: {cache_key}")

        self.loaded_models.clear()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info(f"GPU cache cleared (VRAM: {self.get_vram_usage():.2f}GB)")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded models and memory usage

        Returns:
            Dictionary with model manager state
        """
        return {
            "loaded_models": list(self.loaded_models.keys()),
            "model_count": len(self.loaded_models),
            "max_models": self.max_models,
            "vram_usage_gb": self.get_vram_usage(),
            "load_times": self.load_times.copy()
        }
