export interface UploadResponse {
  job_id: string
}

export interface ErrorResponse {
  detail: string
}

export interface StatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number  // 0-100
  message: string
  created_at: string  // ISO 8601
  updated_at: string  // ISO 8601
}

export interface Segment {
  start: number  // Float seconds
  end: number    // Float seconds
  text: string
}

export interface TranscriptionResult {
  segments: Segment[]
}
