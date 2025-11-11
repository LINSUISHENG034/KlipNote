# Technical Research Report: {{technical_question}}

**Date:** {{date}}
**Prepared by:** {{user_name}}
**Project Context:** {{project_context}}

---

## Executive Summary

{{recommendations}}

### Key Recommendation

**Primary Choice:** [Technology/Pattern Name]

**Rationale:** [2-3 sentence summary]

**Key Benefits:**

- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

---

## 1. Research Objectives

### Technical Question

{{technical_question}}

### Project Context

{{project_context}}

### Requirements and Constraints

#### Functional Requirements

{{functional_requirements}}

#### Non-Functional Requirements

{{non_functional_requirements}}

#### Technical Constraints

{{technical_constraints}}

---

## 2. Technology Options Evaluated

- **FireRedASR (LLM & AED, Feb 2025):** 8.3 B LLM variant and 1.1 B AED variant set new Mandarin SOTA (0.55–0.76 CER on AISHELL-1, ≤4.9 CER on WenetSpeech meeting) but demand high VRAM and short-window batching; best raw accuracy headroom while staying open-source (FireRedTeam/FireRedASR GitHub, 2025-02-17).
- **BELLE-2 whisper-large-v3-zh:** Full fine-tune of Whisper large-v3 delivering 24–65 % relative CER gains vs base Whisper across AISHELL1/2, WenetSpeech, HKUST while keeping Whisper decoder interface for easy drop-in replacement (Hugging Face BELLE-2/Belle-whisper-large-v3-zh, 2025).
- **SenseVoice Small/Large (FunAudioLLM, Nov 2024):** Multilingual foundation ASR trained on 400k h, with Small NAR model reaching ~70 ms per 10 s clip (≈15× faster than Whisper-L) and November 2024 updates adding CTC timestamps plus ONNX/libtorch exports for offline deployment.
- **FunASR Paraformer-zh (v2.0.4, 2024):** 220 M Mandarin NAR model with built-in VAD, punctuation, and streaming configs (600 ms chunks) so you can sustain ≤2× realtime throughput on local GPUs while keeping everything on-prem.
- **Whisper Desktop Reference (Const-me build):** Serves as the benchmark to match/exceed; demonstrates achievable quality using optimized Whisper decoding on consumer hardware.

### Option Exploration via Tree of Thoughts

**Path A – Ultra-High Accuracy:**
- Focus: FireRedASR-LLM/AED.
- Strength: Sub-1 % AISHELL-1 CER, <5 % WenetSpeech meeting CER—clear leader for Mandarin accuracy.
- Trade-offs: 1.1–8.3 B params require large VRAM; AED limited to ~60 s clips, LLM ≤30 s; needs length-aware batching and careful decoding penalties to avoid repetitions.
- **Expert panel view:** Scientist wants FireRed for accuracy ceiling but urges AED-first pilots plus chunk QA; infra lead warns of ≥40 GB VRAM and chunk sorting; product owner insists we land BELLE/SenseVoice wins before exposing users to FireRed’s stricter input rules.

**Path B – Whisper-Compatible Fine-Tune:**
- Focus: BELLE-2 whisper-large-v3-zh.
- Strength: 24–65 % CER reduction over base Whisper while retaining the same decoder hooks, enabling fastest drop-in upgrade for today’s pipeline.
- Trade-offs: Still autoregressive, so throughput similar to current Whisper unless combined with quantization/temperature sweeps; must verify timestamp stability vs Whisper Desktop.

**Path C – Mandarin-Optimized Non-Autoregressive:**
- Focus: SenseVoice-Small/Large, Paraformer-zh.
- Strength: Built for offline Mandarin; SenseVoice-Small achieves ~15× Whisper-L throughput, Paraformer has integrated VAD/punctuation and streaming chunk configs—ideal for 10–20 concurrent local sessions.
- Trade-offs: Need side-by-side comparison with Whisper Desktop on dense meeting speech; SenseVoice-L needs ONNX/TensorRT export for best latency; Paraformer chunking may require second-pass alignment to keep timestamps precise.

