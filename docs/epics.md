# KlipNote - Epic Breakdown

**Author:** Link
**Date:** 2025-11-03
**Project Level:** 2
**Target Scale:** Medium project - multiple epics, 10+ stories

---

## Overview

This document provides the detailed epic breakdown for KlipNote, expanding on the high-level epic list in the [PRD](./PRD.md).

Each epic includes:

- Expanded goal and value proposition
- Complete story breakdown with user stories
- Acceptance criteria for each story
- Story sequencing and dependencies

**Epic Sequencing Principles:**

- Epic 1 establishes foundational infrastructure and initial functionality
- Subsequent epics build progressively, each delivering significant end-to-end value
- Stories within epics are vertically sliced and sequentially ordered
- No forward dependencies - each story builds only on previous work

---

## Epic 1: Foundation & Core Transcription Workflow

**Expanded Goal:**

Establish the technical foundation for KlipNote by implementing the complete backend API architecture (FastAPI + Celery + WhisperX), basic frontend interface, and end-to-end upload → transcription → display workflow. This epic proves the core AI transcription capability works reliably and establishes the API-first architecture that enables future development. Upon completion, users can upload media files and receive accurate transcription results, validating the technical feasibility of the self-hosted GPU approach.

**Deliverable:** Users can upload media files and receive AI transcription results

---

**Story 1.1: Project Scaffolding and Development Environment**

As a developer,
I want the project structure and development environment configured,
So that I can begin building features on a solid foundation.

**Acceptance Criteria:**
1. Backend: FastAPI project initialized with proper directory structure (api/, models/, services/, tasks/)
2. Frontend: Vue 3 + Vite project initialized with component structure
3. Dependencies installed: FastAPI, Celery, Redis, Vue 3, Vite, Tailwind CSS v4.1.16+
4. Tailwind CSS v4 configured using `@tailwindcss/vite` plugin (NOT `@tailwindcss/postcss`)
   - `@tailwindcss/vite` added to `frontend/package.json` devDependencies
   - `tailwindcss()` plugin added to `frontend/vite.config.ts` plugins array
   - `frontend/src/assets/main.css` uses `@import "tailwindcss";` syntax (NOT `@tailwind` directives)
   - No `postcss.config.js` file exists in frontend directory
5. WhisperX integrated as git submodule at `ai_services/whisperx/`
6. Git repository configured with .gitignore for Python and Node
7. Basic README with setup instructions
8. Local development servers can run (backend on port 8000, frontend on port 5173)
9. Tailwind CSS utility classes render correctly (verify with test element using `bg-primary` or similar)

**Prerequisites:** None - first story in project

---

**Story 1.2: Backend API Upload Endpoint**

As a user,
I want to upload audio/video files through a web form,
So that I can start the transcription process.

**Acceptance Criteria:**
1. POST /upload endpoint accepts multipart/form-data file uploads
2. Validates file formats (MP3, MP4, WAV, M4A minimum)
3. Validates media duration using ffprobe - rejects files exceeding 2 hours (NFR-004)
4. Returns unique job_id for tracking
5. Saves uploaded file to server storage with job_id reference
6. Returns 400 error with clear message for unsupported formats or excessive duration
7. Handles files up to 2GB size (tested with actual 2GB file)
8. API endpoint documented in FastAPI auto-docs (/docs)

**Prerequisites:** Story 1.1 (project scaffolding)

---

**Story 1.3: Celery Task Queue and WhisperX Integration**

As a system,
I want to process transcription jobs asynchronously using WhisperX,
So that the web API remains responsive during long-running transcriptions.

**Acceptance Criteria:**
1. Celery configured with Redis broker
2. Transcription task accepts job_id and file path parameters
3. WhisperX integration transcribes media file with word-level timestamps
4. Task updates progress in Redis with stage-based messages:
   - Stage 1 (progress: 10): "Task queued..."
   - Stage 2 (progress: 20): "Loading AI model..."
   - Stage 3 (progress: 40): "Transcribing audio..." (longest stage)
   - Stage 4 (progress: 80): "Aligning timestamps..."
   - Stage 5 (progress: 100): "Processing complete!"
5. Task stores transcription result as JSON with subtitle segments [{start, end, text}]
6. Task handles transcription errors and stores error state with descriptive message
7. Celery worker can be started and processes jobs successfully

**Prerequisites:** Story 1.2 (upload endpoint provides job_id)

---

**Story 1.4: Status and Result API Endpoints**

As a user,
I want to check transcription progress and retrieve results,
So that I know when my transcription is ready and can access it.

