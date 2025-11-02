#!/usr/bin/env python3
"""
测试脚本：使用streaming_whisperx_provider转录音频文件
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from backend.ai_services.providers.streaming_whisperx_provider import transcribe_file_stream
from backend.app.schemas.transcription import TranscriptionConfig


async def test_transcription():
    """测试音频转录功能"""
    # 音频文件路径
    audio_file = r"C:\Users\LINSUISHENG034\Desktop\Weixin Videos2025-10-28_185213_864\Weixin Videos2025-10-28_185213_864.aac"
    
    # 检查音频文件是否存在
    if not os.path.exists(audio_file):
        print(f"错误：音频文件不存在: {audio_file}")
        return
    
    # 生成输出文件路径
    audio_path = Path(audio_file)
    output_file = audio_path.parent / f"{audio_path.stem}.txt"
    
    print(f"音频文件: {audio_file}")
    print(f"输出文件: {output_file}")
    print("=" * 60)
    
    # 创建转录配置
    config = TranscriptionConfig(
        model_name="large-v3",           # 可选模型["tiny", "base", "small", "medium", "large-v2", "large-v3"]
        language="zh",                 # 中文转录
        batch_size=1,                  # 批处理大小
        enable_alignment=False,         # 禁用词级对齐
        enable_diarization=False,      # 禁用说话人分离（单人音频）
        vad_method="silero",          # VAD方法
        vad_threshold=0.3,            # VAD阈值
        min_silence_duration_ms=700,   # 最小静音时长
        max_chunk_duration_s=30       # 最大分块时长
    )
    
    # 存储转录结果
    segments = []
    full_text = []
    
    try:
        print("开始转录...")
        print("-" * 40)
        
        # 执行转录
        async for result in transcribe_file_stream(audio_file, config):
            result_type = result.get("type")
            
            if result_type == "progress":
                stage = result.get("stage")
                message = result.get("message")
                print(f"[进度] {stage}: {message}")
                
            elif result_type == "segment":
                segment_id = result.get("segment_id")
                start = result.get("start")
                end = result.get("end")
                text = result.get("text")
                
                segments.append(result)
                full_text.append(text)
                
                print(f"[分段 {segment_id:03d}] {start:7.3f}s - {end:7.3f}s: {text}")
                
            elif result_type == "error":
                error_msg = result.get("message")
                print(f"[错误] {error_msg}")
                return
                
        print("-" * 40)
        print("转录完成！")
        
        # 保存转录结果到文件
        print(f"\n正在保存转录结果到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入完整文本
            f.write("完整转录文本:\n")
            f.write("=" * 50 + "\n")
            f.write(" ".join(full_text) + "\n\n")
            
            # 写入详细分段信息
            f.write("详细分段信息:\n")
            f.write("=" * 50 + "\n")
            for segment in segments:
                f.write(f"[{segment['start']:7.3f}s - {segment['end']:7.3f}s] {segment['text']}\n")
            
            # 如果有词级信息，也写入
            if segments and segments[0].get('words'):
                f.write("\n词级对齐信息:\n")
                f.write("=" * 50 + "\n")
                for segment in segments:
                    f.write(f"\n分段 {segment['segment_id']}: {segment['text']}\n")
                    for word_info in segment.get('words', []):
                        word = word_info.get('word', '')
                        start = word_info.get('start', 0)
                        end = word_info.get('end', 0)
                        score = word_info.get('score', 0)
                        f.write(f"  {word} [{start:.3f}s-{end:.3f}s] (置信度:{score:.3f})\n")
        
        print(f"转录结果已保存到: {output_file}")
        
        # 输出统计信息
        total_duration = segments[-1]['end'] if segments else 0
        total_segments = len(segments)
        total_words = sum(len(seg.get('words', [])) for seg in segments)
        
        print(f"\n统计信息:")
        print(f"  总时长: {total_duration:.2f} 秒")
        print(f"  分段数: {total_segments}")
        print(f"  总词数: {total_words}")
        print(f"  输出文件大小: {output_file.stat().st_size} 字节")
        
    except Exception as e:
        print(f"转录过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("WhisperX 流式转录测试脚本")
    print("=" * 60)
    
    # 运行异步转录测试
    asyncio.run(test_transcription())


if __name__ == "__main__":
    main()