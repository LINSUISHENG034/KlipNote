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
    },
  },
})
