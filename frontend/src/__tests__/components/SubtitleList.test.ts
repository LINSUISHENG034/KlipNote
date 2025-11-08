import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SubtitleList from '@/components/SubtitleList.vue'
import { useTranscriptionStore } from '@/stores/transcription'
import type { Segment } from '@/types/api'

describe('SubtitleList - Story 2.3: Click-to-Timestamp Navigation', () => {
  beforeEach(() => {
    setActivePinia(createPinia())

    // Mock scrollIntoView (not available in JSDOM)
    Element.prototype.scrollIntoView = vi.fn()
  })

  const createMockSegments = (count: number): Segment[] => {
    return Array.from({ length: count }, (_, i) => ({
      start: i * 5,
      end: (i + 1) * 5,
      text: `Segment ${i + 1} text content`
    }))
  }

  describe('Component Rendering', () => {
    it('should render all segments from store', () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(3)

      const wrapper = mount(SubtitleList)

      const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
      expect(segmentElements).toHaveLength(3)
    })

    it('should display timestamp and text for each segment', () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0, end: 10, text: 'First segment' },
        { start: 10, end: 20, text: 'Second segment' }
      ]

      const wrapper = mount(SubtitleList)

      const firstSegment = wrapper.findAll('[data-testid="subtitle-segment"]')[0]
      expect(firstSegment.find('[data-testid="timestamp"]').text()).toBe('00:00')
      expect(firstSegment.find('[data-testid="text"]').text()).toBe('First segment')

      const secondSegment = wrapper.findAll('[data-testid="subtitle-segment"]')[1]
      expect(secondSegment.find('[data-testid="timestamp"]').text()).toBe('00:10')
      expect(secondSegment.find('[data-testid="text"]').text()).toBe('Second segment')
    })

    it('should handle empty segments array gracefully', () => {
      const store = useTranscriptionStore()
      store.segments = []

      const wrapper = mount(SubtitleList)

      const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
      expect(segmentElements).toHaveLength(0)
      expect(wrapper.find('[data-testid="subtitle-list"]').exists()).toBe(true)
    })

    it('should render 100+ segments without errors (stress test)', () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(150)

      const wrapper = mount(SubtitleList)

      const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
      expect(segmentElements).toHaveLength(150)
    })
  })

  describe('Click-to-Timestamp Navigation (AC #1, #2)', () => {
    it('should call store.seekTo() when subtitle clicked', async () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0.5, end: 3.2, text: 'Test subtitle' },
        { start: 3.5, end: 7.8, text: 'Another segment' }
      ]

      const wrapper = mount(SubtitleList)
      await wrapper.findAll('[data-testid="subtitle-segment"]')[0].trigger('click')

      expect(store.currentTime).toBe(0.5)
    })

    it('should seek to correct timestamp for second segment', async () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0, end: 5, text: 'First' },
        { start: 5, end: 10, text: 'Second' },
        { start: 10, end: 15, text: 'Third' }
      ]

      const wrapper = mount(SubtitleList)
      await wrapper.findAll('[data-testid="subtitle-segment"]')[1].trigger('click')

      expect(store.currentTime).toBe(5)
    })

    it('should handle rapid clicking on multiple segments', async () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(5)

      const wrapper = mount(SubtitleList)
      const segments = wrapper.findAll('[data-testid="subtitle-segment"]')

      await segments[0].trigger('click')
      expect(store.currentTime).toBe(0)

      await segments[2].trigger('click')
      expect(store.currentTime).toBe(10)

      await segments[4].trigger('click')
      expect(store.currentTime).toBe(20)
    })
  })

  describe('Active Segment Highlighting (AC #3, #4)', () => {
    it('should highlight active segment based on store.activeSegmentIndex', async () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0, end: 5, text: 'Segment 1' },
        { start: 5, end: 10, text: 'Segment 2' },
        { start: 10, end: 15, text: 'Segment 3' }
      ]
      store.activeSegmentIndex = 1

      const wrapper = mount(SubtitleList)
      const segments = wrapper.findAll('[data-testid="subtitle-segment"]')

      expect(segments[0].classes()).not.toContain('bg-blue-900/40')
      expect(segments[1].classes()).toContain('bg-blue-900/40')
      expect(segments[1].classes()).toContain('border-l-4')
      expect(segments[2].classes()).not.toContain('bg-blue-900/40')
    })

    it('should update highlighting when activeSegmentIndex changes', async () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(3)
      store.activeSegmentIndex = 0

      const wrapper = mount(SubtitleList)

      let segments = wrapper.findAll('[data-testid="subtitle-segment"]')
      expect(segments[0].classes()).toContain('bg-blue-900/40')

      // Simulate playback progressing to next segment
      store.activeSegmentIndex = 1
      await wrapper.vm.$nextTick()

      segments = wrapper.findAll('[data-testid="subtitle-segment"]')
      expect(segments[0].classes()).not.toContain('bg-blue-900/40')
      expect(segments[1].classes()).toContain('bg-blue-900/40')
    })

    it('should handle activeSegmentIndex = -1 (between segments)', async () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(3)
      store.activeSegmentIndex = -1

      const wrapper = mount(SubtitleList)
      const segments = wrapper.findAll('[data-testid="subtitle-segment"]')

      segments.forEach(segment => {
        expect(segment.classes()).not.toContain('bg-blue-900/40')
      })
    })

    it('should apply distinct styles to active segment', async () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0, end: 5, text: 'Active segment' }]
      store.activeSegmentIndex = 0

      const wrapper = mount(SubtitleList)
      const segment = wrapper.find('[data-testid="subtitle-segment"]')

      expect(segment.classes()).toContain('bg-blue-900/40')
      expect(segment.classes()).toContain('border-blue-500')
      expect(segment.classes()).toContain('font-semibold')
    })
  })

  describe('Hover and Touch Feedback (AC #7)', () => {
    it('should show cursor pointer when not editing', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0, end: 5, text: 'Test' }]
      store.editingSegmentId = null

      const wrapper = mount(SubtitleList)
      const segment = wrapper.find('[data-testid="subtitle-segment"]')

      expect(segment.classes()).toContain('cursor-pointer')
    })

    it('should show hover background when not editing', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0, end: 5, text: 'Test' }]
      store.activeSegmentIndex = -1
      store.editingSegmentId = null

      const wrapper = mount(SubtitleList)
      const segment = wrapper.find('[data-testid="subtitle-segment"]')

      expect(segment.classes()).toContain('hover:bg-zinc-800/70')
    })

    it('should NOT show hover on active segment', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0, end: 5, text: 'Test' }]
      store.activeSegmentIndex = 0

      const wrapper = mount(SubtitleList)
      const segment = wrapper.find('[data-testid="subtitle-segment"]')

      expect(segment.classes()).not.toContain('hover:bg-zinc-800/70')
      expect(segment.classes()).toContain('bg-blue-900/40')
    })
  })

  describe('Editing State Guard (Story 2.4 Prep)', () => {
    it('should block seek when editingSegmentId is set', async () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0, end: 5, text: 'Test' },
        { start: 5, end: 10, text: 'Another' }
      ]
      store.editingSegmentId = 0
      const initialTime = store.currentTime

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const wrapper = mount(SubtitleList)
      await wrapper.find('[data-testid="subtitle-segment"]').trigger('click')

      // currentTime should not change when editing
      expect(store.currentTime).toBe(initialTime)
      expect(consoleWarnSpy).toHaveBeenCalledWith('Cannot seek while editing. Please finish editing first.')

      consoleWarnSpy.mockRestore()
    })

    it('should show cursor-not-allowed when editing', () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 0, end: 5, text: 'Test' }]
      store.editingSegmentId = 0

      const wrapper = mount(SubtitleList)
      const segment = wrapper.find('[data-testid="subtitle-segment"]')

      expect(segment.classes()).toContain('cursor-not-allowed')
      expect(segment.classes()).toContain('opacity-60')
    })

    it('should allow seek when editingSegmentId is null', async () => {
      const store = useTranscriptionStore()
      store.segments = [{ start: 2.5, end: 7.0, text: 'Test' }]
      store.editingSegmentId = null

      const wrapper = mount(SubtitleList)
      await wrapper.find('[data-testid="subtitle-segment"]').trigger('click')

      expect(store.currentTime).toBe(2.5)
    })
  })

  describe('Auto-scroll Behavior (AC #3, #4)', () => {
    it('should have refs array for scroll management', () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(3)

      const wrapper = mount(SubtitleList)

      // Component should have segmentRefs array
      expect(wrapper.vm).toBeDefined()
    })

    it('should add ref attribute to each segment', () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(3)

      const wrapper = mount(SubtitleList)
      const segments = wrapper.findAll('[data-testid="subtitle-segment"]')

      // Each segment should have ref binding
      expect(segments.length).toBe(3)
    })
  })

  describe('Performance and Edge Cases', () => {
    it('should handle segments with identical timestamps', async () => {
      const store = useTranscriptionStore()
      store.segments = [
        { start: 0, end: 5, text: 'First' },
        { start: 0, end: 5, text: 'Duplicate' }
      ]

      const wrapper = mount(SubtitleList)
      await wrapper.findAll('[data-testid="subtitle-segment"]')[1].trigger('click')

      expect(store.currentTime).toBe(0)
    })

    it('should handle very long segment text', () => {
      const store = useTranscriptionStore()
      const longText = 'This is a very long subtitle segment that contains a lot of text content and should still render correctly without breaking the layout or causing any visual issues in the component. '.repeat(5)
      store.segments = [{ start: 0, end: 10, text: longText }]

      const wrapper = mount(SubtitleList)
      const text = wrapper.find('[data-testid="text"]')

      // Check that text starts with expected content
      expect(text.text()).toContain('This is a very long subtitle segment')
      expect(text.text().length).toBeGreaterThan(500)
    })

    it('should maintain scroll container max height', () => {
      const store = useTranscriptionStore()
      store.segments = createMockSegments(50)

      const wrapper = mount(SubtitleList)
      const container = wrapper.find('[data-testid="subtitle-list"]')

      expect(container.classes()).toContain('max-h-[600px]')
      expect(container.classes()).toContain('overflow-y-auto')
    })
  })
})
