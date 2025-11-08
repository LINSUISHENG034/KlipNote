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
      store.currentTime = 10
      store.playbackTime = 8.5
      store.isPlaying = true
      store.activeSegmentIndex = 3
      store.editingSegmentId = 1

      // Reset
      store.reset()

      // Verify all fields reset
      expect(store.jobId).toBeNull()
      expect(store.status).toBe('pending')
      expect(store.progress).toBe(0)
      expect(store.message).toBe('')
      expect(store.segments).toEqual([])
      expect(store.error).toBeNull()
      expect(store.currentTime).toBe(0)
      expect(store.playbackTime).toBe(0)
      expect(store.isPlaying).toBe(false)
      expect(store.activeSegmentIndex).toBe(-1)
      expect(store.editingSegmentId).toBeNull()
    })
  })

  // Story 2.3: Click-to-Timestamp Navigation Tests
  describe('Active Segment Tracking (Story 2.3)', () => {
    describe('updateActiveSegment', () => {
      it('identifies active segment correctly', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 2.5, text: 'Segment 1' },
          { start: 2.5, end: 5.0, text: 'Segment 2' },
          { start: 5.0, end: 8.0, text: 'Segment 3' }
        ]

        store.updateActiveSegment(3.0)
        expect(store.activeSegmentIndex).toBe(1)

        store.updateActiveSegment(6.5)
        expect(store.activeSegmentIndex).toBe(2)

        store.updateActiveSegment(1.0)
        expect(store.activeSegmentIndex).toBe(0)
      })

      it('uses O(1) fast path for sequential playback', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 2.5, text: 'Segment 1' },
          { start: 2.5, end: 5.0, text: 'Segment 2' },
          { start: 5.0, end: 8.0, text: 'Segment 3' }
        ]

        // Simulate sequential playback
        store.activeSegmentIndex = 0
        store.updateActiveSegment(1.0)  // Still in segment 0
        expect(store.activeSegmentIndex).toBe(0)

        store.updateActiveSegment(2.6)  // Moved to segment 1 (next segment check)
        expect(store.activeSegmentIndex).toBe(1)

        store.updateActiveSegment(3.0)  // Still in segment 1
        expect(store.activeSegmentIndex).toBe(1)

        store.updateActiveSegment(5.5)  // Moved to segment 2
        expect(store.activeSegmentIndex).toBe(2)
      })

      it('handles time between segments gracefully', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 2.0, text: 'Segment 1' },
          { start: 5.0, end: 8.0, text: 'Segment 2' }
        ]

        store.updateActiveSegment(3.5)  // Between segments
        expect(store.activeSegmentIndex).toBe(-1)
      })

      it('handles empty segments array', () => {
        const store = useTranscriptionStore()
        store.segments = []

        store.updateActiveSegment(5.0)
        expect(store.activeSegmentIndex).toBe(-1)
      })

      it('handles time before first segment', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 5.0, end: 10.0, text: 'First segment' }
        ]

        store.updateActiveSegment(2.0)
        expect(store.activeSegmentIndex).toBe(-1)
      })

      it('handles time after last segment', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 5.0, text: 'Last segment' }
        ]

        store.updateActiveSegment(10.0)
        expect(store.activeSegmentIndex).toBe(-1)
      })

      it('handles exact segment boundaries', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 5.0, text: 'Segment 1' },
          { start: 5.0, end: 10.0, text: 'Segment 2' }
        ]

        // Exactly at start of segment 2
        store.updateActiveSegment(5.0)
        expect(store.activeSegmentIndex).toBe(1)

        // Just before end of segment 1
        store.updateActiveSegment(4.99)
        expect(store.activeSegmentIndex).toBe(0)
      })

      it('handles user seeking (fallback O(n) search)', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 5.0, text: 'Segment 1' },
          { start: 5.0, end: 10.0, text: 'Segment 2' },
          { start: 10.0, end: 15.0, text: 'Segment 3' },
          { start: 15.0, end: 20.0, text: 'Segment 4' }
        ]

        // Start at segment 0
        store.activeSegmentIndex = 0
        store.updateActiveSegment(1.0)
        expect(store.activeSegmentIndex).toBe(0)

        // User seeks to segment 3 (skips 1 and 2)
        store.updateActiveSegment(17.0)
        expect(store.activeSegmentIndex).toBe(3)

        // Verify it found the correct segment via fallback search
        expect(store.segments[3].start).toBe(15.0)
      })
    })

    describe('seekTo', () => {
      it('updates currentTime for MediaPlayer', () => {
        const store = useTranscriptionStore()
        store.seekTo(10.5)
        expect(store.currentTime).toBe(10.5)
      })

      it('handles zero timestamp', () => {
        const store = useTranscriptionStore()
        store.seekTo(0)
        expect(store.currentTime).toBe(0)
      })

      it('handles fractional timestamps', () => {
        const store = useTranscriptionStore()
        store.seekTo(3.14159)
        expect(store.currentTime).toBe(3.14159)
      })
    })

    describe('updatePlaybackTime', () => {
      it('updates playbackTime and calls updateActiveSegment', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 5.0, text: 'Segment 1' },
          { start: 5.0, end: 10.0, text: 'Segment 2' }
        ]

        store.updatePlaybackTime(2.5)

        expect(store.playbackTime).toBe(2.5)
        expect(store.activeSegmentIndex).toBe(0)
      })

      it('automatically updates activeSegmentIndex during playback', () => {
        const store = useTranscriptionStore()
        store.segments = [
          { start: 0.0, end: 3.0, text: 'Segment 1' },
          { start: 3.0, end: 6.0, text: 'Segment 2' },
          { start: 6.0, end: 9.0, text: 'Segment 3' }
        ]

        // Simulate playback progression
        store.updatePlaybackTime(1.0)
        expect(store.activeSegmentIndex).toBe(0)

        store.updatePlaybackTime(4.5)
        expect(store.activeSegmentIndex).toBe(1)

        store.updatePlaybackTime(7.2)
        expect(store.activeSegmentIndex).toBe(2)
      })
    })

    describe('setEditingSegment (Story 2.4 Prep)', () => {
      it('sets editingSegmentId', () => {
        const store = useTranscriptionStore()
        store.setEditingSegment(5)
        expect(store.editingSegmentId).toBe(5)
      })

      it('clears editingSegmentId when set to null', () => {
        const store = useTranscriptionStore()
        store.editingSegmentId = 3
        store.setEditingSegment(null)
        expect(store.editingSegmentId).toBeNull()
      })
    })
  })
})
