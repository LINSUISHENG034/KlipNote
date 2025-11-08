import { defineStore } from 'pinia'
import type { Segment, StatusResponse } from '@/types/api'
import * as api from '@/services/api'

export const useTranscriptionStore = defineStore('transcription', {
  state: () => ({
    jobId: null as string | null,
    status: 'pending' as 'pending' | 'processing' | 'completed' | 'failed',
    progress: 0,
    message: '',
    segments: [] as Segment[],
    error: null as string | null,

    // Epic 2: Media player state synchronization
    currentTime: 0,       // Commanded seek position (Story 2.3 uses this)
    playbackTime: 0,      // Actual player position
    isPlaying: false,     // Player play/pause state

    // Story 2.3: Click-to-timestamp navigation
    activeSegmentIndex: -1,  // Currently highlighted segment (-1 = none)

    // Story 2.4 prep: Inline editing
    editingSegmentId: null as number | null,  // Segment being edited (null = none)
  }),

  getters: {
    isProcessing: (state) => state.status === 'processing' || state.status === 'pending',
    isCompleted: (state) => state.status === 'completed',
    isFailed: (state) => state.status === 'failed',
  },

  actions: {
    async fetchStatus(jobId: string) {
      try {
        const response = await api.fetchStatus(jobId)
        this.jobId = jobId
        this.status = response.status
        this.progress = response.progress
        this.message = response.message
        this.error = null
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to fetch status'
        throw error
      }
    },

    async fetchResult(jobId: string) {
      try {
        const response = await api.fetchResult(jobId)
        this.segments = response.segments
        this.error = null
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to fetch result'
        throw error
      }
    },

    reset() {
      this.jobId = null
      this.status = 'pending'
      this.progress = 0
      this.message = ''
      this.segments = []
      this.error = null

      // Reset player state
      this.currentTime = 0
      this.playbackTime = 0
      this.isPlaying = false
      this.activeSegmentIndex = -1
      this.editingSegmentId = null
    },

    // Epic 2: Media player state actions
    seekTo(time: number) {
      this.currentTime = time
    },

    updatePlaybackTime(time: number) {
      this.playbackTime = time
      this.updateActiveSegment(time)
    },

    setIsPlaying(playing: boolean) {
      this.isPlaying = playing
    },

    // Story 2.3: Active segment tracking with incremental search optimization
    updateActiveSegment(time: number) {
      if (this.segments.length === 0) {
        this.activeSegmentIndex = -1
        return
      }

      const currentIndex = this.activeSegmentIndex

      // Fast path 1: Check current segment (99% case during playback)
      if (currentIndex >= 0 && currentIndex < this.segments.length) {
        const currentSeg = this.segments[currentIndex]
        if (time >= currentSeg.start && time < currentSeg.end) {
          return // Still in current segment, no update needed
        }
      }

      // Fast path 2: Check next segment (normal sequential playback)
      const nextIndex = currentIndex + 1
      if (nextIndex < this.segments.length) {
        const nextSeg = this.segments[nextIndex]
        if (time >= nextSeg.start && time < nextSeg.end) {
          this.activeSegmentIndex = nextIndex
          return
        }
      }

      // Fallback: User seeked/scrubbed, do full search (O(n))
      const index = this.segments.findIndex(
        seg => time >= seg.start && time < seg.end
      )
      this.activeSegmentIndex = index // -1 if not found (between segments)
    },

    // Story 2.4 prep: Editing state management
    setEditingSegment(segmentId: number | null) {
      this.editingSegmentId = segmentId
    },
  },
})
