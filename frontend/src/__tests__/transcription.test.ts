import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTranscriptionStore } from '@/stores/transcription'
import * as api from '@/services/api'

vi.mock('@/services/api')

describe('Transcription Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('initializes with default values', () => {
      const store = useTranscriptionStore()

      expect(store.jobId).toBeNull()
      expect(store.status).toBe('pending')
      expect(store.progress).toBe(0)
      expect(store.message).toBe('')
      expect(store.segments).toEqual([])
      expect(store.error).toBeNull()
    })
  })

  describe('Getters', () => {
    it('isProcessing returns true when status is pending', () => {
      const store = useTranscriptionStore()
      store.status = 'pending'
      expect(store.isProcessing).toBe(true)
    })

    it('isProcessing returns true when status is processing', () => {
      const store = useTranscriptionStore()
      store.status = 'processing'
      expect(store.isProcessing).toBe(true)
    })

    it('isProcessing returns false when status is completed', () => {
      const store = useTranscriptionStore()
      store.status = 'completed'
      expect(store.isProcessing).toBe(false)
    })

    it('isCompleted returns true when status is completed', () => {
      const store = useTranscriptionStore()
      store.status = 'completed'
      expect(store.isCompleted).toBe(true)
    })

    it('isCompleted returns false when status is pending', () => {
      const store = useTranscriptionStore()
      store.status = 'pending'
      expect(store.isCompleted).toBe(false)
    })

    it('isFailed returns true when status is failed', () => {
      const store = useTranscriptionStore()
      store.status = 'failed'
      expect(store.isFailed).toBe(true)
    })

    it('isFailed returns false when status is processing', () => {
      const store = useTranscriptionStore()
      store.status = 'processing'
      expect(store.isFailed).toBe(false)
    })
  })

  describe('fetchStatus', () => {
    it('updates store state on successful API call', async () => {
      const store = useTranscriptionStore()
      const mockResponse = {
        status: 'processing' as const,
        progress: 45,
        message: 'Transcribing audio...',
        created_at: '2025-11-06T10:00:00Z',
        updated_at: '2025-11-06T10:05:00Z',
      }

      vi.mocked(api.fetchStatus).mockResolvedValue(mockResponse)

      await store.fetchStatus('test-job-123')

      expect(store.jobId).toBe('test-job-123')
      expect(store.status).toBe('processing')
      expect(store.progress).toBe(45)
      expect(store.message).toBe('Transcribing audio...')
      expect(store.error).toBeNull()
    })

    it('sets error and throws on API failure', async () => {
      const store = useTranscriptionStore()
      const errorMessage = 'Job not found. Please check the job ID.'

      vi.mocked(api.fetchStatus).mockRejectedValue(new Error(errorMessage))

      await expect(store.fetchStatus('invalid-job')).rejects.toThrow(errorMessage)
      expect(store.error).toBe(errorMessage)
    })

    it('clears previous error on successful call', async () => {
      const store = useTranscriptionStore()
      store.error = 'Previous error'

      const mockResponse = {
        status: 'processing' as const,
        progress: 50,
        message: 'Processing...',
        created_at: '2025-11-06T10:00:00Z',
        updated_at: '2025-11-06T10:05:00Z',
      }

      vi.mocked(api.fetchStatus).mockResolvedValue(mockResponse)

      await store.fetchStatus('test-job')

      expect(store.error).toBeNull()
    })
  })

  describe('fetchResult', () => {
    it('updates segments on successful API call', async () => {
      const store = useTranscriptionStore()
      const mockSegments = [
        { start: 0, end: 5.2, text: 'Hello world' },
        { start: 5.2, end: 10.5, text: 'This is a test' },
      ]

      vi.mocked(api.fetchResult).mockResolvedValue({ segments: mockSegments })

      await store.fetchResult('test-job-123')

      expect(store.segments).toEqual(mockSegments)
      expect(store.error).toBeNull()
    })

    it('sets error and throws on API failure', async () => {
      const store = useTranscriptionStore()
      const errorMessage = 'Result not ready yet or job not found.'

      vi.mocked(api.fetchResult).mockRejectedValue(new Error(errorMessage))

      await expect(store.fetchResult('invalid-job')).rejects.toThrow(errorMessage)
      expect(store.error).toBe(errorMessage)
    })

    it('clears previous error on successful call', async () => {
      const store = useTranscriptionStore()
      store.error = 'Previous error'

      vi.mocked(api.fetchResult).mockResolvedValue({ segments: [] })

      await store.fetchResult('test-job')

      expect(store.error).toBeNull()
    })
  })

  describe('reset', () => {
    it('resets all state to default values', () => {
      const store = useTranscriptionStore()

      // Modify state
      store.jobId = 'test-job'
      store.status = 'completed'
      store.progress = 100
      store.message = 'Complete!'
      store.segments = [{ start: 0, end: 5, text: 'Test' }]
      store.error = 'Some error'

      // Reset
      store.reset()

      // Verify all fields reset
      expect(store.jobId).toBeNull()
      expect(store.status).toBe('pending')
      expect(store.progress).toBe(0)
      expect(store.message).toBe('')
      expect(store.segments).toEqual([])
      expect(store.error).toBeNull()
    })
  })
})