**Acceptance Criteria:**
1. GET /status/{job_id} endpoint returns {status: "pending"|"processing"|"completed"|"failed", progress: 0-100}
2. GET /result/{job_id} endpoint returns transcription JSON with subtitle array
3. Status endpoint returns 404 for non-existent job_id
4. Result endpoint returns 404 if job not completed
5. Result endpoint returns error details if job failed
6. Both endpoints documented in FastAPI auto-docs

**Prerequisites:** Story 1.3 (Celery tasks generate status/results)

---

**Story 1.5: Frontend Upload Interface**

As a user,
I want a simple web page to upload my media file,
So that I can start using KlipNote without technical knowledge.

**Acceptance Criteria:**
1. Landing page displays file upload form with clear instructions
2. File input accepts audio/video formats (validated client-side)
3. Upload button triggers POST /upload API call
4. Success: Stores job_id and navigates to progress page
5. Failure: Displays error message from API
6. UI works on desktop, tablet, and mobile browsers
7. Basic responsive layout (no advanced styling required for MVP)
8. Drag-and-drop file upload supported (drop zone with visual feedback)

**Prerequisites:** Story 1.2 (upload API exists)

---

**Story 1.6: Frontend Progress Monitoring**

As a user,
I want to see real-time progress while my file is transcribing,
So that I know the system is working and how long to wait.

**Acceptance Criteria:**
1. Progress page polls GET /status/{job_id} every 3 seconds
2. Progress bar or percentage displayed visually
3. Status message shows current state ("Uploading...", "Processing...", "Complete!")
4. On completion: Automatically navigates to results view
5. On error: Displays error message with retry option
6. User can safely navigate away and return using job_id (in URL)
7. Polling stops when job completes or fails

**Prerequisites:** Story 1.4 (status API exists), Story 1.5 (upload flow provides job_id)

---

**Story 1.7: Frontend Transcription Display**

As a user,
I want to view the transcription results in a readable format,
So that I can verify the AI transcription quality.

**Acceptance Criteria:**
1. Results page calls GET /result/{job_id} on load
2. Displays subtitle segments as scrollable list
3. Each segment shows timestamp (MM:SS format) and text
4. Clear visual separation between subtitle segments
5. Handles long transcriptions (100+ segments) with smooth scrolling
6. Loading state while fetching results
7. Error handling if result fetch fails

**Prerequisites:** Story 1.4 (result API exists), Story 1.6 (progress flow navigates to results)

---

**Story 1.8: UI Refactoring with Stitch Design System**

As a user,
I want a professional, polished interface that matches modern design standards,
So that the application looks credible and is enjoyable to use.

