import asyncio
import os
import sys
import gc
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

import torch
import whisperx
from whisperx.diarize import DiarizationPipeline
import structlog
from app.core.config import settings
from app.core.enums import ModelStatus

logger = structlog.get_logger(__name__)

# ==============================================================================
# 环境与路径设置
# ==============================================================================
def setup_environment():
    """配置模型缓存目录和Python路径，确保使用项目指定的依赖和模型。"""
    hf_home = Path(settings.HF_HOME)
    hf_home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_home.absolute())
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(hf_home.absolute())
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    # TORCH_HOME is useful for other torch utilities, let's keep it pointing inside
    torch_home = hf_home / "torch"
    torch_home.mkdir(parents=True, exist_ok=True)
    os.environ["TORCH_HOME"] = str(torch_home.absolute())
    
    # Adjust path if whisperx is not directly in sys.path
    whisperx_path = Path(__file__).parent.parent / "whisperx"
    if str(whisperx_path.absolute()) not in sys.path:
        sys.path.insert(0, str(whisperx_path.absolute()))
        logger.info(f"Added custom WhisperX path to sys.path: {whisperx_path.absolute()}")

# 设置模型缓存
setup_environment()

# ==============================================================================
# 1. Model Bundle Definition
# ==============================================================================

class WhisperXModelBundle:
    """模型的容器，包含ASR、对齐和说话人分离模型。"""
    def __init__(self, device: str, compute_type: str):
        self.device = device
        self.compute_type = compute_type
        
        # Main ASR pipeline (which includes VAD)
        self.asr_pipeline: Optional[whisperx.asr.FasterWhisperPipeline] = None
        
        # Cached sub-models
        self.align_models: Dict[str, Tuple[Any, Any]] = {}
        self.diarize_model: Optional[DiarizationPipeline] = None
        
        # Locks for thread-safe lazy loading of sub-models
        self._align_lock = asyncio.Lock()
        self._diarize_lock = asyncio.Lock()

    async def get_or_load_align_model(self, language_code: str) -> Optional[Tuple[Any, Any]]:
        """
        Asynchronously gets or loads a language-specific alignment model.
        Loading is done in a separate thread to avoid blocking the event loop.
        """
        if language_code in self.align_models:
            return self.align_models[language_code]

        async with self._align_lock:
            # Double-check after acquiring the lock
            if language_code in self.align_models:
                return self.align_models[language_code]
            
            logger.info(f"Alignment model for '{language_code}' not in cache, loading...")
            try:
                align_model, metadata = await asyncio.to_thread(
                    whisperx.load_align_model, language_code, device=self.device
                )
                self.align_models[language_code] = (align_model, metadata)
                logger.info(f"Alignment model for '{language_code}' loaded and cached.")
                return self.align_models[language_code]
            except Exception as e:
                logger.error(f"Failed to load alignment model for '{language_code}'", error=e, exc_info=True)
                return None

    async def get_or_load_diarize_model(self) -> Optional[DiarizationPipeline]:
        """
        Asynchronously gets or loads the diarization model.
        Loading is done in a separate thread.
        """
        if self.diarize_model:
            return self.diarize_model
            
        async with self._diarize_lock:
            # Double-check after acquiring the lock
            if self.diarize_model:
                return self.diarize_model

            logger.info("Diarization model not in cache, loading...")
            try:
                # DiarizationPipeline uses HF_TOKEN from settings if needed
                diarize_model = await asyncio.to_thread(
                    DiarizationPipeline, device=self.device, use_auth_token=settings.HUGGINGFACE_TOKEN
                )
                self.diarize_model = diarize_model
                logger.info("Diarization model loaded and cached.")
                return self.diarize_model
            except Exception as e:
                logger.error("Failed to load diarization model", error=e, exc_info=True)
                return None

# ==============================================================================
# 2. Model Manager Implementation
# ==============================================================================

