# Story 3.2c: BELLE-2 vs WhisperX A/B Testing Framework

## Overview

This directory contains the comprehensive A/B testing framework for comparing BELLE-2 and WhisperX Chinese transcription models across 5 key dimensions.

## Test Scripts

### 1. `ab_test_accuracy.py` - Accuracy Comparison (CER/WER)

Measures transcription accuracy using Character Error Rate (CER) and Word Error Rate (WER) metrics.

**Requires:** Ground truth transcripts in `tests/fixtures/ground_truth.json` or `tests/fixtures/mandarin-test-reference.txt`

```bash
# BELLE-2
python scripts/ab_test_accuracy.py --test-dir tests/fixtures --model belle2 --output belle2_accuracy.json

# WhisperX (in .venv-whisperx)
python scripts/ab_test_accuracy.py --test-dir tests/fixtures --model whisperx --output whisperx_accuracy.json
```

**Metrics:**
- Average CER (%)
- Average WER (%)
- Per-file accuracy scores

---

### 2. `ab_test_segments.py` - Segment Length Compliance

Evaluates compliance with subtitle standards (1-7 seconds, <200 characters).

```bash
python scripts/ab_test_segments.py --test-dir tests/fixtures --model belle2 --output belle2_segments.json
python scripts/ab_test_segments.py --test-dir tests/fixtures --model whisperx --output whisperx_segments.json
```

**Metrics:**
- % segments meeting 1-7s constraint
- % segments meeting <200 char constraint
- % segments meeting both constraints
- Mean/median/P95 segment durations
- Character count statistics

---

### 3. `ab_test_gibberish.py` - Repetition/Gibberish Detection

Detects repetitive "gibberish loops" and transcription quality issues.

```bash
python scripts/ab_test_gibberish.py --test-dir tests/fixtures --model belle2 --output belle2_gibberish.json
python scripts/ab_test_gibberish.py --test-dir tests/fixtures --model whisperx --output whisperx_gibberish.json
```

**Metrics:**
- Overall quality score (0-100)
- Repetition score (% of text that is repetitive)
- Gibberish score (excessive char repetition, nonsense patterns)
- Files with major quality issues

---

### 4. `ab_test_performance.py` - Performance Benchmarking

Measures GPU processing speed using Real-Time Factor (RTF) and throughput.

**RTF:** processing_time / audio_duration
- RTF < 1.0 = faster than real-time
- RTF = 1.0 = real-time processing
- RTF > 1.0 = slower than real-time

```bash
python scripts/ab_test_performance.py --test-dir tests/fixtures --model belle2 --output belle2_performance.json
python scripts/ab_test_performance.py --test-dir tests/fixtures --model whisperx --output whisperx_performance.json
```

**Metrics:**
- Average RTF
- Throughput (x real-time)
- Processing time vs audio duration
- RTF by file size category (small/medium/large)

---

### 5. `ab_test_memory.py` - VRAM Usage Monitoring

Monitors GPU memory usage during transcription.

```bash
python scripts/ab_test_memory.py --test-dir tests/fixtures --model belle2 --output belle2_memory.json
python scripts/ab_test_memory.py --test-dir tests/fixtures --model whisperx --output whisperx_memory.json
```

**Metrics:**
- Peak allocated memory (GB)
- Peak reserved memory (GB)
- Average peak memory across files
- Memory usage over time (sampled at 100ms intervals)

---

### 6. `consolidate_ab_results.py` - Results Consolidation

Consolidates all test results and generates weighted comparison with final recommendation.

```bash
python scripts/consolidate_ab_results.py \
    --belle2-accuracy belle2_accuracy.json \
    --belle2-segments belle2_segments.json \
    --belle2-gibberish belle2_gibberish.json \
    --belle2-performance belle2_performance.json \
    --belle2-memory belle2_memory.json \
    --whisperx-accuracy whisperx_accuracy.json \
    --whisperx-segments whisperx_segments.json \
    --whisperx-gibberish whisperx_gibberish.json \
    --whisperx-performance whisperx_performance.json \
    --whisperx-memory whisperx_memory.json \
    --output consolidated_comparison.json
```

**Weighted Scoring (from Epic 3 requirements):**
- Accuracy (CER/WER): 30%
- Segment compliance: 25%
- Gibberish elimination: 20%
- Performance: 15%
- Memory efficiency: 10%

**Output:**
- Dimension-by-dimension comparison
- Overall winner with confidence level
- Recommendation with supporting reasons
- Epic 3 path forward

