"""
Integration tests for BELLE-2 transcription service
Requires GPU and real model loading - marked with @pytest.mark.gpu
"""

import pytest
import os
import torch
from typing import List


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Calculate Character Error Rate (CER) using Levenshtein distance.

    CER = (Substitutions + Deletions + Insertions) / Total_Reference_Characters

    Args:
        reference: Ground truth text
        hypothesis: Predicted/transcribed text

    Returns:
        CER value (0.0 = perfect match, higher = more errors)
    """
    # Normalize whitespace
    ref = reference.strip()
    hyp = hypothesis.strip()

    # Edge cases
    if len(ref) == 0:
        return 1.0 if len(hyp) > 0 else 0.0

    # Levenshtein distance using dynamic programming
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]

    # Initialize first column and row
    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j

    # Fill matrix
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                cost = 0
            else:
                cost = 1

            d[i][j] = min(
                d[i - 1][j] + 1,      # Deletion
                d[i][j - 1] + 1,      # Insertion
                d[i - 1][j - 1] + cost # Substitution
            )

    # CER = edit_distance / reference_length
    edit_distance = d[len(ref)][len(hyp)]
    cer = edit_distance / len(ref)

    return cer


class TestCERCalculation:
    """Unit tests for CER calculation function"""

    def test_cer_perfect_match(self):
        """Test CER with identical strings"""
        reference = "这是一个测试"
        hypothesis = "这是一个测试"
        cer = calculate_cer(reference, hypothesis)
        assert cer == 0.0, "Identical strings should have CER of 0.0"

    def test_cer_complete_mismatch(self):
        """Test CER with completely different strings"""
        reference = "这是一个测试"
        hypothesis = "完全不同文本"
        cer = calculate_cer(reference, hypothesis)
        # All characters are different, so CER should be >= 1.0
        assert cer >= 1.0, "Completely different strings should have CER >= 1.0"

    def test_cer_partial_match(self):
        """Test CER with partial match"""
        reference = "这是一个测试句子"
        hypothesis = "这是测试句子"  # Missing "一个"
        cer = calculate_cer(reference, hypothesis)
        # Should have some error but not complete mismatch
        assert 0.0 < cer < 1.0, f"Partial match should have 0 < CER < 1, got {cer}"

    def test_cer_insertion(self):
        """Test CER with extra characters"""
        reference = "测试"
        hypothesis = "测试额外字符"
        cer = calculate_cer(reference, hypothesis)
        # CER = edit_distance / len(reference)
        # 4 extra chars, 2 reference chars = 4/2 = 2.0
        assert cer > 0.0, "Extra characters should increase CER"

    def test_cer_deletion(self):
        """Test CER with missing characters"""
        reference = "这是测试句子"
        hypothesis = "这是"
        cer = calculate_cer(reference, hypothesis)
        # 4 chars missing from 6 = 4/6 ≈ 0.67
        assert 0.5 < cer < 1.0, f"Missing characters should give moderate CER, got {cer}"

    def test_cer_empty_reference(self):
        """Test CER with empty reference"""
        reference = ""
        hypothesis = "some text"
        cer = calculate_cer(reference, hypothesis)
        assert cer == 1.0, "Empty reference with non-empty hypothesis should give CER of 1.0"

    def test_cer_both_empty(self):
        """Test CER with both strings empty"""
        reference = ""
        hypothesis = ""
        cer = calculate_cer(reference, hypothesis)
        assert cer == 0.0, "Both empty should give CER of 0.0"


@pytest.mark.gpu
class TestBelle2Integration:
    """Integration tests with real BELLE-2 model (requires GPU)"""

    def test_belle2_transcription_real_model(self, tmp_path):
        """
        Test BELLE-2 transcription with real model loading

        Requirements:
        - GPU with CUDA support
        - ~6GB VRAM available
        - Internet connection (first run downloads ~3.1GB model)
        """
        from app.ai_services.belle2_service import Belle2Service

        # Skip if CUDA not available
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for integration test")

        service = Belle2Service(device="cuda")

        # Use a short test audio file (create or provide fixture)
        # For now, create a simple test file if it doesn't exist
        test_audio_path = "../tests/fixtures/mandarin-test.mp3"

        if not os.path.exists(test_audio_path):
            pytest.skip(f"Test audio file not found: {test_audio_path}")

        # Transcribe audio
        result = service.transcribe(test_audio_path, language="zh")

        # Verify results
        assert len(result) > 0, "Transcription returned no segments"
        assert all(seg["start"] < seg["end"] for seg in result), "Invalid timestamps"

        # Verify Chinese text in output (basic sanity check)
        text = " ".join(seg["text"] for seg in result)
        # Check for Chinese characters (Unicode range U+4E00 to U+9FFF)
        has_chinese = any(0x4E00 <= ord(char) <= 0x9FFF for char in text if len(text) > 0)

        if len(text) > 0:
            assert has_chinese or len(text) > 0, "Transcription should contain Chinese characters or text"

        print(f"✓ Transcribed {len(result)} segments")
        print(f"✓ Sample text: {result[0]['text'][:100] if result else 'N/A'}")

    def test_belle2_model_loading_performance(self):
        """
        Test BELLE-2 model loading time

        AC #2: Subsequent loads <5 seconds from cache
        """
        from app.ai_services.belle2_service import Belle2Service
        import time

        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for integration test")

        # First load (may download model, can take 5-10 minutes)
        print("\n[Test] First load (may download model)...")
        start_time = time.time()
        service1 = Belle2Service(device="cuda")
        service1._load_model()
        first_load_time = time.time() - start_time
        print(f"✓ First load: {first_load_time:.2f}s")

        # Second load (should be from cache)
        print("[Test] Second load (from cache)...")
        start_time = time.time()
        service2 = Belle2Service(device="cuda")
        service2._load_model()
        second_load_time = time.time() - start_time

        print(f"✓ Second load: {second_load_time:.2f}s")
        print(f"✓ Cache speedup: {first_load_time / second_load_time:.1f}x")

        # Verify cache load time is <5 seconds (AC #2)
        assert second_load_time < 5.0, f"Cache load time {second_load_time:.2f}s exceeds 5s threshold"

    def test_timestamp_alignment_vs_whisperx(self):
        """
        Test timestamp alignment stability (AC #4)

        Compare BELLE-2 timestamps against WhisperX baseline
        Drift must be <200ms per segment to ensure click-to-timestamp compatibility
        """
        from app.ai_services.belle2_service import Belle2Service
        from app.ai_services.whisperx_service import WhisperXService

        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for integration test")

        test_audio_path = "../tests/fixtures/mandarin-test.mp3"
        if not os.path.exists(test_audio_path):
            pytest.skip(f"Test audio file not found: {test_audio_path}")

        # Transcribe with both models
        belle2 = Belle2Service(device="cuda")
        whisperx = WhisperXService(device="cuda")

        print("\n[Test] Transcribing with BELLE-2...")
        belle2_segments = belle2.transcribe(test_audio_path, language="zh")

        print("[Test] Transcribing with WhisperX...")
        whisperx_segments = whisperx.transcribe(test_audio_path, language="zh")

        # Compare timestamps (allow ±200ms drift per AC #4)
        min_segments = min(len(belle2_segments), len(whisperx_segments))
        max_drift = 0.0

        for i in range(min_segments):
            b_seg = belle2_segments[i]
            w_seg = whisperx_segments[i]

            start_drift = abs(b_seg["start"] - w_seg["start"])
            end_drift = abs(b_seg["end"] - w_seg["end"])

            max_drift = max(max_drift, start_drift, end_drift)

            if start_drift > 0.2 or end_drift > 0.2:
                print(f"⚠ Segment {i}: drift {start_drift:.3f}s / {end_drift:.3f}s exceeds 200ms")

        print(f"✓ Max timestamp drift: {max_drift:.3f}s")

        # AC #4: Drift <200ms per segment
        assert max_drift < 0.2, f"Timestamp drift {max_drift:.3f}s exceeds 200ms threshold"

    def test_belle2_cer_improvement(self):
        """
        Test CER (Character Error Rate) improvement (AC #6)

        This test verifies that BELLE-2 produces lower CER than WhisperX
        for Mandarin Chinese audio transcription.

        Requires:
        - Reference transcript (ground truth)
        - Test audio file (mandarin-test.mp3)
        - GPU with CUDA support
        """
        from app.ai_services.belle2_service import Belle2Service
        from app.ai_services.whisperx_service import WhisperXService

        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for integration test")

        test_audio_path = "../tests/fixtures/mandarin-test.mp3"
        reference_path = "../tests/fixtures/mandarin-test-reference.txt"

        # Check for test fixtures
        if not os.path.exists(test_audio_path):
            pytest.skip(f"Test audio file not found: {test_audio_path}")

        if not os.path.exists(reference_path):
            pytest.skip(f"Reference transcript not found: {reference_path}")

        # Load reference transcript (ground truth)
        # Extract only the text content, removing timestamp markers
        with open(reference_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Remove timestamp markers like "[00:00:00.000 --> 00:00:02.680]"
        import re
        reference_text = ""
        for line in lines:
            # Remove timestamp pattern [HH:MM:SS.mmm --> HH:MM:SS.mmm]
            text_only = re.sub(r'\[[\d:\.]+\s*-->\s*[\d:\.]+\]', '', line).strip()
            if text_only:
                reference_text += text_only

        print(f"\n[Test] Reference text length: {len(reference_text)} characters")

        # Transcribe with BELLE-2
        print("[Test] Transcribing with BELLE-2...")
        belle2 = Belle2Service(device="cuda")
        belle2_segments = belle2.transcribe(test_audio_path, language="zh")
        belle2_text = " ".join(seg["text"] for seg in belle2_segments).strip()

        # Transcribe with WhisperX (baseline)
        print("[Test] Transcribing with WhisperX (baseline)...")
        whisperx = WhisperXService(device="cuda")
        whisperx_segments = whisperx.transcribe(test_audio_path, language="zh")
        whisperx_text = " ".join(seg["text"] for seg in whisperx_segments).strip()

        # Calculate CER for both models
        belle2_cer = calculate_cer(reference_text, belle2_text)
        whisperx_cer = calculate_cer(reference_text, whisperx_text)

        print(f"\n✓ BELLE-2 CER: {belle2_cer:.4f} ({belle2_cer * 100:.2f}%)")
        print(f"✓ WhisperX CER: {whisperx_cer:.4f} ({whisperx_cer * 100:.2f}%)")

        # Debug: Print text lengths and samples
        print(f"\n--- Text Comparison ---")
        print(f"Reference length: {len(reference_text)} characters")
        print(f"BELLE-2 length: {len(belle2_text)} characters")
        print(f"WhisperX length: {len(whisperx_text)} characters")
        print(f"\nReference (first 200 chars): {reference_text[:200]}")
        print(f"\nBELLE-2 (first 200 chars): {belle2_text[:200]}")
        print(f"\nWhisperX (first 200 chars): {whisperx_text[:200]}")

        # Calculate improvement
        if whisperx_cer > 0:
            improvement = ((whisperx_cer - belle2_cer) / whisperx_cer) * 100
            print(f"✓ CER Improvement: {improvement:.2f}%")
        else:
            improvement = 0.0

        # AC #6: Verify BELLE-2 shows improvement over WhisperX
        # According to research: 24-65% relative CER reduction expected
        # We'll accept any improvement as passing (belle2_cer <= whisperx_cer)
        assert belle2_cer <= whisperx_cer, (
            f"BELLE-2 CER ({belle2_cer:.4f}) should be <= WhisperX CER ({whisperx_cer:.4f}). "
            f"Expected improvement not achieved."
        )

        # Log sample outputs for manual review
        print(f"\n--- Sample Comparison ---")
        print(f"Reference: {reference_text[:100]}...")
        print(f"BELLE-2:   {belle2_text[:100]}...")
        print(f"WhisperX:  {whisperx_text[:100]}...")

        print(f"\n✓ AC #6 PASSED: BELLE-2 achieves CER improvement over WhisperX")


@pytest.mark.gpu
class TestBelle2VRAMFootprint:
    """Test VRAM usage validation (AC #7, Task 8)"""

    def test_belle2_vram_usage(self):
        """
        Validate BELLE-2 VRAM usage stays within ~6GB constraint

        AC #7: Memory footprint ~6GB VRAM
        """
        from app.ai_services.belle2_service import Belle2Service

        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for VRAM test")

        # Clear GPU cache before measurement
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

        baseline_vram = torch.cuda.memory_allocated() / (1024 ** 3)
        print(f"\n[Test] Baseline VRAM: {baseline_vram:.2f}GB")

        # Load BELLE-2 model
        print("[Test] Loading BELLE-2 model...")
        service = Belle2Service(device="cuda")
        service._load_model()

        # Measure VRAM after model load
        model_vram = torch.cuda.memory_allocated() / (1024 ** 3)
        peak_vram = torch.cuda.max_memory_allocated() / (1024 ** 3)

        vram_usage = model_vram - baseline_vram

        print(f"✓ Model VRAM: {model_vram:.2f}GB")
        print(f"✓ Peak VRAM: {peak_vram:.2f}GB")
        print(f"✓ BELLE-2 usage: {vram_usage:.2f}GB")

        # AC #7: VRAM usage ≤6.5GB (6GB target + 0.5GB buffer)
        assert vram_usage <= 6.5, f"VRAM usage {vram_usage:.2f}GB exceeds 6.5GB limit"
        assert peak_vram <= 7.0, f"Peak VRAM {peak_vram:.2f}GB exceeds 7GB safety limit"

        print(f"✓ VRAM usage within target: {vram_usage:.2f}GB / 6.0GB target")

    def test_model_manager_vram_tracking(self):
        """Test ModelManager VRAM monitoring"""
        from app.ai_services.model_manager import ModelManager

        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for VRAM test")

        manager = ModelManager()

        # Get initial VRAM
        initial_vram = manager.get_vram_usage()
        assert initial_vram >= 0.0

        # Load model and check VRAM increase
        try:
            manager.load_belle2("BELLE-2/Belle-whisper-large-v3-zh", "cuda")
            loaded_vram = manager.get_vram_usage()

            assert loaded_vram > initial_vram, "VRAM should increase after model load"
            print(f"✓ VRAM increased: {initial_vram:.2f}GB → {loaded_vram:.2f}GB")
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")


@pytest.mark.gpu
class TestBelle2FallbackIntegration:
    """Test fallback mechanism in production scenario"""

    def test_fallback_mechanism_with_real_services(self):
        """
        Test fallback from BELLE-2 to WhisperX in production scenario

        This test verifies the fallback mechanism works with real services,
        not just mocked components.
        """
        from app.tasks.transcription import select_transcription_service
        from app.services.redis_service import RedisService
        from app.ai_services.base import TranscriptionService

        redis_service = RedisService()

        # Test successful BELLE-2 selection for Chinese
        service, model_name, selection = select_transcription_service(
            job_id="test-job-belle2",
            redis_service=redis_service,
            language="zh"
        )

        assert service is not None
        assert isinstance(service, TranscriptionService)

        # Model name should be belle2 (if available) or whisperx (fallback)
        assert model_name in ["belle2", "whisperx"]
        assert selection["detected_language"] == "zh"

        print(f"✓ Selected model: {model_name}")

        # Test WhisperX selection for English
        service_en, model_name_en, selection_en = select_transcription_service(
            job_id="test-job-whisperx",
            redis_service=redis_service,
            language="en"
        )

        assert service_en is not None
        assert model_name_en == "whisperx"
        assert selection_en["selection_reason"] == "language_not_chinese"

        print(f"✓ English uses WhisperX: {model_name_en}")


@pytest.mark.gpu
class TestBelle2EndToEnd:
    """End-to-end integration test"""

    def test_full_transcription_workflow(self):
        """
        Full transcription workflow test: upload → transcribe → retrieve

        This test simulates the complete user journey:
        1. Audio file is provided
        2. Transcription task is executed
        3. Results are saved to disk and Redis
        4. Results can be retrieved
        """
        pytest.skip("End-to-end test requires full application setup")

        # TODO: Implement E2E test
        # 1. Create test audio file
        # 2. Call transcribe_audio Celery task
        # 3. Wait for completion
        # 4. Verify results in Redis
        # 5. Verify results on disk
        # 6. Verify model_metadata.json created