**Evaluation:**
- Path B offers the quickest accuracy uplift with minimal plumbing changes.
- Path A provides maximum headroom if we can budget VRAM and segmentation orchestration.
- Path C should be prototyped early to prove near-realtime performance under local GPU constraints.

### Expert Panel Perspectives
- **ASR Research Scientist:** Push for FireRedASR-AED as the accuracy ceiling (0.55 CER AISHELL-1, <5 CER WenetSpeech) but plan for ≥40 GB VRAM, ≤60 s windows, and careful decoding penalties per repo guidance before batching longer meetings.
- **Infrastructure Engineer:** Advocate BELLE-2 whisper-large-v3-zh first because it preserves existing Whisper decoder hooks and can leverage current quantization + timestamp tooling; run SenseVoice-Small ONNX trials in parallel to validate 15× faster inference for concurrency bursts.
- **Product/UX Owner:** Sequence work so BELLE parity lands quickly while FireRed/SenseVoice pilots must prove timestamp stability and deliver automated transcript diffs against the Const-me reference to rebuild user trust.

---

## 3. Detailed Technology Profiles

### Option 1: BELLE-2 Whisper-Large-v3-zh

**Overview:** Full-parameter fine-tune of OpenAI’s Whisper large-v3 focused on Mandarin accuracy; trained on AISHELL‑1/2, WenetSpeech, and HKUST, delivering 24–65 % relative CER improvement over base Whisper across those benchmarks (Hugging Face model card, 2025).

**Current Status (2025):** Latest release targets 16 kHz speech, reports CER 2.78 on AISHELL‑1, 3.79 on AISHELL‑2, 8.86 on WenetSpeech-net, and 11.25 on WenetSpeech-meeting while holding 16.44 on HKUST dev—substantially lower than stock Whisper’s 8–28 CER on the same sets (model card table).

**Technical Characteristics:**
- Architecture inherits Whisper large-v3 (decoder-compatible transformer) so existing Whisper decoding hooks—including forced decoder IDs for zh transcription—carry over without pipeline changes (model card usage snippet).
- Requires 16 kHz mono input; fine-tune performed via full-parameter training (Whisper-Finetune GitHub reference in model card).
- Maintains autoregressive decoding so beam search/temperature ladders remain applicable; gains come from Mandarin-specific data rather than architectural shifts.

**Developer Experience:**
- Drop-in with `transformers` pipeline; sample code provided in model card including forced decoder IDs for zh.
- Existing WhisperX alignment/timestamp tooling should continue to work because tokenization + ID space is unchanged (analysis).
- Full fine-tune instructions in linked GitHub repo for future domain adaptation.

**Operations:**
- Model size remains Whisper large-v3 (~1.55 B parameters); expect same VRAM footprint and throughput as current Whisper deployments.
- Supports on-prem deployment wherever Whisper already runs; no extra runtime dependencies beyond PyTorch/Transformers.

**Ecosystem & Support:**
- Backed by BELLE group with active GitHub/ModelScope presence; downloads ~1.6 k (ModelScope stats, 2024-03-11 release) show adoption momentum.
- Community resources via BELLE GitHub (LianjiaTech/BELLE) and Whisper-Finetune repo.

**Costs/Risks:**
- Apache-2.0 license; infrastructure cost mirrors existing Whisper usage.
- Still autoregressive, so throughput and latency match current Whisper; verify timestamp stability and accuracy versus Const-me references before rollout.

**Sources:** Hugging Face BELLE-2/Belle-whisper-large-v3-zh model card; model.aibase Belle profile (accessed 2025-11-09).

### Option 2: SenseVoice (Small/Large)

**Overview:** Multilingual speech foundation models (ASR + LID + SER + AED) trained on >400 k hours across 50+ languages; SenseVoice-Small focuses on ultra-low-latency non-autoregressive decoding while SenseVoice-Large maximizes accuracy (FunAudioLLM/SenseVoice README, accessed 2025-11-09).

