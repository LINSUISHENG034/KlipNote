# KlipNote Product Requirements Document (PRD)

**Author:** Link
**Date:** 2025-11-03
**Project Level:** 2
**Target Scale:** Medium project - multiple epics, 10+ stories

---

## Goals and Background Context

### Goals

**Project Goals for KlipNote:**

1. **Enable self-service transcription workflow** - Non-technical users can independently convert meeting recordings to LLM-ready text without technical assistance
2. **Eliminate cost and duration barriers** - Provide unlimited, free transcription for 1-2 hour meetings that paid services restrict
3. **Validate data flywheel foundation** - Collect human-edited transcriptions as training data to enable continuous quality improvement
4. **Prove technical feasibility** - Demonstrate self-hosted GPU architecture reliably handles concurrent transcription jobs for 10-20 users

### Background Context

Finance industry professionals and office workers (particularly in Chinese-speaking markets) regularly record meetings but face a critical workflow bottleneck: converting recordings into text for LLM processing (meeting minutes, action items, analysis). Paid transcription services impose cost barriers ($120-360/year) and duration limits (10-30 min free tiers), while open-source tools like Whisper CLI require terminal expertise that non-technical users lack.

KlipNote solves this by combining state-of-the-art transcription accuracy with a zero-friction web interface accessible from any device. The integrated click-to-timestamp review interface transforms tedious verification into rapid workflow, while every human correction becomes training data for continuous model improvement - establishing a self-improving system that deepens its competitive advantage with usage. Chinese/Mandarin meeting transcription represents the primary use case, requiring specialized optimization for accurate subtitle-length segmentation.

---

## Requirements

### Functional Requirements

**File Upload & Processing**

- **FR001:** System shall accept audio and video file uploads via web interface
- **FR002:** System shall support common media formats including MP3, MP4, WAV, M4A, and other formats supported by FFmpeg
- **FR003:** System shall process uploaded media files using empirically validated transcription model (BELLE-2 or WhisperX selected for MVP based on Epic 3 A/B comparison; both models validated, multi-model support planned for post-MVP Epic 4) with word-level timestamps, automatically detecting and preserving the original audio language
- **FR003b:** System shall optimize Chinese/Mandarin transcription quality as primary use case with segment lengths suitable for subtitle editing workflows (typically 1-7 seconds per segment, maximum ~200 characters)
- **FR004:** System shall queue multiple transcription jobs and process them sequentially using available GPU resources

**Transcription Display & Management**

- **FR005:** System shall display transcription results as a list of time-stamped subtitle segments
- **FR006:** System shall provide real-time progress updates during transcription processing
- **FR007:** System shall return job status and completion percentage via polling mechanism
- **FR008:** System shall handle transcription errors gracefully with clear error messages

**Review & Editing Interface**

- **FR009:** System shall allow users to edit subtitle text inline within the web interface
- **FR010:** System shall synchronize subtitle segments with corresponding audio/video timestamps
- **FR011:** System shall enable click-to-timestamp navigation - clicking any subtitle jumps to exact media position
- **FR012:** System shall provide integrated media player supporting play, pause, and seek controls
- **FR013:** System shall highlight active subtitle segment during media playback

**Export & Delivery**

- **FR014:** System shall export edited transcriptions in SRT (SubRip) subtitle format
- **FR015:** System shall export edited transcriptions in plain TXT format for LLM processing
- **FR016:** System shall capture both original AI-generated and human-edited versions during export

**Data Persistence**

- **FR017:** System shall store uploaded media files on server for playback and future reference
- **FR018:** System shall persist original transcription outputs with timestamps
- **FR019:** System shall store human-edited transcription versions to enable data flywheel analysis
- **FR020:** System shall persist user edits to browser localStorage to prevent data loss during browser refresh or accidental navigation

### Non-Functional Requirements

- **NFR001: Performance** - Transcription processing shall complete at 1-2x real-time speed (1 hour audio = 30-60 min processing). UI shall load in <3 seconds, media playback shall start within 2 seconds, and timestamp seeking shall respond in <1 second.

- **NFR002: Usability** - Non-technical users shall complete the upload → review → export workflow without documentation or technical assistance. System shall provide clear error messages and visual feedback throughout all operations.

