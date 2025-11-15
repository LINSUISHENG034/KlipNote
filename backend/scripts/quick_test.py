#!/usr/bin/env python3
"""
Quick test: BELLE-2 + WhisperX on single file
Tests the complete workflow before running full benchmark
"""
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.optimization.whisperx_optimizer import WhisperXOptimizer

def main():
    print('='*70)
    print('QUICK TEST: mandarin-test.mp3 (BELLE-2 + WhisperX)')
    print('='*70)

    # Initialize services
    print('\n[1/4] Initializing BELLE-2 service...')
    belle2 = Belle2Service(device='cuda')
    print('  ✓ BELLE-2 ready')

    print('\n[2/4] Initializing WhisperX optimizer...')
    whisperx_opt = WhisperXOptimizer()
    print('  ✓ WhisperX ready')

    # Transcribe
    audio_path = '../tests/fixtures/mandarin-test.mp3'
    print(f'\n[3/4] Transcribing with BELLE-2: {audio_path}')
    t_start = time.time()
    segments = belle2.transcribe(audio_path, language='zh')
    t_time = time.time() - t_start
    print(f'  ✓ Transcription complete: {len(segments)} segments in {t_time:.2f}s')

    # Optimize
    print(f'\n[4/4] Optimizing with WhisperX...')
    o_start = time.time()
    result = whisperx_opt.optimize(segments, audio_path, language='zh')
    o_time = time.time() - o_start
    print(f'  ✓ Optimization complete: {len(result.segments)} segments in {o_time:.2f}s')

    # Calculate metrics
    overhead_pct = (o_time / t_time) * 100 if t_time > 0 else 0
    total_time = t_time + o_time

    print('\n' + '='*70)
    print('RESULTS SUMMARY')
    print('='*70)
    print(f'Transcription time:  {t_time:.2f}s')
    print(f'Optimization time:   {o_time:.2f}s')
    print(f'Total time:          {total_time:.2f}s')
    print(f'Overhead:            {overhead_pct:.2f}%')
    print(f'Threshold:           25.00%')
    print(f'Status:              {"✓ PASS" if overhead_pct < 25.0 else "✗ FAIL"}')
    print('='*70)
    print(f'\nSegments before: {len(segments)}')
    print(f'Segments after:  {len(result.segments)}')
    print(f'Optimizer:       {result.optimizer_name}')
    print(f'Metrics:         {result.metrics}')
    print('='*70)

if __name__ == '__main__':
    main()
