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
3. Dependencies installed: FastAPI, Celery, Redis, Vue 3, Vite
4. WhisperX integrated as git submodule at `ai_services/whisperx/`
5. Git repository configured with .gitignore for Python and Node
6. Basic README with setup instructions
7. Local development servers can run (backend on port 8000, frontend on port 5173)

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
