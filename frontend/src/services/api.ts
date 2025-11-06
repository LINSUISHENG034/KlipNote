import type { UploadResponse } from '@/types/api'

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
