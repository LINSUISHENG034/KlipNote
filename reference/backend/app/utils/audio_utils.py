from typing import Optional
import os
import numpy as np
import structlog

logger = structlog.get_logger(__name__)

# 检查 WhisperX 可用性
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError as e:
    whisperx = None
    WHISPERX_AVAILABLE = False
    logger.warning(f"WhisperX not available: {e}")

# 支持的音频文件扩展名
SUPPORTED_AUDIO_EXTENSIONS = {
    '.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg',
    '.wma', '.mp4', '.avi', '.mov', '.mkv'
}


# ==============================================================================
# 辅助函数
# ==============================================================================
def validate_audio_file(file_path: str) -> None:
    """
    验证音频文件是否存在且格式支持

    Args:
        file_path: 音频文件路径

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式不支持
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in SUPPORTED_AUDIO_EXTENSIONS:
        logger.warning(f"File extension '{file_ext}' may not be supported, but will attempt to load")


def get_audio_info(file_path: str) -> dict:
    """
    获取音频文件基本信息（如果可能）

    Args:
        file_path: 音频文件路径

    Returns:
        包含音频信息的字典
    """
    info = {"file_path": file_path, "file_size": os.path.getsize(file_path)}

    try:
        import soundfile as sf
        with sf.SoundFile(file_path) as f:
            info.update({
                "duration": len(f) / f.samplerate,
                "sample_rate": f.samplerate,
                "channels": f.channels,
                "format": f.format
            })
    except Exception as e:
        logger.debug(f"Could not get audio info with soundfile: {e}")

    return info


# ==============================================================================
# 安全音频加载功能
# ==============================================================================
def safe_load_audio(file_path: str, sr: int = 16000, output_format: str = 'numpy') -> np.ndarray:
    """
    安全的音频加载函数，支持多种后端，并可以返回指定格式的数据。

    Args:
        file_path (str): 音频文件路径。
        sr (int, optional): 目标采样率。默认为 16000。
        output_format (str, optional): 输出格式 ('numpy' 或 'torch')。默认为 'numpy'。

    Raises:
        RuntimeError: 如果所有加载方法都失败。
        FileNotFoundError: 如果音频文件不存在。
        ValueError: 如果参数无效。

    Returns:
        np.ndarray or torch.Tensor: 加载后的音频数据。
    """
    # 参数验证
    if output_format not in ['numpy', 'torch']:
        raise ValueError(f"Unsupported output_format: {output_format}. Must be 'numpy' or 'torch'.")

    if not file_path or not isinstance(file_path, str):
        raise ValueError("file_path must be a non-empty string")

    if sr <= 0:
        raise ValueError("Sample rate must be positive")

    # 验证文件
    validate_audio_file(file_path)

    # 记录音频文件信息
    audio_info = get_audio_info(file_path)
    logger.debug(f"Loading audio file: '{file_path}' with target sample rate: {sr}",
                extra={"audio_info": audio_info})

    audio_np = None

    # 方法1: 尝试使用 librosa (最可靠)
    try:
        import librosa
        audio_np, _ = librosa.load(file_path, sr=sr, mono=True)
        logger.debug(f"Audio loaded successfully with librosa. Shape: {audio_np.shape}")
    except Exception as e:
        logger.warning(f"Librosa loading failed: {e}")

    # 方法2: 尝试使用 WhisperX 的 load_audio (如果可用)
    if audio_np is None and WHISPERX_AVAILABLE:
        try:
            audio_np = whisperx.load_audio(file_path)
            if sr != 16000:
                import librosa
                audio_np = librosa.resample(audio_np, orig_sr=16000, target_sr=sr)
            logger.debug(f"Audio loaded successfully with WhisperX. Shape: {audio_np.shape}")
        except Exception as e:
            logger.warning(f"WhisperX load_audio failed: {e}")

    # 方法3: 尝试使用 torchaudio
    if audio_np is None:
        try:
            import torchaudio
            import torchaudio.transforms as T
            try:
                torchaudio.set_audio_backend('soundfile')
            except:
                pass

            waveform, sample_rate = torchaudio.load(file_path)
            if sample_rate != sr:
                resampler = T.Resample(orig_freq=sample_rate, new_freq=sr)
                waveform = resampler(waveform)

            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            audio_np = waveform.numpy().flatten()
            logger.debug(f"Audio loaded successfully with torchaudio. Shape: {audio_np.shape}")
        except Exception as e:
            logger.warning(f"Torchaudio loading failed: {e}")

    # 方法4: 回退到 soundfile
    if audio_np is None:
        try:
            import soundfile as sf
            audio_np, sample_rate = sf.read(file_path, dtype='float32')
            if audio_np.ndim > 1:
                audio_np = audio_np.mean(axis=1)
            if sample_rate != sr:
                import librosa
                audio_np = librosa.resample(y=audio_np, orig_sr=sample_rate, target_sr=sr)
            logger.debug(f"Audio loaded successfully with soundfile. Shape: {audio_np.shape}")
        except Exception as e:
            logger.warning(f"Soundfile loading failed: {e}")

    # 检查是否成功加载
    if audio_np is None:
        error_message = f"All available audio loading methods failed for: {file_path}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # 根据需要转换输出格式
    if output_format == 'torch':
        import torch
        return torch.from_numpy(audio_np)
    
    return audio_np


# ==============================================================================
# 便利函数
# ==============================================================================
def load_audio_with_fallback(file_path: str, sr: int = 16000,
                           max_retries: int = 3) -> Optional[np.ndarray]:
    """
    带重试机制的音频加载函数，失败时返回 None 而不是抛出异常

    Args:
        file_path: 音频文件路径
        sr: 目标采样率
        max_retries: 最大重试次数

    Returns:
        加载的音频数组，失败时返回 None
    """
    for attempt in range(max_retries):
        try:
            return safe_load_audio(file_path, sr)
        except Exception as e:
            logger.warning(f"Audio loading attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts to load audio failed for: {file_path}")
                return None
    return None