# Quality Validation Guide

**Document Version:** 1.0
**Created:** 2025-11-20
**Last Updated:** 2025-11-20

---

## Overview

This guide documents the quality validation processes for KlipNote transcription outputs, including:
- Using the QualityValidator tool for accuracy measurement
- Working with hand-verified test samples
- Interpreting accuracy metrics (CER/WER)
- Running accuracy regression tests
- Maintaining test baselines

---

## Hand-Verified Test Samples

### Purpose

Hand-verified test samples provide objective ground truth for measuring transcription accuracy. These samples enable:
- **Continuous monitoring** of transcription accuracy across releases
- **Objective comparison** between models (BELLE-2 vs WhisperX)
- **Regression prevention** by detecting accuracy degradation
- **Data-driven decisions** for model selection and optimization

### Test Sample Repository

Located at: `test-fixtures/`

```
test-fixtures/
├── zh_long_audio1/
│   ├── audio.mp3                  # Long-form Chinese audio (>30 min)
│   ├── reference_transcript.txt   # Hand-verified ground truth
│   └── metadata.json              # Sample metadata
├── zh_medium_audio1/
│   ├── audio.mp3                  # Medium-length Chinese audio (10-30 min)
│   ├── reference_transcript.txt
│   └── metadata.json
└── zh_short_video1/
    ├── video.mp4                  # Short video sample (<10 min)
    ├── reference_transcript.txt
    └── metadata.json
```

### Sample Characteristics

| Sample | Duration | Content Type | Primary Use Case |
|--------|----------|--------------|------------------|
| zh_long_audio1 | >30 min | Chinese meeting/lecture | Stress testing, long-form accuracy |
| zh_medium_audio1 | 10-30 min | Chinese conversation | Balanced testing, typical use case |
| zh_short_video1 | <10 min | Chinese video content | Quick validation, video format testing |

### Reference Transcript Format

**File:** `reference_transcript.txt`

**Format:** Plain text, UTF-8 encoded

**Content:**
- Contains only the text content (no timestamps)
- Whitespace and punctuation normalized for comparison
- Segmentation differences ignored (focus on text accuracy)
- Human-verified for correctness

**Example:**
```
这是一段关于产品规划的讨论
我们需要在下个季度推出新功能
团队需要评估技术可行性
预计开发时间为三个月
```

### Metadata Format

**File:** `metadata.json`

**Schema:**
```json
{
  "sample_id": "zh_long_audio1",
  "language": "zh",
  "duration_seconds": 1847,
  "content_description": "Business meeting with technical discussion",
  "recording_quality": "medium",
  "speaker_count": 3,
  "accent": "Mandarin (Standard)",
  "created_date": "2025-11-15",
  "verified_by": "Human Reviewer",
  "notes": "Clear audio, minimal background noise"
}
```

---

## Quality Validator Tool

### Tool Location

**Path:** `backend/app/cli/validate_quality.py`

**Prerequisites:**
- Python environment with dependencies installed
- Access to test samples and reference transcripts
- Transcription model available (BELLE-2 or WhisperX)

### Usage

#### Generate Baseline

Create a baseline metric file for a test sample:

```bash
cd backend

python app/cli/validate_quality.py \
  --audio ../test-fixtures/zh_long_audio1/audio.mp3 \
  --reference ../test-fixtures/zh_long_audio1/reference_transcript.txt \
  --output quality_metrics/baselines/zh_long_audio1_belle2.json \
  --model belle2
```

**Output:** Baseline file saved to `quality_metrics/baselines/`

#### Compare Against Baseline

Validate current transcription against stored baseline:

```bash
python app/cli/validate_quality.py \
  --audio ../test-fixtures/zh_long_audio1/audio.mp3 \
  --reference ../test-fixtures/zh_long_audio1/reference_transcript.txt \
  --baseline quality_metrics/baselines/zh_long_audio1_belle2.json \
  --model belle2
```