---

## Quick Start: Run All Tests

### Option 1: Automated Script (Recommended)

**Windows:**
```cmd
backend\scripts\run_all_ab_tests.bat
```

**Linux/macOS:**
```bash
bash backend/scripts/run_all_ab_tests.sh
```

**With file limit (for quick testing):**
```cmd
backend\scripts\run_all_ab_tests.bat --limit 2
```

This will:
1. Run all 5 tests for BELLE-2 (in main `.venv`)
2. Run all 5 tests for WhisperX (in `.venv-whisperx`)
3. Consolidate results and generate comparison report

---

### Option 2: Manual Execution

**Step 1: BELLE-2 Tests (main .venv)**
```bash
cd backend
source .venv/Scripts/activate  # or .venv\Scripts\activate.bat on Windows

python scripts/ab_test_accuracy.py --test-dir ../tests/fixtures --model belle2 --output ab_test_results/belle2_accuracy.json
python scripts/ab_test_segments.py --test-dir ../tests/fixtures --model belle2 --output ab_test_results/belle2_segments.json
python scripts/ab_test_gibberish.py --test-dir ../tests/fixtures --model belle2 --output ab_test_results/belle2_gibberish.json
python scripts/ab_test_performance.py --test-dir ../tests/fixtures --model belle2 --output ab_test_results/belle2_performance.json
python scripts/ab_test_memory.py --test-dir ../tests/fixtures --model belle2 --output ab_test_results/belle2_memory.json

deactivate
```

**Step 2: WhisperX Tests (.venv-whisperx)**
```bash
source .venv-whisperx/Scripts/activate

python scripts/ab_test_accuracy.py --test-dir ../tests/fixtures --model whisperx --output ab_test_results/whisperx_accuracy.json
python scripts/ab_test_segments.py --test-dir ../tests/fixtures --model whisperx --output ab_test_results/whisperx_segments.json
python scripts/ab_test_gibberish.py --test-dir ../tests/fixtures --model whisperx --output ab_test_results/whisperx_gibberish.json
python scripts/ab_test_performance.py --test-dir ../tests/fixtures --model whisperx --output ab_test_results/whisperx_performance.json
python scripts/ab_test_memory.py --test-dir ../tests/fixtures --model whisperx --output ab_test_results/whisperx_memory.json

deactivate
```

**Step 3: Consolidate Results**
```bash
source .venv/Scripts/activate

python scripts/consolidate_ab_results.py \
    --belle2-accuracy ab_test_results/belle2_accuracy.json \
    --belle2-segments ab_test_results/belle2_segments.json \
    --belle2-gibberish ab_test_results/belle2_gibberish.json \
    --belle2-performance ab_test_results/belle2_performance.json \
    --belle2-memory ab_test_results/belle2_memory.json \
    --whisperx-accuracy ab_test_results/whisperx_accuracy.json \
    --whisperx-segments ab_test_results/whisperx_segments.json \
    --whisperx-gibberish ab_test_results/whisperx_gibberish.json \
    --whisperx-performance ab_test_results/whisperx_performance.json \
    --whisperx-memory ab_test_results/whisperx_memory.json \
    --output ab_test_results/consolidated_comparison.json
```

---

## Test Audio Corpus

Located in: `tests/fixtures/`

**Available test files:**
- `mandarin-test.mp3` (5.3MB) - Primary test with ground truth transcript
- `zh_short_audio.mp3` (500KB) - Short form test
- `zh_medium_audio.mp3` (5.3MB) - Medium form test
- `zh_long_audio.mp3` (76MB) - Long form test (~40+ minutes)

**Ground truth transcripts:**
- `mandarin-test-reference.txt` - Reference transcript for accuracy testing
- `ground_truth.json` - JSON format (optional, for multiple files)

---

## Output Format

All test scripts generate JSON output with the following structure:

```json
{
  "model": "belle2|whisperx",
  "test_dir": "tests/fixtures",
  "timestamp": "2025-11-15 10:30:00",
  "test_files_count": 4,
  "summary": {
    // Aggregate metrics for the dimension
  },
  "results": [
    {
      "file": "mandarin-test.mp3",
      "transcription": { /* ... */ },
      "metrics": { /* dimension-specific metrics */ }
    }
  ]
}
```

---

## Prerequisites

### Main Environment (`.venv`) - BELLE-2
- Python 3.12
- transformers
- faster-whisper
- torch (CUDA 11.8)
- jiwer (for CER/WER)
- numpy, librosa, scipy

