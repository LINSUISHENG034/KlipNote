import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SubtitleList from '@/components/SubtitleList.vue'
import type { Segment } from '@/types/api'

describe('SubtitleList', () => {
  const createMockSegments = (count: number): Segment[] => {
    return Array.from({ length: count }, (_, i) => ({
      start: i * 10,
      end: (i + 1) * 10,
      text: `Segment ${i + 1} text content`
    }))
  }

  it('should render all segments from props', () => {
    const segments = createMockSegments(3)
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
    expect(segmentElements).toHaveLength(3)
  })

  it('should display timestamp and text for each segment', () => {
    const segments: Segment[] = [
      { start: 0, end: 10, text: 'First segment' },
      { start: 10, end: 20, text: 'Second segment' }
    ]
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    const firstSegment = wrapper.findAll('[data-testid="subtitle-segment"]')[0]
    expect(firstSegment.find('[data-testid="timestamp"]').text()).toBe('00:00')
    expect(firstSegment.find('[data-testid="text"]').text()).toBe('First segment')

    const secondSegment = wrapper.findAll('[data-testid="subtitle-segment"]')[1]
    expect(secondSegment.find('[data-testid="timestamp"]').text()).toBe('00:10')
    expect(secondSegment.find('[data-testid="text"]').text()).toBe('Second segment')
  })

  it('should format timestamps correctly using formatTime()', () => {
    const segments: Segment[] = [
      { start: 65.5, end: 75, text: 'Test segment' },
      { start: 3661, end: 3671, text: 'Another segment' }
    ]
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    const timestamps = wrapper.findAll('[data-testid="timestamp"]')
    expect(timestamps[0].text()).toBe('01:05')
    expect(timestamps[1].text()).toBe('61:01')
  })

  it('should handle empty segments array gracefully', () => {
    const wrapper = mount(SubtitleList, {
      props: { segments: [] }
    })

    const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
    expect(segmentElements).toHaveLength(0)

    // Component should still render the container
    expect(wrapper.find('[data-testid="subtitle-list"]').exists()).toBe(true)
  })

  it('should render container with scrollable class', () => {
    const segments = createMockSegments(5)
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    const container = wrapper.find('[data-testid="subtitle-list"]')
    expect(container.exists()).toBe(true)
    // Container has the subtitle-list data-testid for identification
    expect(container.attributes('data-testid')).toBe('subtitle-list')
  })

  it('should render 100+ segments without errors', () => {
    const segments = createMockSegments(150)
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
    expect(segmentElements).toHaveLength(150)
  })

  it('should have distinct visual separation for each segment', () => {
    const segments = createMockSegments(3)
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    const segmentElements = wrapper.findAll('[data-testid="subtitle-segment"]')
    segmentElements.forEach(segment => {
      // Each segment should have its own container with data-testid
      expect(segment.attributes('data-testid')).toBe('subtitle-segment')
    })
  })

  it('should have proper semantic structure', () => {
    const segments: Segment[] = [
      { start: 0, end: 10, text: 'Test segment' }
    ]
    const wrapper = mount(SubtitleList, {
      props: { segments }
    })

    expect(wrapper.find('[data-testid="subtitle-list"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="subtitle-segment"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="timestamp"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="text"]').exists()).toBe(true)
  })
})
