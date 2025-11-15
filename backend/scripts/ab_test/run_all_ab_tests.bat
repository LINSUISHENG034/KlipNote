@echo off
REM Story 3.2c: Run All A/B Tests for BELLE-2 vs WhisperX (Windows)
REM
REM This script runs all 5 A/B tests for both models and consolidates results.
REM
REM Usage:
REM   backend\scripts\run_all_ab_tests.bat [--limit N]
REM

setlocal enabledelayedexpansion

REM Parse arguments
set LIMIT_ARG=
:parse_args
if "%~1"=="--limit" (
    set LIMIT_ARG=--limit %~2
    shift
    shift
    goto parse_args
)

REM Configuration
set PROJECT_ROOT=%~dp0..\..\
set BACKEND_DIR=%PROJECT_ROOT%backend
set RESULTS_DIR=%BACKEND_DIR%\ab_test_results
set TEST_DIR=%PROJECT_ROOT%tests\fixtures

REM Create results directory
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

echo ======================================================================
echo Story 3.2c: BELLE-2 vs WhisperX A/B Testing
echo ======================================================================
echo Project root: %PROJECT_ROOT%
echo Test directory: %TEST_DIR%
echo Results directory: %RESULTS_DIR%
if not "%LIMIT_ARG%"=="" echo Test file limit: %LIMIT_ARG%
echo ======================================================================
echo.

REM ============================================================================
REM Phase 1: BELLE-2 Tests (using main .venv)
REM ============================================================================

echo ======================================================================
echo PHASE 1: Running BELLE-2 Tests (main .venv)
echo ======================================================================
echo.

cd /d "%BACKEND_DIR%"

REM Activate main .venv
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: Main .venv not found!
    exit /b 1
)

echo OK Activated main .venv (BELLE-2 environment)
echo.

REM Run BELLE-2 tests
echo Running BELLE-2 tests...
echo.

echo [1/5] Accuracy test (CER/WER)...
python scripts\ab_test_accuracy.py --test-dir "%TEST_DIR%" --model belle2 --output "%RESULTS_DIR%\belle2_accuracy.json" %LIMIT_ARG%

echo.
echo [2/5] Segment compliance test...
python scripts\ab_test_segments.py --test-dir "%TEST_DIR%" --model belle2 --output "%RESULTS_DIR%\belle2_segments.json" %LIMIT_ARG%

echo.
echo [3/5] Gibberish/repetition test...
python scripts\ab_test_gibberish.py --test-dir "%TEST_DIR%" --model belle2 --output "%RESULTS_DIR%\belle2_gibberish.json" %LIMIT_ARG%

echo.
echo [4/5] Performance test (RTF)...
python scripts\ab_test_performance.py --test-dir "%TEST_DIR%" --model belle2 --output "%RESULTS_DIR%\belle2_performance.json" %LIMIT_ARG%

echo.
echo [5/5] Memory usage test (VRAM)...
python scripts\ab_test_memory.py --test-dir "%TEST_DIR%" --model belle2 --output "%RESULTS_DIR%\belle2_memory.json" %LIMIT_ARG%

echo.
echo OK BELLE-2 tests complete!
echo.

REM Deactivate main .venv
call deactivate

REM ============================================================================
REM Phase 2: WhisperX Tests (using .venv-whisperx)
REM ============================================================================

echo ======================================================================
echo PHASE 2: Running WhisperX Tests (.venv-whisperx)
echo ======================================================================
echo.

REM Activate .venv-whisperx
if exist ".venv-whisperx\Scripts\activate.bat" (
    call .venv-whisperx\Scripts\activate.bat
) else (
    echo ERROR: .venv-whisperx not found!
    echo Please create it first: python -m venv .venv-whisperx
    exit /b 1
)

echo OK Activated .venv-whisperx (WhisperX environment)
echo.

REM Run WhisperX tests
echo Running WhisperX tests...
echo.

echo [1/5] Accuracy test (CER/WER)...
python scripts\ab_test_accuracy.py --test-dir "%TEST_DIR%" --model whisperx --output "%RESULTS_DIR%\whisperx_accuracy.json" %LIMIT_ARG%

echo.
echo [2/5] Segment compliance test...
python scripts\ab_test_segments.py --test-dir "%TEST_DIR%" --model whisperx --output "%RESULTS_DIR%\whisperx_segments.json" %LIMIT_ARG%

echo.
echo [3/5] Gibberish/repetition test...
python scripts\ab_test_gibberish.py --test-dir "%TEST_DIR%" --model whisperx --output "%RESULTS_DIR%\whisperx_gibberish.json" %LIMIT_ARG%

echo.
echo [4/5] Performance test (RTF)...
python scripts\ab_test_performance.py --test-dir "%TEST_DIR%" --model whisperx --output "%RESULTS_DIR%\whisperx_performance.json" %LIMIT_ARG%

echo.
echo [5/5] Memory usage test (VRAM)...
python scripts\ab_test_memory.py --test-dir "%TEST_DIR%" --model whisperx --output "%RESULTS_DIR%\whisperx_memory.json" %LIMIT_ARG%

echo.
echo OK WhisperX tests complete!
echo.

REM Deactivate .venv-whisperx
call deactivate

REM ============================================================================
REM Phase 3: Consolidate Results
REM ============================================================================

echo ======================================================================
echo PHASE 3: Consolidating Results
echo ======================================================================
echo.

REM Activate main .venv for consolidation
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat

python scripts\consolidate_ab_results.py --belle2-accuracy "%RESULTS_DIR%\belle2_accuracy.json" --belle2-segments "%RESULTS_DIR%\belle2_segments.json" --belle2-gibberish "%RESULTS_DIR%\belle2_gibberish.json" --belle2-performance "%RESULTS_DIR%\belle2_performance.json" --belle2-memory "%RESULTS_DIR%\belle2_memory.json" --whisperx-accuracy "%RESULTS_DIR%\whisperx_accuracy.json" --whisperx-segments "%RESULTS_DIR%\whisperx_segments.json" --whisperx-gibberish "%RESULTS_DIR%\whisperx_gibberish.json" --whisperx-performance "%RESULTS_DIR%\whisperx_performance.json" --whisperx-memory "%RESULTS_DIR%\whisperx_memory.json" --output "%RESULTS_DIR%\consolidated_comparison.json"

call deactivate

echo.
echo ======================================================================
echo OK ALL A/B TESTS COMPLETE!
echo ======================================================================
echo.
echo Results saved to: %RESULTS_DIR%\
echo.
echo View consolidated comparison:
echo   type "%RESULTS_DIR%\consolidated_comparison.json"
echo.
echo Next steps:
echo   1. Review consolidated_comparison.json for winner recommendation
echo   2. Create phase gate decision report (Story AC #5)
echo   3. Define Epic 3 path forward based on winning model (Story AC #6)
echo.
echo ======================================================================

endlocal