- **NFR003: Reliability** - System shall achieve 90%+ transcription completion rate (successful upload → export). Browser-based state shall prevent data loss during normal operation including page refresh and accidental navigation, with clear warnings for potentially destructive actions like leaving during upload.

- **NFR004: Compatibility** - Web interface shall function on desktop, tablet, and mobile browsers including Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+. System shall handle media files up to 2 hours duration (primary constraint for GPU processing). File size limit of 2GB serves as practical upload boundary, though actual constraint is processing duration.

- **NFR005: Transcription Quality** - Subtitle segments shall conform to industry-standard length conventions for subtitle editing workflows. Segments should typically span 1-7 seconds with maximum ~200 characters to ensure usability in review and editing interfaces. Chinese/Mandarin transcription quality is prioritized as the primary use case. Model selection determined through empirical A/B testing in Epic 3 (Stories 3.2b-3.2c) validating both BELLE-2 and WhisperX across comprehensive metrics: CER/WER accuracy, segment length compliance (1-7s / ≤200 chars), gibberish elimination, processing speed, and GPU memory efficiency. MVP ships with [selected model TBD], multi-model framework deferred to post-MVP Epic 4.

---

## User Journeys

### Journey 1: Office Worker Transcribes Meeting for LLM Processing (Happy Path)

**Persona:** Sarah, Finance Analyst - non-technical office worker, recorded a 45-minute client meeting on her phone

**Goal:** Convert meeting recording to text for ChatGPT to generate meeting minutes

**Steps:**

1. **Access KlipNote**
   - Sarah opens Chrome on her laptop and navigates to the KlipNote URL provided by IT
   - Landing page shows simple upload interface with clear instructions

2. **Upload Recording**
   - Sarah clicks "Choose File" button and selects her meeting recording (MP4, 120MB)
   - She clicks "Upload and Transcribe"
   - System confirms upload successful and shows "Transcription in progress..."

3. **Monitor Progress**
   - Progress bar appears showing "Processing: 15% complete"
   - Sarah switches to another tab to check email while waiting
   - After ~30 minutes, she returns and sees "Transcription Complete!"

4. **Review Transcription**
   - Screen displays scrollable list of timestamped subtitle segments
   - Integrated media player at top shows her meeting video
   - Sarah clicks on a subtitle segment around minute 12 where client discussed budget
   - Video instantly jumps to 12:03 timestamp and plays

5. **Edit Errors**
   - Sarah notices AI transcribed "fiscal quarter" as "physical quarter"
   - She clicks the subtitle text and edits it inline
   - She continues scanning, finds a few client names misspelled, corrects them
   - Total editing time: 4 minutes for 45-minute meeting

6. **Export Results**
   - Sarah clicks "Export" button at bottom of page
   - She selects "TXT format" (for LLM use)
   - Browser downloads "meeting-transcript.txt" to her Downloads folder

7. **Use in LLM Workflow**
   - Sarah opens ChatGPT, pastes the transcription text
   - Prompts: "Generate meeting minutes with action items"
   - Receives formatted meeting minutes in 30 seconds

**Outcome:** Sarah transformed 45-minute meeting into actionable minutes in ~35 total minutes (30 min transcription + 4 min editing + 1 min export/LLM), compared to 2+ hours of manual transcription or $12 paid service charge.

**Success Criteria:**
- Zero technical assistance required
- Clear status feedback throughout process
- Click-to-timestamp enabled rapid verification
- Export format worked seamlessly with LLM tool

---

## UX Design Principles

**1. Zero-Friction "Use and Go"**
- No account creation, no login, no session management
- Single-purpose workflow: Upload → Review → Export → Done
- Ephemeral by design - users complete task and leave, no workspace clutter

**2. Self-Service Clarity**
- Every step has clear visual feedback and status indicators
- Error messages guide users to resolution without technical jargon
- Progress is always visible - never leave users guessing

**3. Mobile-First Accessibility**
- Touch-optimized controls for tablet and mobile devices
- Responsive layout adapts to screen sizes from 320px (mobile) to desktop
- Core functionality works on any modern browser without plugins

