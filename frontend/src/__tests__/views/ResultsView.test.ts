import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ResultsView from '@/views/ResultsView.vue'
import { useTranscriptionStore } from '@/stores/transcription'
import type { Segment } from '@/types/api'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { job_id: 'test-job-123' }
  }),
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('ResultsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const createMockSegments = (count: number): Segment[] => {
    return Array.from({ length: count }, (_, i) => ({
      start: i * 10,
      end: (i + 1) * 10,
      text: `Segment ${i + 1} text`
    }))
  }

  it('should extract job_id from route params', () => {
    const wrapper = mount(ResultsView)
    const vm = wrapper.vm as any
    expect(vm.jobId).toBe('test-job-123')
  })

  it('should call fetchResult on mount if segments are empty', async () => {
    const store = useTranscriptionStore()
    store.segments = []
    const fetchResultSpy = vi.spyOn(store, 'fetchResult').mockResolvedValue()

    mount(ResultsView)
    await flushPromises()

    expect(fetchResultSpy).toHaveBeenCalledWith('test-job-123')
  })

  it('should NOT call fetchResult if segments are already loaded', async () => {
    const store = useTranscriptionStore()
    store.segments = createMockSegments(5)
    const fetchResultSpy = vi.spyOn(store, 'fetchResult').mockResolvedValue()

    mount(ResultsView)
    await flushPromises()

    expect(fetchResultSpy).not.toHaveBeenCalled()
  })

  it('should display loading state during fetch', async () => {
    const store = useTranscriptionStore()
    store.segments = []
    vi.spyOn(store, 'fetchResult').mockImplementation(() => {
      return new Promise(() => {}) // Never resolves
    })

    const wrapper = mount(ResultsView)
    await flushPromises()

    expect(wrapper.find('[data-testid="loading-state"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Loading transcription')
  })

  it('should display error message on fetch failure', async () => {
    const store = useTranscriptionStore()
    store.segments = []
    vi.spyOn(store, 'fetchResult').mockRejectedValue(new Error('Network error'))

    const wrapper = mount(ResultsView)
    await flushPromises()

    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="error-message"]').text()).toBe(
      'Failed to load transcription results. Please try again.'
    )
  })

  it('should display retry button on error', async () => {
    const store = useTranscriptionStore()
    store.segments = []
    vi.spyOn(store, 'fetchResult').mockRejectedValue(new Error('Network error'))

    const wrapper = mount(ResultsView)
    await flushPromises()

    const retryButton = wrapper.find('[data-testid="retry-button"]')
    expect(retryButton.exists()).toBe(true)
    expect(retryButton.text()).toContain('Retry')
  })

  it('should clear error and refetch on retry button click', async () => {
    const store = useTranscriptionStore()
    store.segments = []
    const fetchResultSpy = vi
      .spyOn(store, 'fetchResult')
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce()

    const wrapper = mount(ResultsView)
    await flushPromises()

    // Error state should be visible
    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)

    // Click retry button
    const retryButton = wrapper.find('[data-testid="retry-button"]')
    await retryButton.trigger('click')
    await flushPromises()

    // Should have called fetchResult again
    expect(fetchResultSpy).toHaveBeenCalledTimes(2)
  })

  it('should render SubtitleList when segments are loaded', async () => {
    const store = useTranscriptionStore()
    store.segments = createMockSegments(3)
    vi.spyOn(store, 'fetchResult').mockResolvedValue()

    const wrapper = mount(ResultsView)
    await flushPromises()

    // SubtitleList component should be rendered
    const subtitleList = wrapper.findComponent({ name: 'SubtitleList' })
    expect(subtitleList.exists()).toBe(true)
    expect(subtitleList.props('segments')).toEqual(store.segments)
  })

  it('should display empty state when no segments available', async () => {
    const store = useTranscriptionStore()
    store.segments = []
    vi.spyOn(store, 'fetchResult').mockResolvedValue()

    const wrapper = mount(ResultsView)
    await flushPromises()

    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('No transcription results available')
  })

  it('should transition from loading to success state', async () => {
    const store = useTranscriptionStore()
    store.segments = []

    let resolvePromise: () => void
    const fetchPromise = new Promise<void>((resolve) => {
      resolvePromise = resolve
    })
    vi.spyOn(store, 'fetchResult').mockReturnValue(fetchPromise)

    const wrapper = mount(ResultsView)
    await flushPromises()

    // Should show loading initially
    expect(wrapper.find('[data-testid="loading-state"]').exists()).toBe(true)

    // Simulate successful fetch
    store.segments = createMockSegments(5)
    resolvePromise!()
    await flushPromises()

    // Should show SubtitleList after loading
    expect(wrapper.find('[data-testid="loading-state"]').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'SubtitleList' }).exists()).toBe(true)
  })

  it('should have proper page title', () => {
    const wrapper = mount(ResultsView)
    expect(wrapper.find('[data-testid="top-bar-title"]').text()).toBe('KlipNote Demo')
  })
})
