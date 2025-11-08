import type { UploadResponse, StatusResponse, TranscriptionResult, Segment } from '@/types/api'

const API_BASE_URL = 'http://localhost:8000'

/**
 * Upload a media file to the backend for transcription processing
 * @param file - The audio or video file to upload
 * @returns Promise resolving to UploadResponse with job_id
 * @throws Error if upload fails, with error.detail from API or generic message
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
      // Do NOT set Content-Type header - browser sets it automatically with boundary
    })

    if (!response.ok) {
      // Try to parse error response from API
      let error
      try {
        error = await response.json()
      } catch (jsonError) {
        // If response is not JSON, throw generic error
        throw new Error(`Upload failed with status ${response.status}`)
      }
      throw new Error(error.detail || 'Upload failed')
    }

    return await response.json()
  } catch (error) {
    // Re-throw if already an Error object, otherwise create new Error
    if (error instanceof Error) {
      throw error
    }
    throw new Error('Network error: Failed to upload file')
  }
}

/**
 * Fetch the current status of a transcription job
 * @param jobId - The job ID to check status for
 * @returns Promise resolving to StatusResponse with status, progress, and message
 * @throws Error if status fetch fails or job not found
 */
export async function fetchStatus(jobId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/status/${jobId}`)

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Job not found. Please check the job ID.')
    }
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch status')
  }

  return response.json()
}

/**
 * Fetch the transcription result for a completed job
 * @param jobId - The job ID to fetch results for
 * @returns Promise resolving to TranscriptionResult with segments
 * @throws Error if result fetch fails or job not ready
 */
export async function fetchResult(jobId: string): Promise<TranscriptionResult> {
  const response = await fetch(`${API_BASE_URL}/result/${jobId}`)

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Result not ready yet or job not found.')
    }
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch result')
  }

  return response.json()
}

/**
 * Export edited transcription in SRT or TXT format
 * @param jobId - Unique job identifier
 * @param segments - Array of edited subtitle segments
 * @param format - Export format: 'srt' or 'txt'
 * @returns Promise resolving to Blob containing the generated file
 * @throws Error if export fails with status-specific messages
 */
export async function exportTranscription(
  jobId: string,
  segments: Segment[],
  format: 'srt' | 'txt'
): Promise<Blob> {
  try {
    const response = await fetch(`${API_BASE_URL}/export/${jobId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        segments: segments,
        format: format
      })
    })

    if (!response.ok) {
      // Handle specific error status codes
      if (response.status === 404) {
        throw new Error('Export failed: Transcription not found.')
      } else if (response.status === 400) {
        throw new Error('Export failed: Invalid format selected.')
      } else if (response.status === 500) {
        throw new Error('Export failed: Server error. Please try again.')
      } else {
        // Generic error for other status codes
        const errorText = await response.text()
        throw new Error(`Export failed: ${response.status} ${errorText}`)
      }
    }

    return response.blob()
  } catch (error) {
    // Re-throw if already an Error object, otherwise create network error
    if (error instanceof Error) {
      throw error
    }
    throw new Error('Export failed: Network error. Check your connection.')
  }
}