**4. Instant Feedback & Responsiveness**
- Click-to-timestamp navigation responds in <1 second
- Inline editing with immediate visual confirmation
- Loading states and progress indicators prevent uncertainty

---

## User Interface Design Goals

**Platform & Screens:**
- **Target Platforms:** Web browser (desktop, tablet, mobile)
- **Core Views:**
  - Upload landing page with drag-drop support
  - Progress monitoring screen with status updates
  - Integrated editor/player view (split or stacked layout)
  - Export confirmation dialog

**Key Interaction Patterns:**
- **Subtitle List:** Scrollable, clickable segments with inline text editing
- **Media Player:** Native HTML5 controls with synchronized subtitle highlighting
- **Click-to-Timestamp:** Primary interaction - clicking subtitle seeks media to exact position
- **Export:** Clear action button with format selection (SRT/TXT)

**Design Constraints:**
- **Minimal Dependencies:** Use browser-native components (HTML5 video/audio, standard form controls)
- **No Design System Required:** Clean, functional interface without complex branding
- **Performance First:** Fast load times prioritized over visual polish
- **Browser Compatibility:** Must work on Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

---

## Epic List

**Epic 1: Foundation & Core Transcription Workflow** ✅ COMPLETE
- Establish project infrastructure, API backend, and basic web frontend with end-to-end upload → transcription → display capability
- **Stories:** 8 stories (1.1-1.8)
- **Deliverable:** ✅ Users can upload media files and receive AI transcription results

**Epic 2: Integrated Review & Export Experience** ✅ COMPLETE
- Build the differentiated review interface with click-to-timestamp navigation, inline editing, and export capabilities including data flywheel foundation
- **Stories:** 7 stories (2.1-2.7)
- **Deliverable:** ✅ Complete MVP - users can review, edit, and export transcriptions with data persistence

**Epic 3: Chinese Transcription Model Selection & Pluggable Architecture Foundation** ✅ COMPLETE
- Conduct evidence-based comparison between BELLE-2 and WhisperX, establish pluggable optimizer architecture
- **Stories:** 4 stories (3.1, 3.2a, 3.2b, 3.2c); 3 stories cancelled (3.3-3.5)
- **Deliverable:** ✅ Both models validated, pluggable architecture proven, foundation for multi-model framework

**Epic 4: Multi-Model Transcription Framework & Composable Enhancements** 📋 POST-MVP
- Production multi-model architecture with model-agnostic enhancement components (VAD, timestamp refinement, segment splitting)
- **Estimated Stories:** 7 stories (4.1-4.7)
- **Deliverable:** Multi-model framework supporting 2+ transcription engines with composable enhancement pipeline

**MVP Scope:** Epics 1-3 + Single Model Selection (Story 4.7 decision)
**Post-MVP:** Epic 4 (Multi-Model Framework)

> **Note:** Detailed epic breakdown with full story specifications is available in [epics.md](./epics.md)

---

## Out of Scope

**Phase 2 Enhancements (Deferred to Post-MVP):**
- Server-Sent Events (SSE) for real-time progress streaming (polling sufficient for MVP)
- Composables architecture refactor for code maintainability
- Edit analytics dashboard and quality metrics
- Multi-job management and concurrent transcription UI
- VTT export format support
- Advanced crash recovery and offline mode support

**Advanced Features (Long-term Vision):**
- Automated model fine-tuning pipeline using collected training data
- AI-powered correction suggestions based on edit patterns
- Real-time streaming transcription for live events
- Collaborative editing with multi-user support
- Speaker diarization and automatic speaker labeling
- Translation and multilingual transcription capabilities
- Audio enhancement features (noise reduction, volume normalization)

**Platform Expansions:**
- Mobile native applications (iOS/Android)
- Desktop native applications (Electron-based)
- Cloud-hosted SaaS offering
- Integration with third-party services (Notion, Google Docs, meeting platforms)

**Authentication & Multi-tenancy:**
- User accounts and authentication system
- Multi-tenant architecture with user isolation
- Role-based access control
- Team/organization workspace features

**Scope Clarifications:**
- Video editing capabilities (transcription focus only)
- Advanced subtitle formatting and styling
- Offline mode operation (requires server connection)
- Automated backup and disaster recovery
- Enterprise compliance features (audit trails, certifications)