**Current Status (Nov 2024):** Update added CTC-based timestamps plus ONNX/libtorch export pipelines; benchmarks show SenseVoice-Small surpassing Whisper on AISHELL/WenetSpeech while processing 10 s of audio in ~70 ms (~15× faster than Whisper-L) per README inference plot.

**Technical Characteristics:**
- Non-autoregressive encoder-decoder with integrated VAD options (`fsmn-vad`) and emotion/event heads; supports dynamic batching via `batch_size_s` (seconds).
- Timestamping available via new CTC alignment; supports multilingual recognition (`language="zh"/"en"/"yue"/etc.).
- Rich transcription outputs (emotion + AED) optional; can be disabled for lean ASR-only mode.

**Developer Experience:**
- Provided through FunASR `AutoModel` API with `trust_remote_code=True`; sample scripts show toggling VAD, ITN, batch size, and export paths.
- ONNX and libtorch exporters plus Python runtimes (`funasr-onnx`, `funasr-torch`) simplify offline deployment.
- Documentation includes parameter descriptions and segmentation strategies, making it straightforward to align with KlipNote’s WhisperX-like workflow.

**Operations:**
- Recommended pipeline runs VAD to split long meetings into ≤30 s chunks, matching SenseVoice-Small’s inference constraints while keeping timestamps consistent.
- Non-autoregressive decoding keeps latency nearly flat as audio length grows, aiding the ≤2× realtime requirement for 10–20 concurrent sessions.
- Supports multi-client service deployment with provided web UI and SDKs (Python, C++, Java, C#, HTML).

**Costs/Risks:**
- Licensed under the FunASR model license (Hugging Face metadata); confirm compatibility with KlipNote’s distribution model.
- Need to validate Mandarin meeting accuracy vs Const-me reference because public benchmarks focus on cleaner corpora; may require alignment tweaks to match WhisperX timestamps.

**Speedrun Validation Plan:**
1. Export Const-me reference transcripts (already in `reference/zh_quality_optimization`) and build a CER/timestamp diff harness.
2. Generate SenseVoice-Small ONNX runtime with `merge_vad=True`, `max_single_segment_time=30000`, mirroring WhisperX segmentation but capping segments ≤30 s.
3. Benchmark a 60‑minute audio batch on the current KlipNote GPU to verify ≤1.5× realtime throughput; tune `batch_size_s` and disable SER/AED heads if needed.
4. Run the diff harness to compare SenseVoice outputs vs Const-me transcripts, ensuring loops disappear and CER sits within ~5 % of target; flag segments needing post-edit.
5. Package ONNX runtime + VAD + post-processing into the offline stack to prove zero network dependency before a beta rollout.

**Sources:** FunAudioLLM/SenseVoice README (EN & ZH), Hugging Face SenseVoiceSmall model card, FunAudioLLM GitHub (accessed 2025-11-09).

### Option 3: FunASR Paraformer-zh (Non-Streaming + Streaming)

**Overview:** Mandarin-specific Paraformer model (220 M parameters) trained on 60 k hours of speech, available in non-streaming (timestamped) and streaming variants plus companion VAD (`fsmn-vad`) and punctuation (`ct-punc`) models for an end-to-end pipeline (Hugging Face `funasr/paraformer-zh` README, accessed 2025-11-09).

**Current Status (v2.0.4):** Latest checkpoints expose both offline and streaming modes; streaming profile uses 600 ms chunks with 300 ms lookahead (`chunk_size = [0,10,5]`) to keep latency low. AutoModel revisions (`model_revision="v2.0.4"`) ensure reproducible runtime behavior.

**Technical Characteristics:**
- Non-autoregressive Paraformer architecture that outputs sentences in parallel, reducing decoding latency relative to Whisper; optimized solely for Mandarin vocabulary.
- Built-in timestamps on non-streaming model; streaming version adds encoder/decoder look-back controls and `is_final=True` flush for final chunk (README streaming example).
- Tight coupling with FunASR ecosystem: integrate VAD, punctuation, timestamp prediction, and hotwording via consistent APIs.

**Developer Experience:**
- Simple `AutoModel` usage: `model="paraformer-zh"` or `"paraformer-zh-streaming"` with optional VAD/punctuation modules and hotword list; CLI supports Kaldi-style wav.scp lists.
- Streaming recipe demonstrates chunked inference loop with adjustable chunk sizes and look-back windows; documentation covers command-line and Python SDK paths.
- Same tooling as SenseVoice, easing experiments across both families.

**Operations:**
- Designed for on-prem deployments; combine ASR + VAD + punctuation models to form a fully offline transcription service.
- Streaming config aligns with KlipNote’s ≤2× realtime target—600 ms chunks provide responsive diarized output, with knobs ([0,8,4]) for stricter latency if needed.
- 220 M parameter footprint fits mid-range GPUs and even CPU inference (with throughput tradeoffs) using FunASR runtimes.

**Ecosystem & Support:**
- Maintained by Alibaba DAMO/FunASR team; mirrored on ModelScope and Hugging Face with extensive documentation and service deployment guides.
- Active FunASR community plus PyPI releases (`funasr`) provide regular updates and tutorials.

**Costs/Risks:**
- Distributed under the FunASR model license; verify redistribution requirements.
- Mandarin-only focus means separate solutions are required for other languages; dependence on FunASR runtimes introduces an additional dependency for KlipNote.

**Speedrun Validation Plan:**
1. Reuse the Const-me diff harness to score Paraformer outputs vs reference transcripts (both non-streaming and streaming modes).
2. Stand up FunASR `AutoModel` with `paraformer-zh-streaming`, `chunk_size=[0,10,5]`, and `fsmn-vad` to mirror KlipNote’s diarized pipeline; capture timestamp alignment for a 30‑minute meeting sample.
3. Benchmark latency on a single KlipNote GPU by sweeping chunk configs ([0,8,4], [0,6,3]) to ensure ≤2× realtime while preserving timestamp stability.
4. Layer `ct-punc` and hotword lists, then rerun the diff harness to confirm no hallucinated loops or timestamp drift relative to Const-me reference.
5. Package the FunASR runtime (models + VAD + punctuation) into an offline container to validate zero-network deployment before user testing.

**Sources:** Hugging Face `funasr/paraformer-zh` README (v2.0.4), FunASR GitHub documentation (accessed 2025-11-09).

### Option 4: FireRedASR (LLM & AED)

**Overview:** Open-source industrial-grade Mandarin ASR family released in Jan–Feb 2025 with two variants: FireRedASR-LLM (8.3 B parameters using an Encoder→Adapter→LLM stack) and FireRedASR-AED (1.1 B attention encoder-decoder) targeting maximum accuracy while remaining self-hostable (FireRedTeam/FireRedASR README and blog).

**Current Status (2025):** Technical report + weights published Jan 24 and Feb 17, 2025. Benchmark table shows AISHELL-1 CER 0.76 (LLM) / 0.55 (AED) and WenetSpeech-meeting CER 4.67 / 4.76, outperforming SenseVoice-L and Paraformer-Large (README table; FireRed blog).

**Technical Characteristics:**
- LLM variant chains a high-capacity encoder with adapter into an instruction-following LLM for conversational ASR; AED variant balances efficiency with attention-based decoding.
- Inputs must be chunked: AED supports ≤60 s segments (hallucinations beyond that), LLM ≤30 s (behavior unknown for longer audio) per README usage notes.
- Decoding parameters (beam size, repetition penalty, length penalties, smoothing) exposed for both variants to manage hallucinations and repetition loops.

**Developer Experience:**
- Python CLI + API provided; requires downloading weights from Hugging Face (plus Qwen2-7B for LLM variant). Example scripts show `FireRedAsr.from_pretrained("aed", ...)` with GPU flag.
- Batch beam search requires similar-length utterances; README warns that mixing lengths can reintroduce repetitions—must pre-sort or use `batch_size=1` when lengths diverge.
- Setup uses Conda/Pip plus `requirements.txt`; includes instructions for ffmpeg conversions and environment variables.

**Operations:**
- Parameter counts (1.1 B / 8.3 B) imply large VRAM needs; expect ≥40 GB for LLM variant to batch more than one stream. AED may run on 24 GB cards but still requires segmentation pipeline.
- Chunking limits mean KlipNote must add VAD/segmentation to keep windows ≤60 s (AED) or ≤30 s (LLM) and then stitch timestamps via secondary alignment (e.g., WhisperX-style pass).
- README notes hallucination risk beyond supported lengths; also warns about repetition on shorter utterances unless sorted—fits with observed loops in the current pipeline, so QA harness is essential.

**Ecosystem & Support:**
- Active GitHub (≈1.6 k stars) plus blog/demo/paper; releases include example scripts, Hugging Face models, and instructions for LLM integration with Qwen2-7B.
- Community is nascent but positioned as SOTA research; citations include arXiv:2501.14350.

**Costs/Risks:**
- Apache-2.0 license but large VRAM footprint raises infra cost; segmentation complexity adds engineering overhead.
- Input-length constraints + repetition sensitivities require robust chunk orchestration and QA before user exposure.
- LLM variant depends on Qwen2-7B weights, increasing storage footprint and model management complexity.

**Critique & Refinement (Quality Checks):**
- *Assumption check:* Benchmark data (AISHELL/WenetSpeech) is far cleaner than KlipNote’s noisy meeting audio; FireRed’s SOTA CER may not translate without domain adaptation or post-filtering—must validate on internal case files before committing resources.
- *Operational realism:* README warnings about ≤60 s/≤30 s windows translate into multi-stage segmentation plus reassembly; that engineering effort may outweigh gains unless the accuracy delta vs BELLE/SenseVoice is material.
- *Risk exposure:* VRAM ≥40 GB for the LLM path and dependency on Qwen2-7B make FireRed hard to ship for individual users unless KlipNote distributes trimmed AED builds or optional “HQ mode”.
- *Recommendation:* Treat FireRed as a stretch goal after BELLE/SenseVoice parity; invest in an automated chunk QA harness (length sorting, repetition penalties) before prototyping to avoid repeating the current “gibberish loops” failure mode.

**Sources:** FireRedTeam/FireRedASR GitHub README, FireRed technical report/blog (accessed 2025-11-09).

---

## 4. Comparative Analysis

| Dimension | BELLE-2 Whisper-L3-zh | SenseVoice Small/Large | Paraformer-zh (FunASR) | FireRedASR (AED/LLM) | Const-me Whisper Desktop |
| --- | --- | --- | --- | --- | --- |
| **Accuracy vs benchmark** | High – 2.8 CER AISHELL-1, 11.2 CER WenetSpeech meeting (SRC: HF) | Medium/High – outperform Whisper on AISHELL/WenetSpeech; real-world TBD | Medium – 60 k h Mandarin training, non-SOTA but strong | Very High – 0.55–0.76 CER AISHELL-1, <4.8 CER WenetSpeech | Baseline – proven good on KlipNote audio |
| **Throughput / Latency** | Medium – matches Whisper large (~1.5–2× realtime) | High – NAR, ~70 ms per 10 s (15× faster than Whisper-L) | High – streaming chunk configs keep ≤2× realtime | Low – large VRAM, short windows; overall <1× realtime unless heavy GPUs | Medium – GPU-accelerated but still AR |
| **Deployment Complexity** | Low – drop-in replacement | Medium – requires FunASR runtime + VAD config | Medium – FunASR stack + VAD + punctuation | High – segmentation, VRAM, extra LLM weights | Low – existing desktop app |
| **Ecosystem / Support** | Mature – BELLE community, ModelScope + HF | Growing – FunAudioLLM team, ONNX runtimes | Mature – Alibaba DAMO/FunASR | Emerging – new repo (1.6 k stars), limited adopters | Stable but Windows-only |
| **Offline / On-Prem Fit** | Yes – same as Whisper | Yes – ONNX/libtorch exports, zero cloud | Yes – fully offline service scripts | Yes – open source but resource intensive | Yes – Windows desktop |
| **Key Risks** | Must verify meeting accuracy/timestamps | Needs validation on noisy speech; license review | Mandarin-only; FunASR dependency | Heavy VRAM, chunk QA, risk of loops if unmanaged | Accuracy plateau vs new options |

**Observations:**
- BELLE provides the fastest accuracy uplift with minimal engineering effort; accuracy gains are documented on Mandarin benchmarks but still require KlipNote audio validation.
- SenseVoice and Paraformer are the strongest plays for meeting the ≤2× realtime requirement while keeping processing local—SenseVoice prioritizes low latency, Paraformer offers robust streaming controls through FunASR.
- FireRed represents the accuracy ceiling but imposes strict chunking and VRAM needs; best treated as a later-phase enhancement once automation (segmentation, QA harness) is in place.
- Const-me Whisper Desktop remains the user-trust baseline; automated diffs against it should gate every experiment to ensure no regression in hallucinations or timestamps.

### Weighted Analysis

**Decision Priorities:**
{{decision_priorities}}

{{weighted_analysis}}

---

## 5. Trade-offs and Decision Factors

{{use_case_fit}}

### Key Trade-offs

1. **FireRedASR vs BELLE-2:** FireRed promises sub-1 % CER but at the cost of extreme VRAM needs and brittle chunk management; BELLE sacrifices some headroom yet plugs directly into the existing Whisper stack with near-zero engineering effort. Choose FireRed when accuracy is worth delaying deployment and you can automate chunk QA; choose BELLE when immediate parity with Const-me is the goal.
2. **SenseVoice vs Paraformer:** SenseVoice-Small offers the fastest low-latency path with multilingual support and ONNX exports, but relies on SenseVoice-specific runtimes; Paraformer integrates seamlessly with the broader FunASR pipeline (VAD, punctuation) and offers streaming control, yet remains Mandarin-only and slightly heavier operationally. Pick SenseVoice for speed-centric experiments; pick Paraformer when you need tight VAD/punctuation coupling and predictable streaming semantics.
3. **Paraformer/SenseVoice vs BELLE:** NAR models (SenseVoice/Paraformer) reduce latency and concurrency load but require adopting FunASR runtimes and new tooling, whereas BELLE maintains the current Whisper-based ecosystem at the cost of higher latency. Select BELLE to minimize change management; select SenseVoice/Paraformer when concurrency pressure or user experience demands snappier turnaround.
4. **FireRed vs SenseVoice/Paraformer:** FireRed yields the highest accuracy but with much higher engineering complexity and resource usage; SenseVoice/Paraformer deliver “good enough” accuracy with better latency and simpler hardware requirements. Favor FireRed only after lightweight NAR options have proven insufficient to close the quality gap.

**Use Case Fit Notes:**
- Mandatory hardware ceiling: deployments must run on NVIDIA GeForce RTX 3070 Ti 16 GB GPUs. This eliminates FireRedASR-LLM (requires ≥40 GB VRAM) and severely constrains FireRedASR-AED unless concurrency is limited to single-stream with aggressive chunking.
- BELLE-2, SenseVoice-Small, and Paraformer-zh all comfortably fit within 16 GB VRAM (with headroom for 1–2 concurrent sessions), making them viable within the constraint.

---

## 6. Real-World Evidence

- BELLE-2: Early adopters report Mandarin business-meeting improvements aligned with AISHELL/Wenet benchmarks (ModelScope reviews, 2024-2025). Needs KlipNote-specific validation due to noise domain differences.
- SenseVoice: FunAudioLLM demo and community posts (ModelScope studios, Linux.do threads) highlight low-latency Mandarin performance when deployed via sherpa-onnx; timestamp support was only added Nov 2024, so production stories are emerging.
- Paraformer: Alibaba DAMO references industrial deployments built on FunASR service scripts; streaming mode documented with chunk-level performance guidance.
- FireRed: Released Feb 2025 with limited field stories so far; paper and blog emphasize SOTA benchmarks but advise caution for inputs exceeding supported window sizes.
- Const-me Whisper Desktop: Long-standing reference implementation used by KlipNote to establish trust; real-world evidence collected internally via `reference/zh_quality_optimization`.

---

## 7. Architecture Pattern Analysis

{{#architecture_pattern_analysis}}
{{architecture_pattern_analysis}}
{{/architecture_pattern_analysis}}

---

## 8. Recommendations

**Primary Recommendation:** Adopt a two-track approach:

1. **Immediate Accuracy Upgrade – BELLE-2 Whisper-L3-zh:** Drop-in replacement for the current Whisper decoder to close the gap with Const-me while preserving existing tooling and staying within the RTX 3070 Ti envelope. Run the Const-me diff harness across representative meeting files before rollout to confirm timestamp stability.
2. **Low-Latency Pilot – SenseVoice-Small (ONNX):** Stand up the ONNX runtime with VAD chunking to validate near-realtime concurrency (≤1.5× realtime) on the same hardware. If accuracy holds within ~5 % of BELLE, position SenseVoice as the high-speed mode for users prioritizing turnaround.

**Next-in-line:** Evaluate Paraformer-zh streaming once the FunASR stack is in place; treat FireRedASR-AED as a longer-term stretch goal after automated chunk QA harnesses are mature.

### Implementation Roadmap

1. **Proof of Concept Phase**
   - Run BELLE-2 vs Const-me regression (CER + timestamp diff) on three noisy meeting recordings.
   - Export SenseVoice-Small ONNX and measure latency on RTX 3070 Ti for a 60-minute audio batch.

2. **Key Implementation Decisions**
   - Decide whether BELLE-2 replaces the current default decoder or ships as an opt-in “Mandarin HQ” preset.
   - Determine if SenseVoice runs as a background service or user-selectable local engine; codify fallback logic to Whisper when runtime errors occur.

3. **Migration Path** (if applicable)
   - Rolling update: deploy BELLE-2 weights alongside existing Whisper models, gate rollout behind the diff harness, then retire the old checkpoint once parity is confirmed.
   - For SenseVoice/Paraformer pilots, bundle FunASR runtimes and config templates within the app, but keep experiments behind feature flags until QA completes.

4. **Success Criteria**
   - BELLE-2: ≤5 % CER delta vs Const-me on noisy meetings, zero timestamp regressions, zero new hallucination loops.
   - SenseVoice: ≤1.5× realtime latency on RTX 3070 Ti, accuracy within ~5 % of BELLE-2, stable ONNX pipeline without network calls.
   - Paraformer (optional): streaming chunk config hitting ≤2× realtime with consistent timestamps.

### Risk Mitigation

- Maintain Const-me diff harness as regression guardrail for every new model.
- For SenseVoice/Paraformer, sandbox FunASR runtimes to ensure no unexpected package updates or network dependencies.
- For FireRed experiments, limit to AED variant and enforce ≤60 s chunking with automated length sorting to prevent repetition loops.

---

## 9. Architecture Decision Record (ADR)

**Status:** Proposed

**Context:** KlipNote must restore trust in Mandarin transcripts by matching the Const-me Whisper Desktop quality baseline while staying entirely offline on RTX 3070 Ti 16 GB hardware and supporting 10–20 concurrent self-service users.

**Decision Drivers:**
- Absolute accuracy vs Const-me reference (priority #1)
- Future flexibility to iterate on low-latency engines (SenseVoice/Paraformer) (priority #2)
- Latency/throughput targets (≤2× realtime) (priority #3)

**Considered Options:** BELLE-2 Whisper-L3-zh, SenseVoice Small/Large, FunASR Paraformer-zh, FireRedASR (AED/LLM), Const-me Whisper Desktop baseline.

**Decision:** Adopt BELLE-2 as the immediate default Mandarin decoder, pilot SenseVoice-Small ONNX for low-latency mode, stage Paraformer-zh streaming as a FunASR-based follow-up, and reserve FireRedASR-AED for future high-accuracy experiments once automation is mature.

**Consequences:**
- Positive: Rapid accuracy gains without architectural upheaval (BELLE); clear path to low-latency experience (SenseVoice); alignment with hardware ceiling.
- Negative: Need to maintain multiple runtime stacks (Transformers + FunASR); FireRed accuracy ceiling deferred until heavier infrastructure and QA investments are feasible.

---

## 10. References and Resources

### Documentation

- [Links to official documentation]

### Benchmarks and Case Studies

- [Links to benchmarks and real-world case studies]

### Community Resources

- [Links to communities, forums, discussions]

### Additional Reading

- [Links to relevant articles, papers, talks]

---

## Appendices

### Appendix A: Detailed Comparison Matrix

[Full comparison table with all evaluated dimensions]

### Appendix B: Proof of Concept Plan

[Detailed POC plan if needed]

### Appendix C: Cost Analysis

[TCO analysis if performed]

---

## References and Sources

**CRITICAL: All technical claims, versions, and benchmarks must be verifiable through sources below**

### Official Documentation and Release Notes

{{sources_official_docs}}

### Performance Benchmarks and Comparisons

{{sources_benchmarks}}

### Community Experience and Reviews

{{sources_community}}

### Architecture Patterns and Best Practices

{{sources_architecture}}

### Additional Technical References

{{sources_additional}}

### Version Verification

- **Technologies Researched:** {{technology_count}}
- **Versions Verified ({{current_year}}):** {{verified_versions_count}}
- **Sources Requiring Update:** {{outdated_sources_count}}

**Note:** All version numbers were verified using current {{current_year}} sources. Versions may change - always verify latest stable release before implementation.

---

## Document Information

**Workflow:** BMad Research Workflow - Technical Research v2.0
**Generated:** {{date}}
**Research Type:** Technical/Architecture Research
**Next Review:** [Date for review/update]
**Total Sources Cited:** {{total_sources}}

---

_This technical research report was generated using the BMad Method Research Workflow, combining systematic technology evaluation frameworks with real-time research and analysis. All version numbers and technical claims are backed by current {{current_year}} sources._

---

Checkpoint: research_type_discovery
- research_type: technical
- research_mode: technical
- focus: Chinese ASR accuracy tuning with offline, low-latency constraints
## Technical Question & Context
- technical_question: How to reach Whisper Desktop parity for Mandarin ASR accuracy while keeping processing local/offline.
- project_context: Personal-productivity meeting recorder targeting individual knowledge workers; accuracy gaps cause adoption risk.

### Functional Requirements
- Primary objective: achieve Mandarin transcription accuracy on par with Const-me Whisper Desktop reference outputs; all other enhancements are secondary.

### Non-Functional Requirements
- Transcription speed must be optimized aggressively; aim for near-realtime throughput despite accuracy-focused tweaks.

### Technical Constraints
1. Existing WhisperX-style decoder optimized for English; Mandarin requires tuned beam search, temperature fallback, and zh-specific suppression settings.
2. GPU capacity limited to self-hosted hardware serving ~10–20 concurrent users, so large models must balance accuracy vs. throughput.
3. Strict local/offline requirement: remain within open-source/on-prem models; no reliance on cloud ASR APIs.
4. End-to-end latency budget ≤2× realtime even with second-stage alignment or guided decoding tweaks.
