# KlipNote API Reference

This document describes the public HTTP API for KlipNote. All endpoints are relative to your deployment base URL (e.g., `http://localhost:8000`). No authentication is required in the current build.

## Conventions
- Content types: JSON unless noted; file uploads use `multipart/form-data`.
- IDs: `job_id` is UUID v4.
- Errors: FastAPI standard shape `{"detail": "..."}`
- Media limits: formats MP3/MP4/WAV/M4A/WMA; max size 2GB; max duration 2 hours.

## Endpoints

### POST /upload
Upload audio/video and start transcription.

Form fields (multipart):
- `file` (required): media file.
- `model` (optional): `belle2` | `whisperx` | `auto` (default from `DEFAULT_TRANSCRIPTION_MODEL`).
- `language` (optional): language hint (e.g., `zh`, `en`); used for routing when `model=auto`.
- `enhancement_config` (optional, JSON string): controls enhancement pipeline.
  - `pipeline`: comma-separated list, default `"vad,refine,split"`.
  - `vad`: `{enabled?, aggressiveness? (0-3)}`
  - `refine`: `{enabled?, search_window_ms?}`
  - `split`: `{enabled?, max_duration?, max_chars?}`
  - Priority: API param > environment variables > code defaults. Omit to stay backward compatible.

Responses:
- 200: `{"job_id": "<uuid>"}` (task queued)
- 400: invalid format/model/enhancement_config
- 413: file too large
- 500: unexpected or storage/ffprobe failure

Examples:
```bash
# Minimal
curl -X POST http://localhost:8000/upload \
  -F "file=@audio.mp3"

# With model and language
curl -X POST http://localhost:8000/upload \
  -F "file=@audio.mp3" \
  -F "model=belle2" \
  -F "language=zh"

# With enhancement_config
curl -X POST http://localhost:8000/upload \
  -F "file=@audio.mp3" \
  -F 'enhancement_config={"pipeline":"vad,split","vad":{"aggressiveness":2}}'
```

### GET /status/{job_id}
Poll transcription status.

Response 200:
```json
{
  "status": "pending|processing|completed|failed",
  "progress": 0,
  "message": "Task queued...",
  "created_at": "2025-11-05T10:30:00Z",
  "updated_at": "2025-11-05T10:31:15Z"
}
```

Errors:
- 404: unknown `job_id`

### GET /result/{job_id}
Fetch completed transcription.

Response 200:
```json
{
  "segments": [
    {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."}
  ]
}
```

Errors:
- 404: job not found, not complete, or failed.

### GET /media/{job_id}
Serve original uploaded media with HTTP Range support. Returns 206 for range requests and appropriate `Content-Type`.

Errors:
- 400: invalid UUID format
- 404: job or media file missing

### POST /export/{job_id}
Export edited transcription as SRT or TXT and store edited copy for data flywheel.

Request body (JSON):
```json
{
  "segments": [
    {"start": 0.5, "end": 3.2, "text": "Edited subtitle text"}
  ],
  "format": "srt"
}
```

Responses:
- 200: file download (`transcript-{job_id}.srt|.txt`)
- 400: invalid payload (empty segments, bad format)
- 404: job/result missing

## Enhancement Config Notes
- Components: `vad`, `refine`, `split` (unknown components rejected).
- Priority: API config > env (`ENHANCEMENT_PIPELINE`, VAD/REFINE/SPLIT settings) > defaults.
- Validation errors return 400 with a descriptive message (invalid JSON, invalid component, out-of-range parameters).

## Common Error Responses
- 400: unsupported file format, duration > 2h, invalid `enhancement_config`, invalid model selection.
- 404: job not found or not ready.
- 413: file exceeds size limit.
- 500: storage or media validation error (ffprobe failure) or unexpected exception.