**Output:**
```
=== Accuracy Validation Results ===
Sample: zh_long_audio1
Model: belle2

Current Metrics:
  CER: 8.7% ✓ (target ≤ 10%)
  WER: 13.2% ✓ (target ≤ 15%)
  Segments: 245
  Avg Segment Length: 4.2s
  Segments Within Constraints: 94.7%

Baseline Comparison:
  CER Delta: +0.3% (baseline: 8.4%)
  WER Delta: +0.5% (baseline: 12.7%)
  Status: PASS (within acceptable variance)
```

### Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--audio` | Yes | Path to audio/video file |
| `--reference` | Yes | Path to reference transcript (txt) |
| `--output` | No | Output path for baseline file |
| `--baseline` | No | Path to baseline file for comparison |
| `--model` | Yes | Model to use: `belle2` or `whisperx` |
| `--verbose` | No | Enable detailed output |

---

## Accuracy Metrics

### Character Error Rate (CER)

**Definition:**
Character-level edit distance between transcription and reference.

**Formula:**
`CER = (S + D + I) / N`

Where:
- S = Substitutions (incorrect characters)
- D = Deletions (missing characters)
- I = Insertions (extra characters)
- N = Total characters in reference

**Target:** ≤ 10% for Chinese audio

**Example:**
- Reference: `这是一个测试` (5 characters)
- Transcription: `这个一个测试` (5 characters, 1 substitution: 是→个)
- CER: 1/5 = 20%

### Word Error Rate (WER)

**Definition:**
Word-level edit distance between transcription and reference.

**Formula:**
`WER = (S + D + I) / N`

Where:
- S = Substitutions (incorrect words)
- D = Deletions (missing words)
- I = Insertions (extra words)
- N = Total words in reference

**Target:** ≤ 15% for Chinese audio

**Example:**
- Reference: `我们需要开发新功能` (6 words)
- Transcription: `我们要开发新功能` (6 words, 1 substitution: 需要→要)
- WER: 1/6 = 16.7%

### Segmentation Tolerance

**Key Principle:** Focus on text accuracy, not segmentation method.

**Acceptable Differences:**
- Segment boundaries at different timestamps
- Different number of segments
- Segments of varying lengths (as long as within 1-7s, ≤200 chars)

**Validation Approach:**
- Normalize text: Combine all segments into single text string
- Remove extra whitespace and normalize punctuation
- Compare normalized text for CER/WER calculation

**Example:**
```
Reference (1 segment):
[0.0-8.0] 我们需要在下个季度推出新功能并评估技术可行性

Transcription (2 segments):
[0.0-4.0] 我们需要在下个季度推出新功能
[4.0-8.0] 并评估技术可行性

Result: PASS (text identical, segmentation acceptable)
```

---

## Running Accuracy Regression Tests

### Local Execution

**Run all accuracy tests:**
```bash
cd backend
pytest tests/test_accuracy_regression.py -v
```

**Run specific test:**
```bash
pytest tests/test_accuracy_regression.py::test_zh_long_audio1_accuracy -v
```

**Run with coverage:**
```bash
pytest tests/test_accuracy_regression.py --cov=app.ai_services --cov-report=term-missing
```

### CI/CD Execution

**Workflow:** `.github/workflows/accuracy-regression.yml`

**Triggers:**
- Push to `main` branch
- Pull requests targeting `main`
- Manual workflow dispatch

**View Results:**
1. Navigate to GitHub Actions tab
2. Select "Accuracy Regression Tests" workflow
3. View test execution logs and results

**Failure Handling:**
- Failed tests block PR merge
- Review test output for failing samples
- Investigate accuracy degradation causes
- Update baselines if intentional changes made

---

## Baseline Management

### When to Update Baselines

**Required Updates:**
1. **Model architecture changes** - New model version or configuration
2. **Enhancement pipeline modifications** - Changes to VAD, refinement, splitting
3. **Intentional accuracy improvements** - Optimization work that improves metrics
4. **Reference transcript corrections** - Errors found in ground truth

**Not Required:**
- Code refactoring with no functional changes
- Documentation updates
- UI/frontend changes

### Update Procedure

