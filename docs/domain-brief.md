# Domain Brief - KlipNote

Generated: 2025-11-09
Domain: Personal Productivity – Transcription Accuracy Tools
Complexity: Low

## Executive Summary

{brief_overview_of_domain_research_findings}

## Domain Overview

### Industry Context

KlipNote operates in the lightweight personal productivity space, targeting individual knowledge workers who need accurate, fast, self-service meeting transcription without enterprise deployment overhead. The emphasis is on boosting personal efficiency rather than satisfying organizational governance programs.

### Regulatory Landscape

No formal industry regulations currently apply because KlipNote does not manage third-party client data or operate in regulated workflows. Privacy expectations still exist, but compliance frameworks (HIPAA, PCI, SOC 2) are not in scope for the present focus on accuracy improvements.

### Key Stakeholders

Primary stakeholders are end users (meeting owners) who depend on trustworthy transcripts to feed downstream LLM workflows. Secondary stakeholders are the internal product/engineering team monitoring accuracy metrics and iterating on the transcription model pipeline.

## Critical Concerns

### Compliance Requirements

1. Current in-house pipeline produces large runs of duplicated, semantically wrong text (see `reference/zh_quality_optimization/case1/current_project.txt:1-40` showing nonsensical loops like “我用了一尾” and “来,我给你拿来洗” repeated dozens of times). Word error rate and hallucinations dominate the perceived quality gap.
2. Baseline open-source reference (Const-me/Whisper desktop build) yields coherent business-meeting content for the same audio (`reference/zh_quality_optimization/case1/WhisperDesktop.txt:1-80`), proving higher quality is achievable without new data collection.
3. Timestamp stability must stay intact even when accuracy tuning introduces more aggressive decoding or language-specific heuristics.
4. Local/offline processing remains a soft requirement so users trust that private Mandarin meetings never leave their hardware.

**Criticality:** Accuracy + timestamp integrity define customer value; we can defer broader concerns (compliance, multi-language) until the Mandarin pipeline matches the open-source benchmark.

**Must-have vs. later:** Achieve parity with Const-me decoding quality ASAP; privacy narrative already satisfied; export fidelity can iterate later but must not regress during optimization.

**Support needed:** Mandarin ASR expertise to compare decoder settings/quantization strategies, plus tooling to diff transcripts vs. reference outputs for fast regression detection.

### Technical Constraints

1. Current transcription stack likely uses WhisperX or a similar server-side decoder tuned for English; Mandarin performance suffers unless beam search, temperature fallback, and language-specific suppression tweaks are enabled.
2. GPU budget is limited to self-hosted hardware for 10–20 concurrent users (per PRD), so large-model experiments must balance accuracy gains with throughput.
3. Local/offline preference limits reliance on cloud ASR APIs (Azure, Google) that might otherwise offer turnkey Mandarin quality; optimizations must stay within open-source/on-prem models.
4. Need to preserve near real-time user experience: any accuracy boosting pass (second-stage alignment, guided decoding) must still keep total processing time within 1–2× realtime, or users will abandon the tool.

### Safety/Risk Considerations

1. **User trust erosion:** Repetitive gibberish transcripts make users re-listen entire meetings, undermining adoption.
2. **Decision risk:** Inaccurate meeting summaries fed into LLM workflows can create false action items or missed commitments.
3. **Data exposure temptation:** If quality stays low, users might upload recordings to third-party cloud services despite privacy concerns, reintroducing the very risks KlipNote wants to avoid.

## Regulatory Requirements

No formal regulatory regimes currently bind KlipNote because it targets personal productivity and runs entirely on user-controlled infrastructure. Still, we must uphold baseline privacy expectations:

- Keep processing local/offline so meeting audio never leaves trusted hardware.
- Provide clear disclosure that transcripts live on the user’s machine and can be deleted at any time.
- Offer simple export/delete controls so individuals satisfy any company policy they work under.

There are no HIPAA/PCI/FINRA-style certifications to pursue at this stage; our “regulation” is self-imposed transparency and data minimization.

## Industry Standards

