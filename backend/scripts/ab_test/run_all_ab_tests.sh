#!/usr/bin/env bash
#
# Story 3.2c: Run All A/B Tests for BELLE-2 vs WhisperX
#
# This script runs all 5 A/B tests for both models and consolidates results.
#
# Usage:
#   bash backend/scripts/run_all_ab_tests.sh [--limit N]
#
# Options:
#   --limit N    Limit number of test files per test (for quick runs)
#

set -e  # Exit on error

# Parse arguments
LIMIT_ARG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT_ARG="--limit $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
RESULTS_DIR="$BACKEND_DIR/ab_test_results"
TEST_DIR="$PROJECT_ROOT/tests/fixtures"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "======================================================================"
echo "Story 3.2c: BELLE-2 vs WhisperX A/B Testing"
echo "======================================================================"
echo "Project root: $PROJECT_ROOT"
echo "Test directory: $TEST_DIR"
echo "Results directory: $RESULTS_DIR"
if [ -n "$LIMIT_ARG" ]; then
    echo "Test file limit: $LIMIT_ARG"
fi
echo "======================================================================"
echo

# ============================================================================
# Phase 1: BELLE-2 Tests (using main .venv)
# ============================================================================

echo "======================================================================"
echo "PHASE 1: Running BELLE-2 Tests (main .venv)"
echo "======================================================================"
echo

cd "$BACKEND_DIR"

# Activate main .venv
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "ERROR: Main .venv not found!"
    exit 1
fi

echo "✓ Activated main .venv (BELLE-2 environment)"
echo

# Run BELLE-2 tests
echo "Running BELLE-2 tests..."
echo

echo "[1/5] Accuracy test (CER/WER)..."
python scripts/ab_test_accuracy.py \
    --test-dir "$TEST_DIR" \
    --model belle2 \
    --output "$RESULTS_DIR/belle2_accuracy.json" \
    $LIMIT_ARG

echo
echo "[2/5] Segment compliance test..."
python scripts/ab_test_segments.py \
    --test-dir "$TEST_DIR" \
    --model belle2 \
    --output "$RESULTS_DIR/belle2_segments.json" \
    $LIMIT_ARG

echo
echo "[3/5] Gibberish/repetition test..."
python scripts/ab_test_gibberish.py \
    --test-dir "$TEST_DIR" \
    --model belle2 \
    --output "$RESULTS_DIR/belle2_gibberish.json" \
    $LIMIT_ARG

echo
echo "[4/5] Performance test (RTF)..."
python scripts/ab_test_performance.py \
    --test-dir "$TEST_DIR" \
    --model belle2 \
    --output "$RESULTS_DIR/belle2_performance.json" \
    $LIMIT_ARG

echo
echo "[5/5] Memory usage test (VRAM)..."
python scripts/ab_test_memory.py \
    --test-dir "$TEST_DIR" \
    --model belle2 \
    --output "$RESULTS_DIR/belle2_memory.json" \
    $LIMIT_ARG

echo
echo "✓ BELLE-2 tests complete!"
echo

# Deactivate main .venv
deactivate

# ============================================================================
# Phase 2: WhisperX Tests (using .venv-whisperx)
# ============================================================================

echo "======================================================================"
echo "PHASE 2: Running WhisperX Tests (.venv-whisperx)"
echo "======================================================================"
echo

# Activate .venv-whisperx
if [ -f ".venv-whisperx/Scripts/activate" ]; then
    source .venv-whisperx/Scripts/activate
elif [ -f ".venv-whisperx/bin/activate" ]; then
    source .venv-whisperx/bin/activate
else
    echo "ERROR: .venv-whisperx not found!"
    echo "Please run: python -m venv .venv-whisperx && .venv-whisperx/Scripts/activate && pip install whisperx torch torchaudio"
    exit 1
fi

echo "✓ Activated .venv-whisperx (WhisperX environment)"
echo

# Run WhisperX tests
echo "Running WhisperX tests..."
echo

echo "[1/5] Accuracy test (CER/WER)..."
python scripts/ab_test_accuracy.py \
    --test-dir "$TEST_DIR" \
    --model whisperx \
    --output "$RESULTS_DIR/whisperx_accuracy.json" \
    $LIMIT_ARG

echo
echo "[2/5] Segment compliance test..."
python scripts/ab_test_segments.py \
    --test-dir "$TEST_DIR" \
    --model whisperx \
    --output "$RESULTS_DIR/whisperx_segments.json" \
    $LIMIT_ARG

echo
echo "[3/5] Gibberish/repetition test..."
python scripts/ab_test_gibberish.py \
    --test-dir "$TEST_DIR" \
    --model whisperx \
    --output "$RESULTS_DIR/whisperx_gibberish.json" \
    $LIMIT_ARG

echo
echo "[4/5] Performance test (RTF)..."
python scripts/ab_test_performance.py \
    --test-dir "$TEST_DIR" \
    --model whisperx \
    --output "$RESULTS_DIR/whisperx_performance.json" \
    $LIMIT_ARG

echo
echo "[5/5] Memory usage test (VRAM)..."
python scripts/ab_test_memory.py \
    --test-dir "$TEST_DIR" \
    --model whisperx \
    --output "$RESULTS_DIR/whisperx_memory.json" \
    $LIMIT_ARG

echo
echo "✓ WhisperX tests complete!"
echo

# Deactivate .venv-whisperx
deactivate

# ============================================================================
# Phase 3: Consolidate Results
# ============================================================================

echo "======================================================================"
echo "PHASE 3: Consolidating Results"
echo "======================================================================"
echo

# Activate main .venv for consolidation
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

python scripts/consolidate_ab_results.py \
    --belle2-accuracy "$RESULTS_DIR/belle2_accuracy.json" \
    --belle2-segments "$RESULTS_DIR/belle2_segments.json" \
    --belle2-gibberish "$RESULTS_DIR/belle2_gibberish.json" \
    --belle2-performance "$RESULTS_DIR/belle2_performance.json" \
    --belle2-memory "$RESULTS_DIR/belle2_memory.json" \
    --whisperx-accuracy "$RESULTS_DIR/whisperx_accuracy.json" \
    --whisperx-segments "$RESULTS_DIR/whisperx_segments.json" \
    --whisperx-gibberish "$RESULTS_DIR/whisperx_gibberish.json" \
    --whisperx-performance "$RESULTS_DIR/whisperx_performance.json" \
    --whisperx-memory "$RESULTS_DIR/whisperx_memory.json" \
    --output "$RESULTS_DIR/consolidated_comparison.json"

deactivate

echo
echo "======================================================================"
echo "✅ ALL A/B TESTS COMPLETE!"
echo "======================================================================"
echo
echo "Results saved to: $RESULTS_DIR/"
echo
echo "View consolidated comparison:"
echo "  cat $RESULTS_DIR/consolidated_comparison.json | python -m json.tool"
echo
echo "Next steps:"
echo "  1. Review consolidated_comparison.json for winner recommendation"
echo "  2. Create phase gate decision report (Story AC #5)"
echo "  3. Define Epic 3 path forward based on winning model (Story AC #6)"
echo
echo "======================================================================"