**Step 1: Regenerate baselines**
```bash
cd backend

# Regenerate for BELLE-2
for sample in zh_long_audio1 zh_medium_audio1 zh_short_video1; do
  python app/cli/validate_quality.py \
    --audio ../test-fixtures/$sample/audio.* \
    --reference ../test-fixtures/$sample/reference_transcript.txt \
    --output quality_metrics/baselines/${sample}_belle2.json \
    --model belle2
done

# Regenerate for WhisperX
for sample in zh_long_audio1 zh_medium_audio1 zh_short_video1; do
  python app/cli/validate_quality.py \
    --audio ../test-fixtures/$sample/audio.* \
    --reference ../test-fixtures/$sample/reference_transcript.txt \
    --output quality_metrics/baselines/${sample}_whisperx.json \
    --model whisperx
done
```

**Step 2: Run regression tests**
```bash
pytest tests/test_accuracy_regression.py -v
```

**Step 3: Document changes**
```bash
git add quality_metrics/baselines/
git commit -m "chore: Update accuracy baselines

Reason: [Describe reason for baseline update]

Metric Changes:
- zh_long_audio1: CER 8.7% → 7.2%, WER 13.2% → 11.5%
- zh_medium_audio1: CER 9.1% → 7.8%, WER 14.3% → 12.1%
- zh_short_video1: CER 7.5% → 6.9%, WER 12.8% → 11.3%

All tests passing after baseline update."
```

**Step 4: Code review**
- Baseline changes require code review approval
- Reviewer validates reason for baseline update
- Reviewer verifies metric improvements are legitimate

### Baseline Versioning

**Git Tags:**
```bash
# Tag major baseline versions
git tag -a baseline-v1.0 -m "Initial baselines for BELLE-2 and WhisperX"
git push origin baseline-v1.0
```

**Changelog:** `quality_metrics/CHANGELOG.md`
```markdown
# Baseline Changelog

## v2.0 (2025-11-20)
- Updated all baselines after VAD preprocessing integration
- CER improved by average 15% across all samples
- WER improved by average 12% across all samples

## v1.0 (2025-11-15)
- Initial baselines for BELLE-2 and WhisperX models
- 3 test samples: zh_long_audio1, zh_medium_audio1, zh_short_video1
```

---

## Adding New Test Samples

### Selection Criteria

**Diversity Requirements:**
- Audio duration: Mix of short (<10 min), medium (10-30 min), long (>30 min)
- Content type: Meetings, lectures, conversations, presentations
- Recording quality: High, medium, low quality samples
- Speaker characteristics: Different accents, speaking rates, background noise levels

**Quality Requirements:**
- Clear reference transcript available or can be created
- Representative of real-world use cases
- Contains challenging scenarios (technical terms, numbers, names)

### Creation Process

**Step 1: Prepare audio file**
- Supported formats: MP3, MP4, WAV, M4A
- File size: Reasonable for CI/CD execution (<100MB preferred)
- Naming: `{language}_{duration_category}_audio{n}.{ext}`
  - Example: `zh_short_audio2.mp3`, `en_medium_audio1.mp4`

**Step 2: Create reference transcript**
- Manually transcribe audio with high accuracy
- Save as UTF-8 encoded text file: `reference_transcript.txt`
- Focus on text accuracy (ignore timing and segmentation)
- Review and verify transcript for correctness

**Step 3: Create metadata file**
```json
{
  "sample_id": "zh_short_audio2",
  "language": "zh",
  "duration_seconds": 420,
  "content_description": "Product planning discussion",
  "recording_quality": "high",
  "speaker_count": 2,
  "accent": "Mandarin (Standard)",
  "created_date": "2025-11-20",
  "verified_by": "Human Reviewer",
  "notes": "Technical vocabulary present"
}
```

**Step 4: Directory structure**
```bash
mkdir test-fixtures/zh_short_audio2
cp audio.mp3 test-fixtures/zh_short_audio2/
cp reference_transcript.txt test-fixtures/zh_short_audio2/
cp metadata.json test-fixtures/zh_short_audio2/
```