- **Whisper-derived tooling (Const-me/Whisper, faster-whisper):** Demonstrates that high-quality Mandarin is achievable via larger models (ggml-medium/large-v3) plus beam search, temperature fallback, and VAD filtering. We should match their default decoder safeguards to avoid repetitive tokens.
- **Prompt + chunking practices (StackOverflow 78246902):** Use initial prompts/word lists (≤244 tokens) for domain vocabulary, break long meetings into 5–10 minute chunks, and optionally fine-tune on accent-specific corpora to reduce WER.
- **Hallucination mitigation (faster-whisper issue #465, Const-me issue #246):** Community guidance highlights tweaking suppressed tokens, enforcing `logprob_threshold`, and enabling temperature increment fallback to stop runaway repetitions—directly relevant to our current failure mode.
- **Quality metrics:** Track word error rate (WER) and character error rate (CER) per locale, with regression harnesses comparing our outputs against reference transcripts (e.g., Const-me results) before releasing new models.

## Practical Implications

### Architecture Impact

- Add a pluggable ASR engine layer so WhisperX, Const-me GPU build, faster-whisper, and FunASR (Paraformer/SenseVoice pipelines) can be benchmarked side-by-side without UI changes.
- Introduce a pre-processing microservice (FFmpeg + VAD) that normalizes Mandarin audio, enforces chunk sizes (5–10 min), and feeds both Whisper-derived decoders and FunASR runtimes.
- Store intermediate logits/timecodes so timestamp alignment can be re-used when swapping models; ensures click-to-timestamp stays accurate regardless of backend.
- Bundle an evaluation harness (WER/CER diff vs. reference transcripts) into CI so any tweak to decoding parameters or model selection runs regression suites automatically.

### Development Impact

- Build adapters for FunASR’s offline transcription service (supports Paraformer-large, SenseVoice, Whisper-large-v3 turbo) to run locally alongside existing Whisper pipeline.
- Implement chunking + prompt injection utilities (StackOverflow 78246902 guidance) and expose them as configurable knobs in the job runner.
- Capture user edits as structured diffs to power supervised fine-tuning or LM-based cleanup passes; requires lightweight annotation tooling in the editor.
- Expand QA: automated scripts compare `current_project` style fixtures against `WhisperDesktop` or FunASR outputs, flagging WER/T timestamp deltas prior to release.

### Timeline Impact

- Short term (1–2 sprints): integrate decoder safeguards (temperature fallback, suppressed tokens) and chunking to eliminate gross repetitions.
- Mid term (3–4 sprints): wire up FunASR models + evaluation harness, run A/B tests on Mandarin corpora, and backfill regression suites.
- Long term: schedule periodic re-benchmarking when new open-source checkpoints drop (FunASR monthly releases, Whisper large-v3 updates) to keep accuracy competitive.

### Cost Impact

- Compute: larger Mandarin models (large-v3, Paraformer-large) may require upgrading self-hosted GPUs or adding a second inference node; estimate +1 high-VRAM GPU.
- Engineering time: 2–3 engineer-weeks to implement pluggable pipeline, chunking utilities, and evaluation harness.
- Software/licensing: all referenced stacks are MIT/MPL, so no licensing fees; primary “cost” is maintaining multiple model artifacts and regression datasets.

## Domain Patterns

### Established Patterns

1. **Guarded Whisper Pipelines (Const-me/Whisper, faster-whisper):** Run large-v3 or medium models locally with GPU acceleration, enforce beam search + temperature fallback + token suppression to avoid hallucinations, and provide UI toggles for VAD and chunking. Pros: battle-tested, easy to embed; Cons: still autoregressive so latency grows with audio length; Use when you want quickest path to higher quality while staying in Whisper ecosystem.
2. **Paraformer/SenseVoice (FunASR):** Non-autoregressive Mandarin-centric models with built-in punctuation, hotword WFSTs, and VAD. Pros: excellent Mandarin accuracy + fast inference; Cons: larger runtime, more ops to integrate; Use when Chinese accuracy is top priority and you can invest in FunASR runtime.
3. **Two-pass pipelines:** First-pass fast model (small/medium) for rough transcript + timestamps, second-pass high-accuracy model or LLM cleanup referencing user dictionary. Pros: balances speed + quality; Cons: adds complexity and requires good synchronization logic; Use when UX needs fast preview while final transcript can take longer.
4. **User-driven wordlist prompting:** Accept glossary/prompt tokens per job (StackOverflow 78246902) so specialized names render correctly. Pros: simple knob for accuracy; Cons: relies on user input; Use when meetings often include acronyms or dialect-specific vocabulary.

### Innovation Opportunities

- **Hybrid engine orchestration:** Automatically route segments to the engine that performs best (e.g., FunASR for Mandarin-only stretches, Whisper for mixed-language). Requires confidence scoring and seamless stitching, but could outperform any single model.
- **Live regression harness:** Bundle fixtures like `case1` and Const-me baselines into the product so every user-run accuracy tweak (temperature, model swap) can be previewed before committing; educates users and crowdsources best configs.
- **Intelligent prompting assistant:** Suggests glossary terms by scanning previous transcripts or uploaded agendas, lowering friction for the word-list pattern.

## Risk Assessment

### Identified Risks

1. **Model regressions:** Tuning Whisper decoding or swapping models could reintroduce hallucinations unless every change runs through regression fixtures (likelihood: medium, impact: high). Mitigation: automated WER/timestamp diff harness and canary jobs.
2. **FunASR integration complexity:** Paraformer/SenseVoice runtime may demand more GPU VRAM and introduces additional dependencies (likelihood: medium, impact: medium). Mitigation: isolate in container, benchmark early, keep Whisper fallback ready.
3. **User trust erosion:** If accuracy doesn’t improve quickly, users may abandon KlipNote or upload to third-party services (likelihood: high, impact: high). Mitigation: ship visible accuracy gains sprint-by-sprint and highlight comparisons versus old pipeline.
4. **Maintenance overhead:** Supporting multiple engines (WhisperX, Const-me, FunASR) increases ops burden (likelihood: medium, impact: medium). Mitigation: pluggable abstraction, shared monitoring, periodic pruning of underperforming models.

### Mitigation Strategies

- **Regression harness:** lock in case fixtures (current_project) and reference transcripts (Const-me, FunASR) so every release must beat baseline WER/CER.
- **Config guardrails:** expose temperature/beam/prompt settings but guard with sensible defaults and warnings when users choose risky combos.
- **Staged rollouts:** deploy new decoders to internal test users before general release; collect feedback/logs to catch repetitions early.
- **Documentation + tutorials:** ship “best known config” guides (e.g., how to use glossary prompts) to accelerate user-driven accuracy boosts.

## Validation Strategy

### Compliance Validation

- Validate that transcripts/audio remain local: automated tests confirm no network egress during processing; document storage locations so users can delete data.
- Provide privacy notice text in the app and verify via UX review that users can export/delete recordings easily.

### Technical Validation

- Maintain WER/CER dashboards comparing current pipeline vs. Const-me and FunASR references on curated Mandarin corpora.
- Run timestamp-alignment tests ensuring click-to-timestamp deviations stay <100 ms after decoder swaps.
- Regression suite processes `reference/zh_quality_optimization/case1` before every release; fail build if hallucination loops resurface.

### Domain Expert Validation

- Engage native Mandarin reviewers (internal or contractors) to spot semantic errors beyond automated metrics.
- Pair with speech/ML experts (FunASR contributors, Whisper community) for periodic audits of decoder settings and tuning strategy.

## Key Decisions

- **Primary objective:** Focus all near-term work on Mandarin accuracy; defer multi-language and heavy compliance features.
- **Engine strategy:** Maintain Whisper-based pipeline but integrate FunASR (Paraformer/SenseVoice) as optional backends, exposing a pluggable abstraction.
- **Quality bar:** Use `reference/zh_quality_optimization/case1` and Const-me outputs as regression baselines; no release ships unless WER improves or at least matches benchmark.
- **Privacy posture:** Keep processing entirely local/offline, highlighting this advantage even though formal compliance isn’t required.

## Recommendations

### Must Have (Critical)

1. Implement decoder safeguards (beam search, temperature fallback, suppressed tokens) and chunking on the current Whisper pipeline to eliminate repetitive gibberish in Chinese transcripts.
2. Establish automated regression benchmarks comparing our outputs against Const-me/Whisper and FunASR references using `reference/zh_quality_optimization/case1` and similar fixtures.
3. Expose wordlist/prompt injection and language locking so Mandarin users can guide the model with jargon and prevent language drift.
4. Keep processing fully local/offline with clear UI messaging so privacy trust remains intact even as we tweak models.

### Should Have (Important)

1. Integrate FunASR Paraformer/SenseVoice runtimes as optional backends with adapters, enabling A/B tests and selective routing for Mandarin audio.
2. Capture user edits as structured diff logs to power future fine-tuning or LLM cleanup passes, turning every session into training data.
3. Build dashboards for WER/CER/timestamp metrics so product/engineering can monitor accuracy gains over time.

### Consider (Nice-to-Have)

1. Hybrid orchestration that automatically selects the best engine per segment (Whisper vs. FunASR) based on confidence and language detection.
2. Intelligent prompting assistant that suggests glossary terms by scanning past transcripts or uploaded agendas.
3. Two-pass pipelines (fast preview + high-accuracy finalize) to balance latency and quality for longer recordings.

### Development Sequence

1. **Sprint 1:** Add decoder safeguards + chunking, ship wordlist UI, set up regression harness with case fixtures.
2. **Sprint 2:** Integrate FunASR runtime in parallel to Whisper, wire evaluation dashboards, begin internal A/B tests.
3. **Sprint 3+:** Implement user edit capture + hybrid orchestration experiments, then iterate on analytics/prompt assistant.

### Required Expertise

- Speech/ML engineer familiar with Whisper/Const-me/Paraformer tuning to own decoder configuration.
- DevOps/infra engineer to manage GPU resources, containerize FunASR runtime, and maintain evaluation pipelines.
- Native Mandarin QA reviewers or linguists to audit semantic accuracy beyond automated metrics.

## PRD Integration Guide

### Summary for PRD

DOMAIN: Personal Productivity – Transcription Accuracy Tools
COMPLEXITY: Low (accuracy-focused scope)

KEY REQUIREMENTS TO INCORPORATE:

- Ship decoder safeguards + chunking + prompts so Mandarin transcripts match Const-me/Whisper benchmark quality.
- Maintain pluggable ASR architecture with FunASR adapters and automated regression harnesses.
- Keep processing fully local, highlighting privacy assurances even without formal compliance obligations.

IMPACTS ON:

- Functional Requirements: add configuration UI (wordlists, engine selection) and background evaluation jobs.
- Non-Functional Requirements: accuracy/WER dashboards, timestamp fidelity guarantees, local-processing assurances.
- Architecture: pluggable ASR layer, preprocessing microservice, FunASR containers, regression harness in CI.
- Development Process: staged rollouts, native reviewer loop, and ongoing benchmarking vs. reference transcripts.

### Requirements to Incorporate

- Decoder safeguards + chunking + prompt UI.
- Pluggable ASR layer with FunASR integration + regression harness.
- User edit capture + accuracy dashboards to sustain improvements.

### Architecture Considerations

- Preprocessing microservice (FFmpeg/VAD), ASR engine abstraction, FunASR runtime isolation, evaluation harness storage.
- Logging pathways for timestamps/logits so different engines can reuse alignments.

### Development Considerations

- Additional QA automation + native reviewer workflow.
- Feature flags and staging environments for trying new decoders safely.

## References

### Regulations Researched

- None (privacy obligations handled via local processing; no external certs).

### Standards Referenced

- Const-me/Whisper README (decoder safeguards) — https://github.com/Const-me/Whisper
- StackOverflow 78246902 (prompt + chunking best practices) — https://stackoverflow.com/questions/78246902/how-to-improve-whisper-speech-to-text
- faster-whisper issue #465 (repetition mitigation) — https://github.com/SYSTRAN/faster-whisper/issues/465
- Const-me issue #246 (mixed-language hallucinations) — https://github.com/Const-me/Whisper/issues/246
- FunASR README (Paraformer/SenseVoice runtimes) — https://github.com/modelscope/FunASR

### Additional Resources

- `reference/zh_quality_optimization/case1/current_project.txt` (current pipeline output)
- `reference/zh_quality_optimization/case1/WhisperDesktop.txt` (Const-me baseline)

## Appendix

### Research Notes

- Reviewed `reference/zh_quality_optimization/case1` transcripts showing severe repetition vs. Const-me baseline.
- Studied Const-me/Whisper README for decoder safeguards.
- Collected community mitigation advice (StackOverflow 78246902, faster-whisper issue #465, Const-me issue #246).
- Investigated FunASR toolkit (Paraformer/SenseVoice) and noted deployment patterns.

### Conversation Highlights

- User emphasized focus solely on transcription accuracy; other concerns out of scope for now.
- User provided reference transcripts demonstrating gap vs. Const-me/Whisper and requested leveraging open-source experience.
- Discussed leveraging Const-me defaults, FunASR integration, chunking, prompts, and regression harnesses.

### Open Questions

- What exact decoder configuration does KlipNote currently run (temperature, beam, suppression)?
- Which GPU resources are available for FunASR deployment and Paraformer-large inference?
- Do we have additional Mandarin corpora or user-provided glossaries to drive fine-tuning?

---

_This domain brief was created through collaborative research between Link and the AI facilitator. It should be referenced during PRD creation and updated as new domain insights emerge._
