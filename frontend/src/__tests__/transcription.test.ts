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

    it('initializes originalSegments with pristine API data (Story 2.4)', async () => {
      const store = useTranscriptionStore()
      const mockSegments = [
        { start: 0, end: 5.2, text: 'Hello world' },
        { start: 5.2, end: 10.5, text: 'This is a test' },
      ]

      vi.mocked(api.fetchResult).mockResolvedValue({ segments: mockSegments })

      await store.fetchResult('test-job-123')

      // originalSegments should be deep copy of segments
      expect(store.originalSegments).toEqual(mockSegments)
      // Verify it's a deep copy, not a reference
      expect(store.originalSegments).not.toBe(store.segments)
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

// Story 2.4: Inline Editing Tests
describe('Transcription Store - Story 2.4: Editing Actions', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  describe('updateSegmentText', () => {
    it('should update segment text immediately', () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0.0, end: 2.5, text: 'Original text' }
      ]

      store.updateSegmentText(0, 'New text')

      expect(store.segments[0].text).toBe('New text')
    })

    it('should handle index bounds', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0.0, end: 2.5, text: 'Test' }]

      // Out of bounds - should not crash
      store.updateSegmentText(-1, 'Invalid')
      store.updateSegmentText(5, 'Invalid')

      expect(store.segments[0].text).toBe('Test')
    })

    it('should handle empty string', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0.0, end: 2.5, text: 'Original' }]

      store.updateSegmentText(0, '')

      expect(store.segments[0].text).toBe('')
    })
  })

  describe('cancelEdit', () => {
    it('should revert to original text', () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0.0, end: 2.5, text: 'Edited text' }
      ]
      store.originalSegments = [
        { start: 0.0, end: 2.5, text: 'Original text' }
      ]
      store.editingSegmentId = 0

      store.cancelEdit(0)

      expect(store.segments[0].text).toBe('Original text')
      expect(store.editingSegmentId).toBeNull()
    })

    it('should handle index bounds', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0.0, end: 2.5, text: 'Test' }]
      store.originalSegments = [{ start: 0.0, end: 2.5, text: 'Original' }]
      store.editingSegmentId = 0

      // Out of bounds - should not crash
      store.cancelEdit(-1)
      store.cancelEdit(5)

      expect(store.segments[0].text).toBe('Test')
    })

    it('should handle missing originalSegments', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0.0, end: 2.5, text: 'Test' }]
      store.originalSegments = []
      store.editingSegmentId = 0

      // Should not crash
      store.cancelEdit(0)

      expect(store.segments[0].text).toBe('Test')
    })
  })

  describe('saveToLocalStorage', () => {
    it('should persist segments with correct key', () => {
      const store = useTranscriptionStore()
      const jobId = 'test-job-123'
      store.jobId = jobId
      store.segments = [
        { start: 0.5, end: 3.2, text: 'Test segment' }
      ]

      store.saveToLocalStorage(jobId)

      const saved = localStorage.getItem(`klipnote_edits_${jobId}`)
      expect(saved).not.toBeNull()

      const parsed = JSON.parse(saved!)
      expect(parsed.job_id).toBe(jobId)
      expect(parsed.segments).toHaveLength(1)
      expect(parsed.segments[0].text).toBe('Test segment')
      expect(parsed.last_saved).toBeDefined()
    })

    it('should include ISO timestamp', () => {
      const store = useTranscriptionStore()
      const jobId = 'test-job-123'
      store.segments = [{ start: 0.5, end: 3.2, text: 'Test' }]

      store.saveToLocalStorage(jobId)

      const saved = localStorage.getItem(`klipnote_edits_${jobId}`)
      const parsed = JSON.parse(saved!)

      // Verify ISO 8601 timestamp format
      expect(parsed.last_saved).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
    })

    it('should handle QuotaExceededError gracefully', () => {
      const store = useTranscriptionStore()

      // Setup console spy BEFORE mocking localStorage
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      // Mock localStorage.setItem to throw QuotaExceededError
      const originalSetItem = Storage.prototype.setItem
      Storage.prototype.setItem = vi.fn(() => {
        const error = new DOMException('QuotaExceededError')
        error.name = 'QuotaExceededError'
        throw error
      })

      store.jobId = 'test-job-123'
      store.segments = [{ start: 0.5, end: 3.2, text: 'Text' }]
      store.saveToLocalStorage('test-job-123')

      expect(consoleSpy).toHaveBeenCalled()
      expect(consoleSpy.mock.calls[0][0]).toContain('quota exceeded')

      // Restore
      Storage.prototype.setItem = originalSetItem
      consoleSpy.mockRestore()
    })

    it('should handle generic localStorage errors', () => {
      const store = useTranscriptionStore()

      // Setup console spy BEFORE mocking localStorage
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      // Mock localStorage.setItem to throw generic error
      const originalSetItem = Storage.prototype.setItem
      Storage.prototype.setItem = vi.fn(() => {
        throw new Error('Generic error')
      })

      store.segments = [{ start: 0.5, end: 3.2, text: 'Text' }]
      store.saveToLocalStorage('test-job-123')

      expect(consoleSpy).toHaveBeenCalled()
      expect(consoleSpy.mock.calls[0][0]).toContain('localStorage save failed')

      // Restore
      Storage.prototype.setItem = originalSetItem
      consoleSpy.mockRestore()
    })
  })

  describe('loadFromLocalStorage', () => {
    it('should restore saved segments', () => {
      const jobId = 'test-job-123'
      const editedSegments = [
        { start: 0.5, end: 3.2, text: 'Edited text' }
      ]

      localStorage.setItem(
        `klipnote_edits_${jobId}`,
        JSON.stringify({
          job_id: jobId,
          segments: editedSegments,
          last_saved: new Date().toISOString()
        })
      )

      const store = useTranscriptionStore()
      store.segments = [
        { start: 0.5, end: 3.2, text: 'Original text' }
      ]

      store.loadFromLocalStorage(jobId)

      expect(store.segments[0].text).toBe('Edited text')
    })

    it('should handle missing localStorage data', () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0.5, end: 3.2, text: 'Original text' }
      ]

      store.loadFromLocalStorage('nonexistent-job')

      // Should keep original segments
      expect(store.segments[0].text).toBe('Original text')
    })

    it('should handle corrupted JSON gracefully', () => {
      const jobId = 'test-job-123'
      localStorage.setItem(`klipnote_edits_${jobId}`, 'corrupted-json{')

      const store = useTranscriptionStore()
      const consoleSpy = vi.spyOn(console, 'error')

      store.loadFromLocalStorage(jobId)

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to parse'),
        expect.any(Error)
      )

      // Should clear corrupted key
      expect(localStorage.getItem(`klipnote_edits_${jobId}`)).toBeNull()

      consoleSpy.mockRestore()
    })

    it('should validate segments array structure', () => {
      const jobId = 'test-job-123'

      // Missing segments array
      localStorage.setItem(
        `klipnote_edits_${jobId}`,
        JSON.stringify({
          job_id: jobId,
          last_saved: new Date().toISOString()
        })
      )

      const store = useTranscriptionStore()
      store.segments = [{ start: 0, end: 5, text: 'Original' }]

      store.loadFromLocalStorage(jobId)

      // Should keep original segments
      expect(store.segments[0].text).toBe('Original')
    })

    it('should log restoration message', () => {
      const jobId = 'test-job-123'
      const timestamp = new Date().toISOString()

      localStorage.setItem(
        `klipnote_edits_${jobId}`,
        JSON.stringify({
          job_id: jobId,
          segments: [{ start: 0, end: 5, text: 'Restored' }],
          last_saved: timestamp
        })
      )

      const store = useTranscriptionStore()
      const consoleSpy = vi.spyOn(console, 'log')

      store.loadFromLocalStorage(jobId)

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Restored edits from')
      )

      consoleSpy.mockRestore()
    })
  })

  describe('reset - Story 2.4', () => {
    it('should reset originalSegments', () => {
      const store = useTranscriptionStore()

      store.segments = [{ start: 0, end: 5, text: 'Test' }]
      store.originalSegments = [{ start: 0, end: 5, text: 'Original' }]

      store.reset()

      expect(store.originalSegments).toEqual([])
    })
  })
})
