#!/usr/bin/env python3
"""
单文件 WhisperX 转录脚本

使用 WhisperX 模型转录单个音频文件并保存结果

Usage:
    # 在 .venv-whisperx 环境中运行
    .venv-whisperx/Scripts/activate
    python backend/scripts/ab_test/transcribe_single_whisperx.py --audio tests/fixtures/zh_long_audio.mp3 --output backend/scripts/ab_test/ab_test_results/whisperx_zh_long_audio.json
"""

import sys
import json
import argparse
from pathlib import Path
import time

def transcribe_whisperx(audio_path: str, language: str = "zh"):
    """使用 WhisperX 模型转录音频文件"""
    try:
        import whisperx
        import torch
    except ImportError:
        print("错误: WhisperX 未安装。请在 .venv-whisperx 环境中运行此脚本。")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"WhisperX 转录")
    print(f"音频文件: {audio_path}")
    print(f"语言: {language}")
    print(f"{'='*60}\n")

    start_time = time.time()

    try:
        # 加载音频
        print("正在加载音频...")
        audio = whisperx.load_audio(audio_path)

        # 加载 WhisperX 模型 (large-v3 for Chinese)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"正在加载模型...")
        print(f"  设备: {device}")
        print(f"  计算类型: {compute_type}")

        model = whisperx.load_model(
            "large-v3",
            device=device,
            compute_type=compute_type,
            language=language
        )

        # 转录
        print(f"正在转录...")
        result = model.transcribe(audio, language=language)
        transcription_time = time.time() - start_time

        # 提取文本和分段
        segments = result.get("segments", [])
        full_text = " ".join(seg["text"] for seg in segments)

        print(f"\n✓ 转录完成!")
        print(f"  分段数量: {len(segments)}")
        print(f"  转录时间: {transcription_time:.1f}秒")
        print(f"\n转录文本:\n{'-'*60}")
        print(full_text)
        print(f"{'-'*60}\n")

        return {
            "model": "whisperx",
            "model_version": "large-v3",
            "audio_file": audio_path,
            "language": language,
            "text": full_text,
            "segments": segments,
            "transcription_time_s": transcription_time,
            "segment_count": len(segments),
            "device": device,
            "compute_type": compute_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": True,
            "error": None
        }
    except Exception as e:
        print(f"\n✗ 转录失败: {str(e)}")
        return {
            "model": "whisperx",
            "audio_file": audio_path,
            "text": "",
            "segments": [],
            "transcription_time_s": time.time() - start_time,
            "segment_count": 0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="使用 WhisperX 转录单个音频文件"
    )
    parser.add_argument(
        "--audio",
        required=True,
        help="音频文件路径 (例如: tests/fixtures/zh_long_audio.mp3)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="输出 JSON 文件路径 (例如: backend/scripts/ab_test/ab_test_results/whisperx_zh_long_audio.json)"
    )
    parser.add_argument(
        "--language",
        default="zh",
        help="音频语言 (默认: zh)"
    )

    args = parser.parse_args()

    # 检查音频文件是否存在
    if not Path(args.audio).exists():
        print(f"错误: 音频文件不存在: {args.audio}")
        sys.exit(1)

    # 转录
    result = transcribe_whisperx(args.audio, language=args.language)

    # 保存结果
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"结果已保存到: {output_path}")

    if result["success"]:
        print(f"\n{'='*60}")
        print(f"转录成功完成!")
        print(f"{'='*60}\n")
        sys.exit(0)
    else:
        print(f"\n{'='*60}")
        print(f"转录失败")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
