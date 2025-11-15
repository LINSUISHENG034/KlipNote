#!/usr/bin/env python3
"""
单文件 BELLE-2 转录脚本

使用 BELLE-2 模型转录单个音频文件并保存结果

Usage:
    # 在主 .venv 环境中运行
    .venv/Scripts/activate
    python backend/scripts/ab_test/transcribe_single_belle2.py --audio tests/fixtures/zh_long_audio.mp3 --output backend/scripts/ab_test/ab_test_results/belle2_zh_long_audio.json
"""

import sys
import json
import argparse
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def transcribe_belle2(audio_path: str, language: str = "zh"):
    """使用 BELLE-2 模型转录音频文件"""
    try:
        from app.ai_services.belle2_service import Belle2Service
    except ImportError as e:
        print(f"错误: 无法导入 Belle2Service: {e}")
        print("请确保在主 .venv 环境中运行此脚本。")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"BELLE-2 转录")
    print(f"音频文件: {audio_path}")
    print(f"语言: {language}")
    print(f"{'='*60}\n")

    service = Belle2Service()
    start_time = time.time()

    try:
        print("正在转录...")
        segments = service.transcribe(audio_path, language=language)
        transcription_time = time.time() - start_time

        # 合并分段文本
        full_text = " ".join(seg["text"] for seg in segments)

        print(f"\n✓ 转录完成!")
        print(f"  分段数量: {len(segments)}")
        print(f"  转录时间: {transcription_time:.1f}秒")
        print(f"\n转录文本:\n{'-'*60}")
        print(full_text)
        print(f"{'-'*60}\n")

        return {
            "model": "belle2",
            "model_version": "BELLE-2-Whisper-large-v3-zh",
            "audio_file": audio_path,
            "language": language,
            "text": full_text,
            "segments": segments,
            "transcription_time_s": transcription_time,
            "segment_count": len(segments),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": True,
            "error": None
        }
    except Exception as e:
        print(f"\n✗ 转录失败: {str(e)}")
        return {
            "model": "belle2",
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
        description="使用 BELLE-2 转录单个音频文件"
    )
    parser.add_argument(
        "--audio",
        required=True,
        help="音频文件路径 (例如: tests/fixtures/zh_long_audio.mp3)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="输出 JSON 文件路径 (例如: backend/scripts/ab_test/ab_test_results/belle2_zh_long_audio.json)"
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
    result = transcribe_belle2(args.audio, language=args.language)

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
