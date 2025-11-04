import asyncio
from typing import Dict, Any, AsyncGenerator
import structlog

from .base import ITranscriber
from ai_services.model_manager import model_manager
from app.schemas.transcription import TranscriptionConfig
from app.utils.audio_utils import safe_load_audio

logger = structlog.get_logger(__name__)

try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError as e:
    whisperx = None
    WHISPERX_AVAILABLE = False
    logger.warning(f"WhisperX not available, streaming transcriber will use mock implementation. Error: {e}")

# ==============================================================================
# 结果格式化和流式处理支持
# ==============================================================================
class ResultFormatter:
    """将处理结果格式化为标准字典。"""
    def format_segment(self, raw_segment: Dict, segment_id: int, time_offset: float) -> Dict:
        """格式化一个转录分段。"""
        start_time = raw_segment.get("start", 0) + time_offset
        end_time = raw_segment.get("end", 0) + time_offset
        return {
            "type": "segment",
            "segment_id": segment_id,
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "text": raw_segment.get("text", "").strip(),
            "words": [
                {
                    "word": w.get("word", ""),
                    "start": round(w.get("start", 0) + time_offset, 3),
                    "end": round(w.get("end", 0) + time_offset, 3),
                    "score": round(w.get("score", 0), 3),
                    "speaker": w.get("speaker") # Add speaker info if present
                } for w in raw_segment.get("words", [])
            ]
        }

    def format_progress(self, stage: str, message: str, **kwargs) -> Dict:
        """格式化一个进度更新。"""
        return {"type": "progress", "stage": stage, "message": message, **kwargs}

    def format_error(self, error_message: str, chunk_id: int = None) -> Dict:
        """格式化一个错误信息。"""
        return {"type": "error", "message": error_message, "chunk_id": chunk_id}

class EnhancedTranscriptionProcessor:
    """
    增强的转录处理器，集成了原始`streaming_whisperx`的核心功能，
    同时使用重构后的ModelManager进行模型管理。
    """
    def __init__(self, file_path: str, config: TranscriptionConfig):
        self.file_path = file_path
        self.config = config
        self.formatter = ResultFormatter()

    async def process_with_progress(self):
        """
        执行完整的转录流程，支持进度报告：
        1. 加载音频
        2. 转录
        3. (可选) 对齐
        4. (可选) 说话人分离
        """
        try:
            yield self.formatter.format_progress("initialization", "Initializing transcriber...")
            
            # 1. 获取模型bundle
            bundle = await model_manager.get_model_bundle(self.config.model_name)
            if not bundle or not bundle.asr_pipeline:
                yield self.formatter.format_error("ASR model pipeline could not be loaded.")
                return

            # 2. 加载音频文件
            yield self.formatter.format_progress("loading_audio", f"Loading audio file: {self.file_path}")
            audio = await asyncio.to_thread(safe_load_audio, self.file_path, output_format='numpy')
            yield self.formatter.format_progress("audio_loaded", f"Audio loaded successfully. Duration: {len(audio) / 16000:.2f}s")

            # 3. 执行ASR转录
            yield self.formatter.format_progress("transcription_started", "Starting ASR transcription...")
            language_for_asr = self.config.language if self.config.language != "auto" else None
            result = await asyncio.to_thread(
                bundle.asr_pipeline.transcribe,
                audio,
                batch_size=self.config.batch_size,
                language=language_for_asr
            )
            yield self.formatter.format_progress("transcription_finished", "ASR transcription completed.")

            # 4. (可选) 执行对齐
            if self.config.enable_alignment and result.get("segments"):
                yield self.formatter.format_progress("alignment_started", "Aligning transcription results...")
                detected_language = result.get("language", self.config.language if self.config.language != "auto" else "en")
                
                align_model_tuple = await bundle.get_or_load_align_model(detected_language)
                if align_model_tuple:
                    align_model, align_metadata = align_model_tuple
                    result = await asyncio.to_thread(
                        whisperx.align,
                        result["segments"], align_model, align_metadata, audio, bundle.device
                    )
                    yield self.formatter.format_progress("alignment_finished", "Alignment complete.")
                else:
                    yield self.formatter.format_progress("alignment_skipped", f"Alignment skipped for language '{detected_language}'.")

            # 5. (可选) 执行说话人分离
            if self.config.enable_diarization and result.get("segments"):
                yield self.formatter.format_progress("diarization_started", "Assigning speaker labels...")
                diarize_model = await bundle.get_or_load_diarize_model()
                
                if diarize_model:
                    diarize_segments = await asyncio.to_thread(
                        diarize_model,
                        audio,
                        min_speakers=self.config.min_speakers,
                        max_speakers=self.config.max_speakers
                    )
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    yield self.formatter.format_progress("diarization_finished", "Speaker diarization complete.")
                else:
                    yield self.formatter.format_progress("diarization_skipped", "Diarization skipped due to model loading failure.")

            # 6. 输出最终分段结果
            for i, segment in enumerate(result.get("segments", [])):
                yield self.formatter.format_segment(segment, segment_id=i, time_offset=0)

            yield self.formatter.format_progress("completed", "Transcription finished successfully.")

        except Exception as e:
            logger.error(f"Failed to process file {self.file_path}: {e}", exc_info=True)
            yield self.formatter.format_error(f"Processing failed: {e}")

class WhisperXStreamingASR(ITranscriber):
    """
    WhisperX 流式转录服务提供者
    集成了增强的转录处理器，支持进度报告和流式输出
    """

    def __init__(self):
        logger.info("Initialized WhisperXStreamingASR provider.")

    async def transcribe(self, file_path: str, config: TranscriptionConfig) -> AsyncGenerator[Dict, None]:
        """
        执行转录任务，支持流式进度报告
        
        Args:
            file_path: 音频文件路径
            config: 转录配置
            
        Yields:
            转录结果字典，包含进度更新、分段结果和错误信息
        """
        processor = EnhancedTranscriptionProcessor(file_path, config)
        async for result in processor.process_with_progress():
            yield result

    def get_provider_name(self) -> str:
        return "whisperx_streaming"

    def get_supported_languages(self) -> list[str]:
        # This could be dynamic in the future
        return ["en", "es", "fr", "de", "it", "ja", "zh", "auto"]

# ==============================================================================
# 公共入口函数
# ==============================================================================
async def transcribe_file_stream(file_path: str, config: TranscriptionConfig):
    """
    公共入口函数，用于流式转录音频文件
    
    Args:
        file_path: 音频文件路径
        config: 转录配置
        
    Yields:
        转录结果字典，包含进度更新、分段结果和错误信息
    """
    processor = EnhancedTranscriptionProcessor(file_path, config)
    async for result in processor.process_with_progress():
        yield result
