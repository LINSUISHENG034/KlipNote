import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { uploadFile, fetchStatus, fetchResult } from '@/services/api'

describe('API Service', () => {
  const mockFetch = vi.fn()
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = mockFetch
    mockFetch.mockClear()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  describe('uploadFile', () => {
    it('constructs FormData with file correctly', async () => {
      const mockJobId = '550e8400-e29b-41d4-a716-446655440000'
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ job_id: mockJobId }),
      })

      await uploadFile(file)

      expect(mockFetch).toHaveBeenCalledTimes(1)

      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs).toBeDefined()
      expect(callArgs![0]).toBe('http://localhost:8000/upload')
      expect(callArgs![1].method).toBe('POST')

      const formData = callArgs![1].body as FormData
      expect(formData).toBeInstanceOf(FormData)
      expect(formData.get('file')).toBe(file)
    })

    it('does not set Content-Type header (browser sets it with boundary)', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ job_id: 'test-id' }),
      })

      await uploadFile(file)

      const callArgs = mockFetch.mock.calls[0]
      expect(callArgs).toBeDefined()
      expect(callArgs![1].headers).toBeUndefined()
    })

    it('returns job_id from successful response', async () => {
      const mockJobId = '550e8400-e29b-41d4-a716-446655440000'
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ job_id: mockJobId }),
      })

      const result = await uploadFile(file)

      expect(result).toEqual({ job_id: mockJobId })
    })

    it('throws Error with detail message from API error response', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
      const errorDetail = 'File format not supported. Please upload MP3, MP4, WAV, or M4A.'

      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: errorDetail }),
      })

      await expect(uploadFile(file)).rejects.toThrow(errorDetail)
    })

    it('throws generic error message when API error response has no detail', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      })

      await expect(uploadFile(file)).rejects.toThrow('Upload failed')
    })

    it('throws generic error when response is not JSON', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(uploadFile(file)).rejects.toThrow('Upload failed with status 500')
    })

    it('throws network error when fetch fails', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockRejectedValue(new TypeError('Network request failed'))

      await expect(uploadFile(file)).rejects.toThrow('Network request failed')
    })

    it('throws generic network error for non-Error exceptions', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockRejectedValue('Unknown error')

      await expect(uploadFile(file)).rejects.toThrow('Network error: Failed to upload file')
    })

    it('handles 413 Payload Too Large error', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
      const errorDetail = 'File size exceeds maximum limit of 2.0GB'

      mockFetch.mockResolvedValue({
        ok: false,
        status: 413,
        json: async () => ({ detail: errorDetail }),
      })

      await expect(uploadFile(file)).rejects.toThrow(errorDetail)
    })

    it('makes POST request to correct endpoint', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ job_id: 'test-id' }),
      })

      await uploadFile(file)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/upload',
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('accepts different audio file types', async () => {
      const audioTypes = [
        { name: 'MP3', type: 'audio/mpeg' },
        { name: 'WAV', type: 'audio/wav' },
        { name: 'M4A', type: 'audio/x-m4a' },
      ]

      for (const { name, type } of audioTypes) {
        const file = new File(['content'], `test.${name.toLowerCase()}`, { type })

        mockFetch.mockResolvedValue({
          ok: true,
          json: async () => ({ job_id: `${name}-id` }),
        })

        const result = await uploadFile(file)
        expect(result.job_id).toBe(`${name}-id`)

        mockFetch.mockClear()
      }
    })

    it('accepts video file types', async () => {
      const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ job_id: 'video-id' }),
      })

      const result = await uploadFile(file)
      expect(result.job_id).toBe('video-id')
    })
  })

  describe('fetchStatus', () => {
    it('returns status response from successful API call', async () => {
      const mockResponse = {
        status: 'processing',
        progress: 45,
        message: 'Transcribing audio...',
        created_at: '2025-11-06T10:00:00Z',
        updated_at: '2025-11-06T10:05:00Z',
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await fetchStatus('test-job-123')

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/status/test-job-123')
      expect(result).toEqual(mockResponse)
    })

    it('throws error with 404 message when job not found', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Job not found' }),
      })

      await expect(fetchStatus('invalid-job')).rejects.toThrow('Job not found. Please check the job ID.')
    })

    it('throws error with detail from API error response', async () => {
      const errorDetail = 'Internal server error'

      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: errorDetail }),
      })

      await expect(fetchStatus('test-job')).rejects.toThrow(errorDetail)
    })

    it('throws generic error when API error has no detail', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      })

      await expect(fetchStatus('test-job')).rejects.toThrow('Failed to fetch status')
    })
  })

  describe('fetchResult', () => {
    it('returns transcription result from successful API call', async () => {
      const mockResponse = {
        segments: [
          { start: 0, end: 5.2, text: 'Hello world' },
          { start: 5.2, end: 10.5, text: 'This is a test' },
        ],
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await fetchResult('test-job-123')

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/result/test-job-123')
      expect(result).toEqual(mockResponse)
    })

    it('throws error with 404 message when result not ready', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Result not found' }),
      })

      await expect(fetchResult('test-job')).rejects.toThrow('Result not ready yet or job not found.')
    })

    it('throws error with detail from API error response', async () => {
      const errorDetail = 'Processing incomplete'

      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: errorDetail }),
      })

      await expect(fetchResult('test-job')).rejects.toThrow(errorDetail)
    })

    it('throws generic error when API error has no detail', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      })

      await expect(fetchResult('test-job')).rejects.toThrow('Failed to fetch result')
    })
  })
})