**Acceptance Criteria:**
1. All Vue 3 template example elements removed (Vue logo, "You did it!" text, HelloWorld.vue, TheWelcome.vue, WelcomeItem.vue)
2. Tailwind CSS configured with Stitch design system (primary color: #137fec, dark background: #101922)
3. Google Fonts Inter and Material Symbols Outlined integrated
4. UploadView.vue redesigned with dark theme, glass-morphism card, and centered layout
5. ProgressView.vue redesigned with top nav bar, audio wave animation, and professional progress indicators
6. ResultsView.vue redesigned with media player placeholder area (for Epic 2), styled subtitle list with cards
7. ExportModal.vue component created (UI only, functionality in Epic 2)
8. All Epic 1 functionality verified working (upload, progress, transcription display)
9. Responsive design works on desktop, tablet, and mobile
10. No TypeScript errors, no console errors, code properly formatted

**Prerequisites:** Story 1.7 (all Epic 1 features completed)

---

## Epic 2: Integrated Review & Export Experience

**Expanded Goal:**

Build the differentiated review and editing interface that transforms KlipNote from basic transcription tool into a productivity powerhouse. Implement the killer feature - click-to-timestamp navigation - that enables rapid verification workflows, along with inline editing capabilities and export functionality. Establish the data flywheel foundation by persisting both original and human-edited transcriptions, creating the training dataset for future model improvements. Upon completion, users have a complete MVP that delivers the full value proposition: upload → review → edit → export workflow with data collection for continuous improvement.

**Deliverable:** Complete MVP - users can review, edit, and export transcriptions with data persistence

---

**Story 2.1: Media Playback API Endpoint**

As a user,
I want to play the original audio/video file in my browser,
So that I can hear what was said while reviewing the transcription.

**Acceptance Criteria:**
1. GET /media/{job_id} endpoint serves uploaded media file
2. Endpoint supports HTTP Range requests for seeking
3. Returns correct Content-Type header based on file format
4. Returns 404 for non-existent job_id
5. Handles partial content requests (206 status code)
6. Works with HTML5 video/audio elements in all target browsers
7. API endpoint documented in FastAPI auto-docs

**Prerequisites:** Story 1.7 (transcription display exists)

---

**Story 2.2: Frontend Media Player Integration**

As a user,
I want to see and control media playback within the transcription review interface,
So that I can listen to the recording while reviewing text.

**Acceptance Criteria:**
1. Integrated HTML5 video/audio player displayed above subtitle list
2. Player automatically selects correct element (video/audio) based on media type
3. Standard controls visible: play, pause, seek bar, volume, current time
4. Player loads media from GET /media/{job_id} endpoint
5. On load: Check localStorage for existing edits (key: `klipnote_edits_{job_id}`) and restore if present
6. Seeking works smoothly (Range request support validated)
7. Responsive layout: player scales appropriately on mobile/tablet
8. Player state persists during subtitle editing (doesn't reload unnecessarily)

**Prerequisites:** Story 2.1 (media API exists)

---

**Story 2.3: Click-to-Timestamp Navigation**

As a user,
I want to click any subtitle segment and jump to that exact moment in the media,
So that I can quickly verify what was actually said.

**Acceptance Criteria:**
1. Clicking any subtitle segment seeks media player to that segment's start time
2. Player automatically starts playing after seek
3. Currently playing segment is visually highlighted
4. Highlight updates automatically as playback progresses
5. Click response time <1 second (per NFR001)
6. Works on touch devices (tap interaction)
7. Visual feedback on hover/touch to indicate clickability

**Prerequisites:** Story 2.2 (media player exists)

---

**Story 2.4: Inline Subtitle Editing**

As a user,
I want to edit subtitle text directly in the interface,
So that I can correct transcription errors before export.

**Acceptance Criteria:**
1. Clicking subtitle text makes it editable (contenteditable or input field)
2. Changes update immediately in component state
3. Tab/Enter key saves edit and moves to next subtitle
4. Escape key cancels edit and reverts changes
5. Edited subtitles visually distinguished from unedited (subtle indicator)
6. Multiple subtitles can be edited in succession
7. Edits persist in localStorage (key: `klipnote_edits_{job_id}`) - auto-saved with throttling (500ms)
8. localStorage prevents data loss from browser refresh or accidental navigation (satisfies FR-020 & NFR-003)

**Prerequisites:** Story 1.7 (subtitle display exists)

---

**Story 2.5: Export API Endpoint with Data Flywheel**

As a system,
I want to capture both original and edited transcriptions during export,
So that I can build training data for future model improvements.

**Acceptance Criteria:**
1. POST /export/{job_id} endpoint accepts edited subtitle array in request body
2. Generates SRT file format from edited subtitles
3. Generates TXT file format (plain text, no timestamps) from edited subtitles
4. Stores both original transcription and edited version on server with job_id reference
5. Stores metadata: edit timestamp, number of changes, export format requested
6. Returns exported files for download (multipart response or separate endpoints)
7. API endpoint documented in FastAPI auto-docs
8. Privacy notice: Inform users that edited transcriptions may be retained for model improvement

**Prerequisites:** Story 1.4 (result API provides original), Story 2.4 (editing produces modified subtitles)

---

**Story 2.6: Frontend Export Functionality**

As a user,
I want to download my edited transcription in standard formats,
So that I can use it in LLM tools or subtitle players.

**Acceptance Criteria:**
1. Export button visible on editor page
2. Format selection: SRT or TXT (radio buttons or dropdown)
3. Export button calls POST /export/{job_id} with edited subtitle array
4. Success: Browser downloads file with appropriate name (job_id-transcript.srt/.txt)
5. Loading state during export processing
6. Error handling if export fails with clear message
7. Multiple exports allowed (user can export both formats sequentially)

**Prerequisites:** Story 2.5 (export API exists), Story 2.4 (edits available to send)

---

**Story 2.7: MVP Release Checklist & Final Validation**

As a project stakeholder,
I want comprehensive validation of the complete MVP system,
So that we can confidently release a reliable, production-ready application.

**Note:** This is a release validation phase, not a single 2-4 hour story. Treat ACs as a checklist spanning multiple days of QA work.

**Acceptance Criteria:**
1. Complete workflow tested: Upload → Progress → View → Edit → Export on 5+ different media files
2. Cross-browser testing completed: Chrome, Firefox, Safari (desktop + mobile)
3. Error handling verified for all failure scenarios (upload fail, transcription fail, network errors)
4. Performance validated: meets NFR001 targets (load <3s, playback <2s, seek <1s)
5. Mobile responsiveness verified on tablet and phone devices
6. Basic documentation updated: README with user instructions and developer setup
7. No critical bugs blocking MVP release
8. Error scenario testing: file size exceeded (>2GB), network timeout, WhisperX model download failure, concurrent job limits, corrupted media files
9. Safari-specific media seeking behavior tested (Safari playback controls may differ from Chrome/Firefox)

**Prerequisites:** All previous stories in Epic 1 and Epic 2

---

## Epic 3: Chinese Transcription Model Selection & Pluggable Architecture Foundation ✅ COMPLETE

**Status:** COMPLETE (2025-11-15)

**Expanded Goal:**

Conduct evidence-based comparison between BELLE-2 and WhisperX transcription models for Chinese/Mandarin audio, establish pluggable architecture supporting multiple models and optimizers, and validate both models in production-ready isolated environments.

**Deliverable:** ✅ Both BELLE-2 and WhisperX validated, pluggable optimizer architecture established, A/B comparison data collected, foundation ready for multi-model framework (Epic 4)

**Key Findings:**
- BELLE-2 successfully eliminates gibberish loops (Story 3.1)
- WhisperX functional in isolated environment despite PyTorch conflicts (Story 3.2b)
- Both models demonstrate value in different scenarios (Story 3.2c)
- Pluggable architecture (OptimizerFactory, TranscriptionService) proven effective

---

**Story 3.1: BELLE-2 Integration** ✅ COMPLETE

As a user transcribing Mandarin Chinese audio,
I want the system to automatically use the BELLE-2 model optimized for Chinese language,
So that I receive significantly more accurate transcriptions with fewer repetitive errors and gibberish loops.

**Acceptance Criteria:**
1. `belle2_service.py` implements `TranscriptionService` interface with Chinese-optimized decoder settings
2. BELLE-2 model downloads from HuggingFace on first use, subsequent loads from cache in <5 seconds
3. Transcription output format matches existing WhisperX format (segments with start, end, text)
4. Timestamp alignment stability verified via click-to-timestamp navigation tests
5. Unit tests mock BELLE-2 model to avoid GPU dependency during CI
6. Integration test transcribes 5-minute Mandarin audio and verifies CER improvement
7. Memory footprint validated: ~6GB VRAM usage
8. Fallback mechanism tested: BELLE-2 load failure defaults to WhisperX with warning

**Prerequisites:** Story 2.7 (all MVP functionality complete)

---

**Story 3.2a: Pluggable Optimizer Architecture Design** ✅ COMPLETE

As a system architect,
I want a pluggable timestamp optimization interface,
So that multiple optimizer implementations can coexist and be selected via configuration without code changes.

**Acceptance Criteria:**
1. `app/ai_services/optimization/base.py` defines `TimestampOptimizer` abstract interface with `optimize()` and `is_available()` methods
2. `OptimizationResult` dataclass standardizes optimizer output (segments, metrics, optimizer_name)
3. `app/ai_services/optimization/factory.py` implements `OptimizerFactory.create(engine)` with three modes: "whisperx", "heuristic", "auto"
4. `OPTIMIZER_ENGINE` configuration added to `app/config.py` with default "auto"
5. "auto" mode: Prefers WhisperXOptimizer if available, falls back to HeuristicOptimizer with logging
6. Factory pattern unit tests verify mode selection and fallback logic
7. Documentation updated: architecture.md §704-708 reflects pluggable design
8. Zero disruption to Story 3.1 BELLE-2 integration (optimization layer is post-transcription)

**Prerequisites:** Story 3.1 (BELLE-2 foundation)

---

**Story 3.2b: WhisperX Integration Validation Experiment** ✅ COMPLETE

As a developer,
I want to validate WhisperX wav2vec2 forced alignment integration feasibility,
So that we can make an informed Phase Gate decision on using mature solutions vs. self-developed optimizers.

**Acceptance Criteria:**
1. Isolated test environment (`.venv-test`) created with dependency resolution attempts
2. Dependency installation validated: `pyannote.audio==3.1.1` + `torch==2.0.1/2.1.0` + BELLE-2 compatibility
3. `app/ai_services/optimization/whisperx_optimizer.py` implements `TimestampOptimizer` interface
4. `WhisperXOptimizer.is_available()` returns True only if dependencies successfully installed
5. Performance benchmarking: 10 test files, optimization overhead <25% of transcription time
6. Quality A/B testing: CER/WER ≤ baseline, segment length improvement ≥10%
7. BELLE-2 compatibility validated: No regressions in transcription accuracy
8. **Phase Gate Decision Report** generated with GO/NO-GO recommendation
9. IF GO: Integrate WhisperXOptimizer into production pipeline
10. IF NO-GO: Document failure reasons, proceed with Story 3.3 (HeuristicOptimizer)

**Prerequisites:** Story 3.2a (pluggable architecture foundation)

**Note:** This is a validation experiment with conditional outcomes. Stories 3.3-3.5 activate only if Phase Gate decision is NO-GO.

---

**Story 3.2c: BELLE-2 vs WhisperX Model Comparison** ✅ COMPLETE

As a product team,
I want comprehensive empirical comparison between BELLE-2 and WhisperX for Chinese transcription,
So that we can make evidence-based decision on which model to use in production.

**Acceptance Criteria:**
1. Isolated WhisperX environment created (`.venv-whisperx`) with PyTorch 2.6+/CUDA 12.x
2. Test audio corpus prepared (30-60 min Chinese audio across diverse scenarios)
3. A/B testing scripts implemented for 5 comparison metrics (accuracy, segments, gibberish, performance, memory)
4. Comprehensive benchmark executed on both BELLE-2 and WhisperX
5. Phase Gate Decision Report completed with side-by-side metric comparison
6. Epic 3 path forward defined based on A/B test results

**Prerequisites:** Story 3.2b (WhisperX dependency validation complete)

**Status:** COMPLETE - Both models validated, multi-model framework approach selected (Epic 4)

---

**~~Story 3.3: Heuristic Optimizer - VAD Preprocessing~~** ❌ CANCELLED

As a user transcribing audio with background noise or silence,
I want the system to filter out non-speech segments and optimize decoder parameters,
So that transcription segments are more focused and accurately timed.

**Acceptance Criteria:**
1. `app/ai_services/optimization/heuristic_optimizer.py` implements `TimestampOptimizer` interface with VAD preprocessing
2. WebRTC VAD integrated with configurable aggressiveness (0-3)
3. VAD filtering removes silence segments >1s duration, generates statistics (original/filtered duration, silence %)
4. BELLE-2 decoder parameters configurable via environment variables (beam size, temperature)
5. A/B testing framework saves pre-optimization baseline (`segments_baseline.json`) for comparison
6. VAD processing completes in <5 minutes for 1-hour audio
7. Unit tests mock audio files, verify VAD filtering logic
8. Integration test on noisy audio validates silence removal effectiveness

**Prerequisites:** Story 3.2b (Phase Gate decision = NO-GO for WhisperX)

**Note:** This story activates only if Story 3.2b Phase Gate decides against WhisperX. Part of HeuristicOptimizer implementation.

**Cancellation Rationale:**
Superseded by Epic 4 multi-model framework approach. Original Story 3.3-3.5 designed for single-model (BELLE-2) optimization. Epic 3 A/B testing (Story 3.2c) revealed both models have production value, leading to architectural evolution toward model-agnostic enhancement components rather than BELLE-2-specific optimization.

**Status:** Cancelled (2025-11-15)
**Moved to:** Epic 4.2 (model-agnostic VAD component)

---

**~~Story 3.4: Heuristic Optimizer - Token-Level Timestamps & Energy-Based Refinement~~** ❌ CANCELLED

As a user navigating transcriptions via click-to-timestamp,
I want segment boundaries refined at natural speech breaks,
So that playback jumps feel smooth and aligned with actual speech patterns.

**Acceptance Criteria:**
1. HeuristicOptimizer extends with timestamp refinement capability
2. Token-level timestamps extracted from BELLE-2 decoder outputs
3. Energy-based refinement analyzes audio waveform using librosa, identifies low-energy boundaries
4. Boundary refinement searches ±200ms for optimal split point (minimum energy)
5. Timestamp alignment maintains <200ms accuracy vs. original BELLE-2 outputs
6. Processing completes in <5 minutes for 500 segments
7. Unit tests mock decoder outputs and waveforms
8. Integration test validates click-to-timestamp functionality after refinement

**Prerequisites:** Story 3.3 (HeuristicOptimizer VAD foundation)

**Note:** This story activates only if Story 3.2b Phase Gate decides against WhisperX. Part of HeuristicOptimizer implementation.

**Cancellation Rationale:** Same as Story 3.3

**Status:** Cancelled (2025-11-15)
**Moved to:** Epic 4.3 (model-agnostic timestamp refinement component)

---

**~~Story 3.5: Heuristic Optimizer - Intelligent Segment Splitting for Subtitle Standards~~** ❌ CANCELLED

As a user editing Chinese subtitles,
I want long segments automatically split into subtitle-standard lengths,
So that each subtitle is readable and conforms to industry conventions.

**Acceptance Criteria:**
1. HeuristicOptimizer extends with segment splitting capability
2. Segments >7 seconds split at natural boundaries (punctuation, pauses)
3. Chinese text length estimation implemented (character count × 0.4s)
4. Splitting respects word/sentence boundaries from token timestamps
5. Short segments <1s merged when safe (no interruption of natural flow)
6. 95% of output segments meet 1-7s, <200 char constraints
7. Processing completes in <3 minutes for 500 segments
8. Unit tests cover splitting/merging logic with synthetic segments
9. Integration test on real Chinese audio validates constraint compliance

**Prerequisites:** Story 3.4 (HeuristicOptimizer timestamp refinement)

**Note:** This story activates only if Story 3.2b Phase Gate decides against WhisperX. Part of HeuristicOptimizer implementation.

**Cancellation Rationale:** Same as Story 3.3

**Status:** Cancelled (2025-11-15)
**Moved to:** Epic 4.4 (model-agnostic segment splitting component)

---

**~~Story 3.6: Quality Validation Framework & Optimization Measurement~~** → MOVED TO EPIC 4

As a system maintainer,
I want automated quality validation measuring segment length statistics and transcription accuracy,
So that I can objectively measure optimization improvements and prevent quality regressions.

**Acceptance Criteria:**
1. `quality_validator.py` calculates CER/WER using jiwer library
2. Segment length statistics calculated (mean, median, P95, % meeting constraints)
3. Baseline comparison implemented (CER delta, length improvement %)
4. Regression testing framework compares against stored baseline transcripts
5. Quality metrics stored in `quality_metrics.json`
6. CLI tool provided for manual validation and baseline generation
7. Unit tests verify metric calculations with known inputs
8. Integration test validates Story 3.1 baseline vs. optimized outputs show ≥20% length improvement

**Prerequisites:** Story 3.2b (WhisperX GO) OR Story 3.5 (HeuristicOptimizer complete)

**Note:** This story is required regardless of Phase Gate decision. Works with both WhisperXOptimizer and HeuristicOptimizer.

**Status:** Moved to Epic 4.6
**Rationale:** Quality validation framework needed for multi-model comparison in Epic 4, not single-model optimization

---

**Epic 3 Retrospective:**

Epic 3 delivered exceptional value by discovering that **both** models warrant production support rather than forcing a single-model choice. This insight directly informed the architectural evolution toward a general-purpose multi-model framework (Epic 4). The pluggable architecture foundation (Stories 3.2a) enables Epic 4 implementation without rework.

**Next Epic:** Epic 4 - Multi-Model Transcription Framework & Composable Enhancements

---

## Epic 4: Multi-Model Transcription Framework & Composable Enhancements

**Status:** 📋 PLANNED (Post-MVP)

**Expanded Goal:**

Build production multi-model architecture where multiple transcription engines (BELLE-2, WhisperX, and future models) can coexist with model-agnostic enhancement components (VAD preprocessing, timestamp refinement, segment splitting, speaker identification). Enable runtime model selection and component composition, allowing users to mix-and-match transcription engines and enhancements based on specific content needs.

**Deliverable:** Production-ready multi-model framework with composable enhancement pipeline supporting 2+ transcription models and 3+ enhancement components

**Key Capabilities:**
- Runtime transcription model selection (BELLE-2, WhisperX, configurable default)
- Model-agnostic enhancement components (work with any transcription model)
- Environment management strategy for PyTorch dependency conflicts
- Component composition framework (mix-and-match VAD, refinement, splitting)
- Multi-model quality validation and regression testing

**Strategic Context:**

Epic 3 validated that both BELLE-2 and WhisperX offer distinct value:
- **BELLE-2:** Eliminates gibberish loops, optimized for Mandarin Chinese
- **WhisperX:** Rich feature set, built-in forced alignment, broader language support

Rather than forcing a single-model choice for production, Epic 4 operationalizes the pluggable architecture foundation (Story 3.2a) to support both models with shared enhancement components.

---

**Story 4.1: Multi-Model Production Architecture Design** 📋 PLANNED

As a system architect,
I want a production deployment strategy supporting multiple transcription models with isolated environments,
So that BELLE-2 and WhisperX can coexist without PyTorch dependency conflicts.

**Acceptance Criteria:**
1. Architecture decision record (ADR) documents multi-environment production strategy
2. Docker Compose configuration supports model-specific containers (belle2-worker, whisperx-worker)
3. Celery task routing directs jobs to appropriate worker based on model selection
4. Environment isolation prevents PyTorch version conflicts (CUDA 11.8 for BELLE-2, CUDA 12.x for WhisperX)
5. Model selection configuration via environment variables or runtime API parameters
6. Documentation updated: deployment guide, environment requirements, model selection logic

**Prerequisites:** Epic 3 complete (both models validated)

---

**Story 4.1b: Frontend Model Selection UI** 📋 PLANNED

As a user,
I want to select which transcription model to use before uploading my file,
So that I can choose between BELLE-2 and WhisperX based on my specific needs.

**Acceptance Criteria:**
1. Upload view displays model selection control (radio buttons or dropdown)
2. Model options: "BELLE-2 (Mandarin-optimized)" and "WhisperX (Multi-language)"
3. Default selection: BELLE-2 (configurable via environment variable)
4. Selected model stored in component state (Pinia store)
5. Upload API call includes `model` parameter based on user selection
6. Model selection persists in localStorage for user convenience
7. Tooltip/help text explains key differences between models
8. Responsive design: model selection works on mobile/tablet
9. Backend validates model parameter and routes to appropriate worker
10. Integration test: Upload with each model, verify correct worker processes job

**Prerequisites:** Story 4.1 (multi-model backend architecture)

---

**Story 4.2: Model-Agnostic VAD Preprocessing & Enhanced Metadata Schema** 📋 PLANNED

As a user transcribing audio with background noise or silence,
I want the system to filter out non-speech segments with high-quality deep-learning VAD and capture rich metadata,
So that transcription segments are more focused, accurately timed, and processing is fully transparent.

**Acceptance Criteria:**

**Task 1: Enhanced Data Schema (Technical Enabler)**
1. `backend/app/ai_services/schema.py` module created with hierarchical TypedDict structures:
   - `CharTiming`: Character-level timestamps (char, start, end, score)
   - `WordTiming`: Word-level timestamps (word, start, end, score, language)
   - `BaseSegment`: Minimal required fields (start, end, text)
   - `EnhancedSegment`: Extends BaseSegment with words, chars, confidence, no_speech_prob, avg_logprob, source_model, enhancements_applied, speaker fields
   - `TranscriptionMetadata`: Global metadata (language, duration, model_name, processing_time, vad_enabled, alignment_model)
   - `TranscriptionResult`: Top-level container (segments + metadata + stats)
2. Backward compatibility alias: `TimestampSegment = EnhancedSegment`
3. Service layer supports both simple and enhanced return modes

**Task 2: Multi-Engine VAD Architecture**
4. `VoiceActivityDetector` class implements model-agnostic VAD interface
5. Silero VAD extracted from WhisperX as primary engine (torch.hub based)
6. WebRTC VAD included as fallback engine (lightweight alternative)
7. Multi-engine support with auto-selection: Silero (preferred) → WebRTC (fallback)
8. VAD filters segments removing silence >1s duration
9. Disable WhisperX built-in VAD (vad_filter=False) to prevent duplicate processing
10. Compatible with both BELLE-2 and WhisperX output formats

**Task 3: Configuration & Integration**
11. Processing completes <5 min for 1-hour audio
12. Unit tests verify filtering logic, integration tests validate with real audio
13. Configuration expanded:
    - `VAD_ENGINE`: "auto" | "silero" | "webrtc"
    - `VAD_SILERO_THRESHOLD`: 0.5 (0.0-1.0)
    - `VAD_SILERO_MIN_SILENCE_MS`: 700
    - `VAD_WEBRTC_AGGRESSIVENESS`: 2 (0-3)

**Implementation Files:**
```
backend/app/ai_services/
├── schema.py                    # NEW: Enhanced metadata schema
├── enhancement/
│   ├── vad_manager.py          # Unified VAD interface
│   └── vad_engines/
│       ├── base_vad.py         # Abstract interface
│       ├── silero_vad.py       # Extracted from WhisperX (NEW)
│       └── webrtc_vad.py       # Existing fallback
```

**Prerequisites:** Story 4.1b (frontend model selection)

---

**Story 4.3: Model-Agnostic Timestamp Refinement Component** 📋 PLANNED

As a user navigating transcriptions via click-to-timestamp,
I want segment boundaries refined at natural speech breaks with character/word-level timing,
So that playback jumps feel smooth, aligned with actual speech patterns, and Chinese editing is precise.

**Acceptance Criteria:**
1. `TimestampRefiner` class implements refinement interface
2. **Populates CharTiming array for Chinese segments (character-level timestamps)**
3. **Populates WordTiming array with confidence scores from alignment model**
4. Energy-based boundary detection using librosa for segment splitting
5. Boundary refinement searches ±200ms for optimal split point
6. Maintains <200ms accuracy vs. original timestamps
7. **Records alignment_model in EnhancedSegment metadata**
8. **Appends "timestamp_refine" to enhancements_applied tracking**
9. Processing completes <5 min for 500 segments
10. Unit tests verify refinement logic and metadata population
11. Integration tests validate click-to-timestamp accuracy and char/word timing arrays

**Prerequisites:** Story 4.2 (VAD component + metadata schema)

---

**Story 4.4: Model-Agnostic Segment Splitting Component** 📋 PLANNED

As a user editing Chinese subtitles,
I want long segments automatically split with preserved timing metadata,
So that each subtitle is readable, conforms to industry conventions, and maintains precise character/word timing.

**Acceptance Criteria:**
1. `SegmentSplitter` class implements splitting interface
2. Segments >7s split at natural boundaries (punctuation, pauses)
3. **Uses CharTiming/WordTiming arrays for precise split point selection**
4. Chinese text length estimation (character count × 0.4s)
5. Short segments <1s merged when safe
6. **Preserves char/word timing arrays when splitting segments**
7. **Appends "segment_split" to enhancements_applied tracking**
8. 95% of output segments meet 1-7s, <200 char constraints
9. Processing completes <3 min for 500 segments
10. Unit tests cover splitting/merging logic and metadata preservation
11. Integration test validates constraint compliance and timing array integrity

**Prerequisites:** Story 4.3 (refinement component pattern established)

---

**Story 4.5: Enhancement Pipeline Composition Framework** 📋 PLANNED

As a system,
I want a composable pipeline where enhancement components track processing metadata,
So that different combinations can be applied and their effectiveness measured transparently.

**Acceptance Criteria:**
1. `EnhancementPipeline` class supports component composition
2. Components registered via configuration (VAD, refinement, splitting)
3. Pipeline executes components in declared order
4. Each component receives previous component's output
5. **Pipeline aggregates enhancements_applied from all components**
6. **TranscriptionResult metadata tracks complete pipeline configuration**
7. Pipeline supports component bypass via configuration flags
8. Error handling: component failure doesn't break entire pipeline (graceful degradation)
9. **Logging records pipeline execution with component timing metrics**
10. Unit tests verify composition logic, execution order, and metadata aggregation
11. Integration test validates multi-component pipeline with full metadata tracking

**Prerequisites:** Stories 4.2, 4.3, 4.4 (all components implemented)

---

**Story 4.6: Multi-Model Quality Validation Framework** ✅ COMPLETE

As a system maintainer,
I want automated quality validation leveraging enhanced metadata across models,
So that I can objectively compare configurations and measure pipeline effectiveness comprehensively.

**Acceptance Criteria:**
1. `QualityValidator` calculates CER/WER using jiwer library
2. Segment length statistics (mean, median, P95, % meeting constraints)
3. **Character-level timing accuracy metrics (for Chinese segments)**
4. **Confidence score analysis (avg_confidence, low_confidence_segments)**
5. **Enhancement pipeline effectiveness metrics (per-component impact)**
6. Baseline comparison (CER delta, length improvement %, confidence trends)
7. **Model comparison reports using TranscriptionMetadata (BELLE-2 vs WhisperX)**
8. Regression testing compares against stored baselines
9. Quality metrics stored in quality_metrics.json with enhanced metadata
10. CLI tool for manual validation and baseline generation
11. Unit tests verify metric calculations including new metadata fields
12. Integration test validates optimization improvements ≥20% with metadata tracking

**Prerequisites:** Story 4.5 (pipeline framework complete)

**Status:** COMPLETE (2025-11-20)

---

**Epic 4 Estimated Timeline:** 10-15 days (post-MVP)

**Epic 4 Dependencies:**
- Epic 3 complete ✅
- MVP shipped with single model
- Production infrastructure available for multi-worker deployment

---

## Story Guidelines Reference

**Story Format:**

```
**Story [EPIC.N]: [Story Title]**

As a [user type],
I want [goal/desire],
So that [benefit/value].

**Acceptance Criteria:**
1. [Specific testable criterion]
2. [Another specific criterion]
3. [etc.]

**Prerequisites:** [Dependencies on previous stories, if any]
```

**Story Requirements:**

- **Vertical slices** - Complete, testable functionality delivery
- **Sequential ordering** - Logical progression within epic
- **No forward dependencies** - Only depend on previous work
- **AI-agent sized** - Completable in 2-4 hour focused session
- **Value-focused** - Integrate technical enablers into value-delivering stories

---

**For implementation:** Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown.