class ModelManager:
    """
    A centralized, asynchronous manager for loading and caching AI model bundles.
    It ensures that each model bundle is loaded only once and handles concurrent
    requests safely. It also re-implements smart device/precision selection.
    """
    def __init__(self):
        self._model_cache: Dict[str, WhisperXModelBundle] = {}
        self._model_locks: Dict[str, asyncio.Lock] = {}
        self._model_status: Dict[str, ModelStatus] = {} # type: ignore

    def get_model_status(self, model_name: str) -> ModelStatus:
        """Gets the current loading status of a given model."""
        return self._model_status.get(model_name, ModelStatus.NOT_LOADED)

    def _get_optimal_device_config(self) -> Tuple[str, str]:
        """检测最佳可用设备和计算类型。"""
        try:
            if torch.cuda.is_available() and settings.WHISPERX_DEVICE.lower() == "cuda":
                device = "cuda"
                if settings.WHISPERX_COMPUTE_TYPE == "auto":
                    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    compute_type = "float16" if gpu_memory_gb >= 8.0 else "int8"
                    logger.info(f"Auto-detected GPU with {gpu_memory_gb:.1f}GB VRAM, selected compute_type: {compute_type}")
                else:
                    compute_type = settings.WHISPERX_COMPUTE_TYPE
                return device, compute_type
        except Exception as e:
            logger.warning(f"GPU detection failed, falling back to CPU. Error: {e}")
        
        logger.info("Using CPU for inference.")
        return "cpu", "int8"

    async def get_model_bundle(self, model_name: str) -> WhisperXModelBundle:
        """
        异步检索模型包。如果不在缓存中，则加载主ASR模型。
        此方法现在会更新模型的加载状态。
        """
        lock = self._model_locks.setdefault(model_name, asyncio.Lock())

        async with lock:
            if model_name in self._model_cache:
                logger.debug("Model bundle found in cache", model_name=model_name)
                self._model_status[model_name] = ModelStatus.LOADED
                return self._model_cache[model_name]

            logger.info("Model bundle not in cache, creating...", model_name=model_name)
            self._model_status[model_name] = ModelStatus.LOADING
            device, compute_type = self._get_optimal_device_config()
            
            bundle = WhisperXModelBundle(device, compute_type)

            try:
                # Load the main ASR model in a separate thread with a timeout
                load_task = asyncio.to_thread(
                    whisperx.load_model,
                    model_name,
                    device,
                    compute_type=compute_type,
                    language=None,  # Load with multilingual support
                    asr_options={"suppress_numerals": True}
                )
                asr_pipeline = await asyncio.wait_for(load_task, timeout=settings.MODEL_LOAD_TIMEOUT_S)
                bundle.asr_pipeline = asr_pipeline
                self._model_cache[model_name] = bundle
                self._model_status[model_name] = ModelStatus.LOADED
                logger.info("Model bundle created and cached successfully", model_name=model_name)
                return bundle
            except asyncio.TimeoutError as e:
                logger.error(
                    "Timeout occurred while loading main ASR model", 
                    model_name=model_name, 
                    timeout_s=settings.MODEL_LOAD_TIMEOUT_S,
                    exc_info=True
                )
                raise RuntimeError(f"Timed out after {settings.MODEL_LOAD_TIMEOUT_S}s waiting for model '{model_name}' to load.") from e
            except Exception as e:
                logger.error("Failed to load main ASR model", model_name=model_name, error=e, exc_info=True)
                # Ensure we don't cache a partial/failed bundle
                self._model_status[model_name] = ModelStatus.FAILED
                logger.error("Failed to load main ASR model", model_name=model_name, error=str(e), exc_info=True)
                if model_name in self._model_cache:
                    del self._model_cache[model_name]
                if isinstance(e, asyncio.TimeoutError):
                    raise RuntimeError(f"Timed out after {settings.MODEL_LOAD_TIMEOUT_S}s waiting for model '{model_name}' to load.") from e
                raise RuntimeError(f"Could not load whisperX model '{model_name}'") from e

    async def unload_model_bundle(self, model_name: str):
        """
        从缓存中移除模型并清理GPU内存。
        """
        if model_name in self._model_cache:
            del self._model_cache[model_name]
            if torch.cuda.is_available():
                gc.collect()
                torch.cuda.empty_cache()
            logger.info("Unloaded model bundle and cleared cache", model_name=model_name)

# --- Singleton Instance ---
model_manager = ModelManager()
