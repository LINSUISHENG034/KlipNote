# Story 1.4: Status and Result API Endpoints

Status: done

## Story

As a user,
I want to check transcription progress and retrieve results,
So that I know when my transcription is ready and can access it.

## Acceptance Criteria

1. GET /status/{job_id} endpoint returns {status: "pending"|"processing"|"completed"|"failed", progress: 0-100}
2. GET /result/{job_id} endpoint returns transcription JSON with subtitle array
3. Status endpoint returns 404 for non-existent job_id
4. Result endpoint returns 404 if job not completed
5. Result endpoint returns error details if job failed
6. Both endpoints documented in FastAPI auto-docs

## Tasks / Subtasks

- [x] Task 1: Implement GET /status/{job_id} endpoint (AC: #1, #3)
  - [x] Define route in backend/app/main.py
  - [x] Query Redis for key pattern: job:{job_id}:status
  - [x] Return StatusResponse model with status, progress, message, timestamps
  - [x] Handle missing job_id with 404 HTTPException
  - [x] Add endpoint to FastAPI auto-docs

- [x] Task 2: Implement GET /result/{job_id} endpoint (AC: #2, #4, #5)
  - [x] Define route in backend/app/main.py
  - [x] Query Redis for key pattern: job:{job_id}:result
  - [x] Return TranscriptionResult model with segments array
  - [x] Handle missing job_id with 404 HTTPException
  - [x] Handle incomplete job (status not "completed") with 404 and message
  - [x] Handle failed job: return error details from status message
  - [x] Add endpoint to FastAPI auto-docs

- [x] Task 3: Add Redis helper methods to RedisService (AC: #1, #2)
  - [x] Verify get_status() method exists in backend/app/services/redis_service.py
  - [x] Verify get_result() method exists in backend/app/services/redis_service.py
  - [x] Ensure methods return None if key doesn't exist (for 404 handling)
  - [x] UUID validation already implemented from Story 1.3

- [x] Task 4: Write comprehensive tests (AC: #1-6)
  - [x] Create backend/tests/test_api_status_result.py
  - [x] Test GET /status/{job_id} with pending job → returns StatusResponse
  - [x] Test GET /status/{job_id} with processing job → returns progress 40%
  - [x] Test GET /status/{job_id} with completed job → returns progress 100%
  - [x] Test GET /status/{job_id} with failed job → returns failed status with error message
  - [x] Test GET /status/{job_id} with non-existent job_id → 404
  - [x] Test GET /result/{job_id} with completed job → returns TranscriptionResult with segments
  - [x] Test GET /result/{job_id} with non-existent job_id → 404
  - [x] Test GET /result/{job_id} with incomplete job (pending/processing) → 404
  - [x] Test GET /result/{job_id} with failed job → returns error details
  - [x] Use fakeredis for Redis mocking
  - [x] Achieve 70%+ code coverage on new endpoint code

- [x] Task 5: Verify FastAPI auto-docs integration (AC: #6)
  - [x] Start backend server: uvicorn app.main:app --reload
  - [x] Navigate to http://localhost:8000/docs
  - [x] Verify GET /status/{job_id} appears with StatusResponse schema
  - [x] Verify GET /result/{job_id} appears with TranscriptionResult schema
  - [x] Test endpoints interactively in Swagger UI
  - [x] Verify response examples show correct data types

- [x] Task 6: Integration testing with Celery workflow (AC: #1-5)
  - [x] Update backend/tests/test_upload_endpoint.py
  - [x] Add integration test: Upload → Wait for completion → Call /status → Verify "completed"
  - [x] Add integration test: Upload → Wait for completion → Call /result → Verify segments present
  - [x] Add integration test: Upload → Call /status immediately → Verify "pending" status
  - [x] Mock transcribe_audio task to complete quickly (avoid long GPU wait)

## Dev Notes

### Learnings from Previous Story

**From Story 1-3-celery-task-queue-and-whisperx-integration (Status: done)**

- **RedisService Available**: `backend/app/services/redis_service.py` provides get_status() and get_result() methods - use these directly
- **UUID Validation Implemented**: UUID v4 validation added in Story 1.3 to RedisService methods - reuse for path traversal prevention
- **Redis Key Patterns**: job:{job_id}:status and job:{job_id}:result already established and tested
- **StatusResponse Model**: Defined in `backend/app/models.py` with Literal type for status enum - ready to use
- **TranscriptionResult Model**: Defined in `backend/app/models.py` with segments array - ready to use
- **Testing Infrastructure**: fakeredis==2.21.1 installed, pytest fixtures configured, 79% coverage achieved
- **Error Handling Pattern**: HTTPException with status codes and clear messages established in upload endpoint

**Key Files to Reuse:**
- `backend/app/services/redis_service.py` - Use get_status() and get_result() methods
- `backend/app/models.py` - StatusResponse, TranscriptionResult, TranscriptionSegment models
- `backend/app/main.py` - Add new routes here following existing patterns
- `backend/tests/conftest.py` - Use existing fixtures (test_client, fakeredis setup)

**Integration Points:**
- Story 1.3 stores status in Redis via transcription task - these endpoints read that data
- Story 1.2 generates job_id via upload endpoint - these endpoints use job_id as path parameter
- Story 1.6 (frontend) will poll GET /status endpoint every 3 seconds
- Story 1.7 (frontend) will fetch results via GET /result endpoint

[Source: docs/stories/1-3-celery-task-queue-and-whisperx-integration.md#Dev-Agent-Record]

### Architectural Patterns and Constraints

**API Endpoint Pattern (from architecture.md):**
- **Route Definition:** Define in backend/app/main.py (all endpoints in one file)
- **Response Models:** Use Pydantic models from backend/app/models.py
- **Error Handling:** HTTPException with standard status codes (404, 500)
- **Error Format:** `{"detail": "Human-readable error message"}`
- **UUID Validation:** RedisService already validates job_id format (from Story 1.3)

**Redis Query Pattern:**
```python
from app.services.redis_service import RedisService

redis_service = RedisService()

# Query status
status_data = redis_service.get_status(job_id)
if status_data is None:
    raise HTTPException(status_code=404, detail="Job not found")

# Query result
result_data = redis_service.get_result(job_id)
if result_data is None:
    raise HTTPException(status_code=404, detail="Transcription not available")
```

**Status Endpoint Logic:**
```python
@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    """
    Retrieve current status and progress of transcription job

    Progress Stages (from Story 1.3):
    - 10%: "Task queued..."
    - 20%: "Loading AI model..."
    - 40%: "Transcribing audio..." (longest stage)
    - 80%: "Aligning timestamps..."
    - 100%: "Processing complete!"

    Returns:
    - status: pending | processing | completed | failed
    - progress: 0-100 integer percentage
    - message: User-friendly stage description
    - timestamps: ISO 8601 UTC strings

    Errors:
    - 404: Job ID not found in Redis
    """
    redis_service = RedisService()
    status_data = redis_service.get_status(job_id)

    if status_data is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    return StatusResponse(**status_data)
```

**Result Endpoint Logic:**
```python
@app.get("/result/{job_id}", response_model=TranscriptionResult)
async def get_result(job_id: str) -> TranscriptionResult:
    """
    Retrieve completed transcription result

    Returns:
    - segments: Array of {start, end, text} objects
      - start/end: Float seconds with decimal precision
      - text: Transcribed subtitle text

    Errors:
    - 404: Job ID not found or job not completed
    - Returns error details if job status is 'failed'
    """
    redis_service = RedisService()

    # Check status first to provide better error messages
    status_data = redis_service.get_status(job_id)
    if status_data is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    # Handle failed jobs
    if status_data.get("status") == "failed":
        raise HTTPException(
            status_code=404,
            detail=f"Transcription failed: {status_data.get('message', 'Unknown error')}"
        )

    # Handle incomplete jobs
    if status_data.get("status") != "completed":
        raise HTTPException(
            status_code=404,
            detail=f"Transcription not yet complete. Current status: {status_data.get('status')}"
        )

    # Retrieve result
    result_data = redis_service.get_result(job_id)
    if result_data is None:
        raise HTTPException(
            status_code=404,
            detail="Transcription result not found. Please try again later."
        )

    return TranscriptionResult(**result_data)
```

**FastAPI Auto-Docs Integration:**
- FastAPI automatically generates /docs (Swagger UI) and /redoc from:
  - Route decorators with response_model
  - Pydantic models (StatusResponse, TranscriptionResult)
  - Docstrings on route functions
- No additional configuration needed beyond Pydantic models

[Source: docs/tech-spec-epic-1.md#APIs-and-Interfaces]

### Source Tree Components to Touch

**Existing Files to Modify:**
```
backend/app/
├── main.py                       # Add GET /status and GET /result routes
```

**Existing Files to Use (No Modification):**
```
backend/app/
├── models.py                     # StatusResponse, TranscriptionResult already defined
├── services/
│   └── redis_service.py          # get_status(), get_result() already implemented
```

**New Test Files to Create:**
```
backend/tests/
└── test_api_status_result.py     # Comprehensive tests for both endpoints
```

**Existing Test Files to Extend:**
```
backend/tests/
└── test_upload_endpoint.py       # Add integration tests for full workflow
```

**Files NOT to Touch:**
- `backend/app/tasks/transcription.py` - Task logic already writes status/result to Redis (Story 1.3)
- `backend/app/services/file_handler.py` - No file operations needed for these endpoints
- Frontend files - Frontend integration in Stories 1.6 and 1.7

### Testing Standards Summary

**Test Coverage Requirements (from Testing Strategy):**
- API endpoint tests: 70%+ code coverage
- All error scenarios must have explicit tests
- Use fakeredis for Redis mocking (already installed in Story 1.3)

**Test Organization:**
- Unit tests: `backend/tests/test_api_status_result.py` (endpoint logic in isolation)
- Integration tests: `backend/tests/test_upload_endpoint.py` (full upload → transcribe → status/result workflow)
- Use pytest fixtures from `conftest.py`: test_client, fakeredis setup

**Test Scenarios to Cover:**

**1. Status Endpoint Happy Paths:**
- Pending job (status: "pending", progress: 10)
- Processing job (status: "processing", progress: 40)
- Completed job (status: "completed", progress: 100)
- Failed job (status: "failed", message with error details)

**2. Status Endpoint Error Cases:**
- Non-existent job_id → 404 with "Job not found" message
- Invalid UUID format → 404 (handled by RedisService validation)

**3. Result Endpoint Happy Path:**
- Completed job with segments → returns TranscriptionResult with array of segments

**4. Result Endpoint Error Cases:**
- Non-existent job_id → 404 with "Job not found"
- Pending job → 404 with "not yet complete" message
- Processing job → 404 with "not yet complete" message
- Failed job → 404 with error details from status message
- Completed job but result missing (edge case) → 404 with "result not found"

**5. Integration Testing:**
- Full workflow: POST /upload → Poll GET /status → GET /result
- Verify status transitions: pending → processing → completed
- Verify segments format matches TranscriptionSegment model

**Mock Strategy:**
- **Redis:** Use fakeredis library for in-memory Redis (already set up in Story 1.3)
- **Celery Task:** Mock transcribe_audio.delay() to avoid GPU dependency
- **Test Data:** Use fixture JSON for status and result data

**Test Execution:**
```bash
cd backend
source .venv/Scripts/activate  # Activate uv environment
pytest tests/test_api_status_result.py -v
pytest tests/test_upload_endpoint.py -v --cov=app --cov-report=html
```

[Source: docs/tech-spec-epic-1.md#Test-Strategy-Summary]

### Project Structure Notes

**Alignment with Unified Project Structure:**
- Follows API endpoint pattern: RESTful routes in main.py
- Follows service layer pattern: RedisService for data access
- Follows Pydantic model pattern: StatusResponse, TranscriptionResult for type safety
- Follows error handling pattern: HTTPException with status codes and clear messages
- No conflicts detected - extends architecture established in Stories 1.1-1.3

**API Endpoint Alignment:**
- GET /status/{job_id} - RESTful resource-based URL
- GET /result/{job_id} - RESTful resource-based URL
- Both use FastAPI auto-docs (no manual documentation needed)
- Both return JSON responses following established data models

**Testing Alignment:**
- Follows pytest structure from Story 1.1
- Uses fakeredis mocking pattern from Story 1.3
- Maintains 70%+ coverage target

### References

- [Source: docs/epics.md#Story-1.4] - User story statement and acceptance criteria
- [Source: docs/tech-spec-epic-1.md#APIs-and-Interfaces] - GET /status and GET /result endpoint specifications
- [Source: docs/tech-spec-epic-1.md#Data-Models-and-Contracts] - StatusResponse, TranscriptionResult Pydantic models
- [Source: docs/tech-spec-epic-1.md#Progress-Tracking-Structure] - Redis key patterns and status schema
- [Source: docs/architecture.md#API-Endpoint-Patterns] - RESTful conventions, HTTP status codes, error format
- [Source: docs/architecture.md#Error-Handling-Strategy] - HTTPException usage, user-friendly messages
- [Source: docs/architecture.md#Testing-Strategy] - pytest framework, coverage targets, mock strategies
- [Source: docs/stories/1-3-celery-task-queue-and-whisperx-integration.md#Dev-Notes] - RedisService methods, Redis key patterns, UUID validation

## Dev Agent Record

### Context Reference

- docs/stories/1-4-status-and-result-api-endpoints.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

**Implementation Approach:**
1. Added GET /status/{job_id} endpoint using existing RedisService.get_status() method
2. Added GET /result/{job_id} endpoint with multi-layered error handling (missing job, incomplete job, failed job)
3. Implemented try-catch blocks to handle ValueError from UUID validation in RedisService
4. Created comprehensive test suite (14 unit tests + 5 integration tests = 19 tests total)
5. Added fake_redis_client fixture to conftest.py for shared test infrastructure
6. All tests pass with 79% coverage on main.py (exceeds 70% requirement)

**Technical Decisions:**
- Used response_model parameter in route decorators to auto-generate OpenAPI docs (AC#6)
- Implemented defensive error handling for invalid UUIDs (caught by RedisService validation)
- Result endpoint checks status first to provide contextual error messages (incomplete vs failed vs missing)
- Integration tests simulate full workflow with fakeredis to avoid external dependencies

### Completion Notes List

**Story 1.4 Implementation Summary:**

✅ **Acceptance Criteria Met:**
1. GET /status/{job_id} returns status/progress (tested: pending, processing, completed, failed)
2. GET /result/{job_id} returns transcription segments array (tested with sample data)
3. Status endpoint returns 404 for non-existent job_id (tested with invalid UUID and missing job)
4. Result endpoint returns 404 if job not completed (tested: pending, processing states)
5. Result endpoint returns error details if job failed (tested with error message extraction)
6. Both endpoints documented in FastAPI auto-docs (automatic via response_model decorators)

✅ **Implementation Quality:**
- **Code Coverage:** 79% on main.py, 82% overall (exceeds 70% target)
- **Test Coverage:** 19 tests (14 unit + 5 integration), all passing
- **Error Handling:** Comprehensive handling of all error scenarios (404 for missing/incomplete/failed jobs, invalid UUIDs)
- **Integration:** Full workflow tested (Upload → Status → Result)

✅ **Key Files Modified:**
- backend/app/main.py: Added 2 new GET endpoints (121 lines added)
- backend/tests/test_api_status_result.py: New test file with 14 comprehensive tests
- backend/tests/test_upload_endpoint.py: Added 5 integration tests for full workflow
- backend/tests/conftest.py: Added fake_redis_client fixture for shared test infrastructure

**Implementation Notes:**
- RedisService methods (get_status, get_result) were already implemented in Story 1.3 - reused successfully
- UUID validation in RedisService required try-catch in endpoints to return proper 404 instead of 500
- FastAPI automatically generates OpenAPI docs from Pydantic models and response_model decorators
- Integration tests use fakeredis for fast, reliable testing without external Redis dependency

**Next Steps for Frontend (Stories 1.5-1.7):**
- Story 1.6: Frontend will poll GET /status every 3 seconds to show progress
- Story 1.7: Frontend will fetch GET /result to display transcription segments

### File List

- backend/app/main.py
- backend/tests/test_api_status_result.py (new)
- backend/tests/test_upload_endpoint.py
- backend/tests/conftest.py

### Completion Notes
**Completed:** 2025-11-05
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

