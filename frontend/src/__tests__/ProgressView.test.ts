import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import ProgressView from '@/views/ProgressView.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { useTranscriptionStore } from '@/stores/transcription'
import * as api from '@/services/api'

vi.mock('@/services/api')

describe('ProgressView', () => {
  let router: ReturnType<typeof createRouter>

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.useFakeTimers()

    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/progress/:job_id',
          component: ProgressView,
        },
        {
          path: '/results/:job_id',
          component: { template: '<div>Results</div>' },
        },
        {
          path: '/',
          component: { template: '<div>Upload</div>' },
        },
      ],
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('extracts job_id from route params', async () => {
    await router.push('/progress/test-job-123')
    await router.isReady()

    const wrapper = mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('.job-id').text()).toContain('test-job-123')
  })

  it('starts polling immediately on mount', async () => {
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'processing',
      progress: 25,
      message: 'Processing...',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // Should be called once immediately on mount
    expect(api.fetchStatus).toHaveBeenCalledTimes(1)
    expect(api.fetchStatus).toHaveBeenCalledWith('test-job')
  })

  it('polls every 3 seconds', async () => {
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'processing',
      progress: 25,
      message: 'Processing...',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(1)

    // Advance 3 seconds
    vi.advanceTimersByTime(3000)
    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(2)

    // Advance another 3 seconds
    vi.advanceTimersByTime(3000)
    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(3)
  })

  it('stops polling on unmount', async () => {
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'processing',
      progress: 25,
      message: 'Processing...',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    const wrapper = mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(1)

    // Unmount component
    wrapper.unmount()

    // Advance time - polling should not continue
    vi.advanceTimersByTime(6000)
    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(1) // Still only once
  })

  it('displays ProgressBar with store progress', async () => {
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'processing',
      progress: 65,
      message: 'Processing...',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    const wrapper = mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    const progressBar = wrapper.findComponent(ProgressBar)
    expect(progressBar.exists()).toBe(true)
    expect(progressBar.props('progress')).toBe(65)
  })

  it('displays status message from store', async () => {
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'processing',
      progress: 50,
      message: 'Transcribing audio...',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    const wrapper = mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.find('.status-message').text()).toBe('Transcribing audio...')
  })

  it('navigates to results page when status is completed', async () => {
    const store = useTranscriptionStore()

    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'processing',
      progress: 50,
      message: 'Processing...',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    vi.mocked(api.fetchResult).mockResolvedValue({
      segments: [{ start: 0, end: 5, text: 'Test' }],
    })

    await router.push('/progress/test-job')
    await router.isReady()

    mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // Simulate completion
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'completed',
      progress: 100,
      message: 'Complete!',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:10:00Z',
    })

    vi.advanceTimersByTime(3000)
    await flushPromises()

    // Should fetch result and navigate
    expect(api.fetchResult).toHaveBeenCalledWith('test-job')
    expect(router.currentRoute.value.path).toBe('/results/test-job')
  })

  it('displays error message when status is failed', async () => {
    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'failed',
      progress: 30,
      message: 'Processing failed due to invalid file format',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    const wrapper = mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.find('.error-section').exists()).toBe(true)
    expect(wrapper.find('.error-message').text()).toContain('Processing failed')
    expect(wrapper.find('.retry-button').exists()).toBe(true)
  })

  it('retry button resets store and navigates to upload page', async () => {
    const store = useTranscriptionStore()

    vi.mocked(api.fetchStatus).mockResolvedValue({
      status: 'failed',
      progress: 0,
      message: 'Failed',
      created_at: '2025-11-06T10:00:00Z',
      updated_at: '2025-11-06T10:05:00Z',
    })

    await router.push('/progress/test-job')
    await router.isReady()

    const wrapper = mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // Click retry button
    await wrapper.find('.retry-button').trigger('click')
    await flushPromises()

    // Store should be reset
    expect(store.jobId).toBeNull()
    expect(store.status).toBe('pending')

    // Should navigate to home
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('continues polling on transient errors', async () => {
    // First call fails, second succeeds
    vi.mocked(api.fetchStatus)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        status: 'processing',
        progress: 40,
        message: 'Processing...',
        created_at: '2025-11-06T10:00:00Z',
        updated_at: '2025-11-06T10:05:00Z',
      })

    await router.push('/progress/test-job')
    await router.isReady()

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // First call should fail
    expect(api.fetchStatus).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).toHaveBeenCalled()

    // Should continue polling
    vi.advanceTimersByTime(3000)
    await flushPromises()

    expect(api.fetchStatus).toHaveBeenCalledTimes(2)

    consoleErrorSpy.mockRestore()
  })

  it('stops polling when status changes to completed', async () => {
    vi.mocked(api.fetchStatus)
      .mockResolvedValueOnce({
        status: 'processing',
        progress: 50,
        message: 'Processing...',
        created_at: '2025-11-06T10:00:00Z',
        updated_at: '2025-11-06T10:05:00Z',
      })
      .mockResolvedValueOnce({
        status: 'completed',
        progress: 100,
        message: 'Complete!',
        created_at: '2025-11-06T10:00:00Z',
        updated_at: '2025-11-06T10:10:00Z',
      })

    vi.mocked(api.fetchResult).mockResolvedValue({
      segments: [],
    })

    await router.push('/progress/test-job')
    await router.isReady()

    mount(ProgressView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(3000)
    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(2)

    // Advance more time - should not poll again
    vi.advanceTimersByTime(6000)
    await flushPromises()
    expect(api.fetchStatus).toHaveBeenCalledTimes(2)
  })
})
