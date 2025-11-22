# Technical Backlog

## Overview
This document tracks technical debt, improvements, and follow-up items identified during development and code reviews.

## Status Legend
- **Open**: Not yet started
- **In Progress**: Currently being worked on
- **Done**: Completed
- **Won't Fix**: Decided not to pursue

---

## Items

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
|------|-------|------|------|----------|-------|--------|-------|
| 2025-11-17 | 4.5 | 4 | TechDebt | Low | TBD | Open | Register pytest custom marks (integration, slow) in pytest.ini to eliminate warnings. Currently shows 13 warnings during test runs. |
| 2025-11-17 | 4.5 | 4 | Enhancement | Low | TBD | Open | Increase test coverage for segment_splitter.py (currently 38%). Component has comprehensive logic but lacks complete test coverage. |
| 2025-11-17 | 4.5 | 4 | Enhancement | Low | TBD | Open | Add Protocol or ABC base class for enhancement components to improve type safety and catch interface violations at static analysis time. |
| 2025-11-17 | 4.5 | 4 | Enhancement | Low | TBD | Open | Add production telemetry for pipeline metrics tracking. Current implementation collects metrics but doesn't persist them for analysis. |
| 2025-11-17 | 4.5 | 4 | Documentation | Low | TBD | Open | Add architecture diagrams showing enhancement pipeline flow and component interaction patterns. |
| 2026-07-02 | 4.7 | 4 | Bug | High | TBD | Open | Import EnhancementConfigRequest in upload handler so enhancement_config requests return 400 instead of 500; unblock AC1/AC5. |
| 2026-07-02 | 4.7 | 4 | Bug | High | TBD | Open | Fix enhancement pipeline defaults to use defined settings (or add missing ones) so env/default path works when enhancement_config is omitted; restore AC7/AC8. |
| 2026-07-02 | 4.7 | 4 | Testing | Medium | TBD | Open | Align Celery enqueue call and tests (apply_async vs delay) to make /upload tests meaningful and passing. |
| 2026-07-02 | 4.7 | 4 | Enhancement | Medium | TBD | Open | Add EnhancementConfig TypeScript interface and wire to API client types to keep frontend/backed contracts aligned. |
| 2026-07-02 | 4.7 | 4 | Testing | Medium | TBD | Open | Strengthen config priority tests with assertions and settings patching to validate API > env > defaults. |

---

## Completed Items

| Date Closed | Story | Epic | Type | Severity | Description |
|-------------|-------|------|------|----------|-------------|
| 2025-11-17 | 4.5 | 4 | Bug | High | Services (belle2_service.py, whisperx_service.py) were directly calling components instead of using EnhancementPipeline. Refactored to delegate to pipeline for consistency. |
| 2025-11-17 | 4.5 | 4 | Testing | High | Integration tests missing for enhancement pipeline. Created test_enhancement_pipeline_integration.py with 12 comprehensive tests. |