### WhisperX Environment (`.venv-whisperx`)
- Python 3.12
- PyTorch 2.5+ with CUDA 12.1
- WhisperX
- pyannote.audio
- jiwer, numpy, librosa

**Installation:**
```bash
# Main .venv (already configured from Stories 3.1, 3.2a)
cd backend
source .venv/Scripts/activate
pip install jiwer librosa scipy numpy

# WhisperX .venv (created in Story 3.2c AC #1)
uv venv .venv-whisperx --python 3.12
source .venv-whisperx/Scripts/activate
uv pip install torch>=2.5.0 torchaudio --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu121/
uv pip install "numpy<2.1.0" whisperx jiwer librosa scipy
```

---

## Interpreting Results

### Consolidated Comparison Report

The `consolidated_comparison.json` provides:

1. **Dimension-by-dimension winners:**
   - Accuracy (CER/WER): Lower is better
   - Segment compliance: Higher is better (target: ≥95%)
   - Gibberish quality: Higher is better (target: ≥70/100)
   - Performance (RTF): Lower is better (target: <1.0)
   - Memory: Lower is better

2. **Weighted overall score:**
   - Combines all dimensions using Epic 3 priorities
   - Range: 0-100 per model
   - Higher score = better overall performance

3. **Recommendation:**
   - Recommended model (BELLE-2 or WhisperX)
   - Confidence level (high/medium/low)
   - Supporting reasons
   - Epic 3 path forward

### Example Output:
```json
{
  "weighted_score": {
    "scores": {
      "belle2": 72.5,
      "whisperx": 81.3
    },
    "overall_winner": "whisperx"
  },
  "recommendation": {
    "recommended_model": "whisperx",
    "confidence": "high",
    "reasons": [
      "Superior accuracy (lower CER/WER)",
      "Better segment length compliance",
      "Faster processing (lower RTF)"
    ],
    "epic_3_path": "Proceed with WHISPERX as primary transcription model"
  }
}
```

---

## Next Steps (Story AC #5 & #6)

After running all tests:

1. **Review consolidated results:**
   ```bash
   cat ab_test_results/consolidated_comparison.json | python -m json.tool
   ```

2. **Create Phase Gate Decision Report (AC #5):**
   - Document in `docs/phase-gate-story-3-2c.md`
   - Include winner, confidence, supporting data
   - Weighted comparison analysis
   - Recommendation for Epic 3 path forward

3. **Define Epic 3 Path Forward (AC #6):**
   - **If BELLE-2 wins:** Proceed with Stories 3.3-3.5 (HeuristicOptimizer)
   - **If WhisperX wins:** Skip Stories 3.3-3.5, proceed to Story 3.6 (QualityValidator)
   - Update `docs/sprint-artifacts/tech-spec-epic-3.md` with decision
   - Update `docs/sprint-artifacts/sprint-status.yaml` to reflect path

---

## Troubleshooting

### WhisperX imports failing
```bash
# Ensure .venv-whisperx is activated
source .venv-whisperx/Scripts/activate
python -c "import whisperx; import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### CUDA not available
- Verify GPU drivers installed
- Check CUDA toolkit version matches PyTorch
- Confirm torch.cuda.is_available() == True

### Ground truth not found
- Place reference transcripts in `tests/fixtures/mandarin-test-reference.txt`
- Or create `tests/fixtures/ground_truth.json` with format:
  ```json
  {
    "mandarin-test.mp3": "参考转录文本..."
  }
  ```

### Memory errors during testing
- Reduce test file count with `--limit` flag
- Close other GPU-heavy applications
- Monitor GPU memory with `nvidia-smi`

---

## Development Notes

**Created:** 2025-11-15 (Story 3.2c)
**Author:** Dev Agent (Claude Code)
**Related Stories:**
- Story 3.1: BELLE-2 integration
- Story 3.2a: Pluggable optimizer architecture
- Story 3.2b: WhisperX dependency validation
- Story 3.2c: BELLE-2 vs WhisperX model comparison

**Files Created:**
- `scripts/ab_test_accuracy.py`
- `scripts/ab_test_segments.py`
- `scripts/ab_test_gibberish.py`
- `scripts/ab_test_performance.py`
- `scripts/ab_test_memory.py`
- `scripts/consolidate_ab_results.py`
- `scripts/run_all_ab_tests.sh` (Linux/macOS)
- `scripts/run_all_ab_tests.bat` (Windows)
- `scripts/README_AB_TESTING.md` (this file)