**Step 5: Generate baselines**
```bash
python backend/app/cli/validate_quality.py \
  --audio test-fixtures/zh_short_audio2/audio.mp3 \
  --reference test-fixtures/zh_short_audio2/reference_transcript.txt \
  --output backend/quality_metrics/baselines/zh_short_audio2_belle2.json \
  --model belle2
```

**Step 6: Add test case**
```python
# backend/tests/test_accuracy_regression.py

@pytest.mark.accuracy
def test_zh_short_audio2_accuracy():
    """Validate accuracy for zh_short_audio2 sample."""
    validator = QualityValidator()
    result = validator.validate(
        audio_path="test-fixtures/zh_short_audio2/audio.mp3",
        reference_path="test-fixtures/zh_short_audio2/reference_transcript.txt",
        model="belle2"
    )

    assert result.cer <= 0.10, f"CER {result.cer:.2%} exceeds 10% threshold"
    assert result.wer <= 0.15, f"WER {result.wer:.2%} exceeds 15% threshold"
```

**Step 7: Update documentation**
- Update `test-fixtures/README.md` with new sample description
- Update this guide with sample characteristics
- Commit all files with descriptive commit message

---

## Troubleshooting

### High CER/WER Results

**Possible Causes:**
1. **Model degradation** - Recent code changes affected accuracy
2. **Reference transcript errors** - Ground truth contains mistakes
3. **Segmentation normalization issues** - Text not properly normalized
4. **Model configuration changes** - Decoder parameters modified

**Investigation Steps:**
1. Review recent commits for relevant changes
2. Manually verify reference transcript accuracy
3. Check normalization logic in QualityValidator
4. Compare current results with historical baselines
5. Test with other samples to identify patterns

### Baseline Comparison Failures

**Error:** "CER delta exceeds acceptable variance"

**Resolution:**
1. Check if recent changes intentionally modified accuracy
2. If intentional improvement: Update baselines
3. If unintentional degradation: Investigate and fix root cause
4. Re-run tests after resolution

### CI/CD Test Failures

**Error:** "Accuracy regression test failed in GitHub Actions"

**Resolution:**
1. Review GitHub Actions logs for specific failure
2. Check if model files are properly cached
3. Verify test-fixtures directory is committed
4. Ensure baselines are up-to-date in repository
5. Re-run workflow after fixes

---

## Best Practices

### Maintaining Test Quality

1. **Regular review** - Periodically review reference transcripts for accuracy
2. **Diverse coverage** - Ensure samples cover various use cases
3. **Version control** - Always commit baselines with git history
4. **Documentation** - Document all baseline changes with clear reasons
5. **Peer review** - Require code review for baseline updates

### Efficiency Tips

1. **Batch baseline generation** - Use shell loops for multiple samples
2. **Cache model files** - Avoid re-downloading models in CI/CD
3. **Parallel testing** - Use pytest-xdist for faster test execution
4. **Selective testing** - Run only affected tests during development

### Quality Standards

1. **CER/WER targets** - Maintain ≤ 10% CER, ≤ 15% WER for Chinese audio
2. **Baseline variance** - Allow <2% variance in metric comparisons
3. **Sample diversity** - At least 3 samples per language/duration category
4. **Review frequency** - Validate baselines quarterly or after major changes

---

## References

**Related Documentation:**
- [Architecture: Accuracy Regression Testing](./architecture.md#accuracy-regression-testing)
- [PRD: NFR-005 Transcription Quality](./PRD.md#non-functional-requirements)
- [Story 4.6b: Hand-Verified Test Sample Integration](./sprint-artifacts/stories/4-6b-hand-verified-samples.md)
- [Test Fixtures README](../test-fixtures/README.md)

**External Resources:**
- [Character Error Rate (CER) Definition](https://en.wikipedia.org/wiki/Word_error_rate)
- [jiwer Library Documentation](https://jitsi.github.io/jiwer/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Document History:**

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-20 | 1.0 | Link | Initial creation with hand-verified samples section |

---

**End of Document**
