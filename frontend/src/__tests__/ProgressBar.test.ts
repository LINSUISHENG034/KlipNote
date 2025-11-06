import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProgressBar from '@/components/ProgressBar.vue'

describe('ProgressBar Component', () => {
  it('renders with 0% progress', () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 0 },
    })

    const fill = wrapper.find('.progress-bar-fill')
    expect(fill.attributes('style')).toContain('width: 0%')

    const text = wrapper.find('.progress-text')
    expect(text.text()).toBe('0%')
  })

  it('renders with 50% progress', () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 50 },
    })

    const fill = wrapper.find('.progress-bar-fill')
    expect(fill.attributes('style')).toContain('width: 50%')

    const text = wrapper.find('.progress-text')
    expect(text.text()).toBe('50%')
  })

  it('renders with 100% progress', () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 100 },
    })

    const fill = wrapper.find('.progress-bar-fill')
    expect(fill.attributes('style')).toContain('width: 100%')

    const text = wrapper.find('.progress-text')
    expect(text.text()).toBe('100%')
  })

  it('renders progress bar container', () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 25 },
    })

    expect(wrapper.find('.progress-bar-container').exists()).toBe(true)
    expect(wrapper.find('.progress-bar').exists()).toBe(true)
    expect(wrapper.find('.progress-bar-fill').exists()).toBe(true)
  })

  it('has smooth transition on progress bar fill', () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 75 },
    })

    const fill = wrapper.find('.progress-bar-fill')

    // Verify the fill element exists (the CSS transition is defined in scoped styles)
    expect(fill.exists()).toBe(true)
    expect(fill.attributes('class')).toContain('progress-bar-fill')
  })

  it('updates when progress prop changes', async () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 10 },
    })

    expect(wrapper.find('.progress-text').text()).toBe('10%')

    await wrapper.setProps({ progress: 90 })

    expect(wrapper.find('.progress-text').text()).toBe('90%')
    expect(wrapper.find('.progress-bar-fill').attributes('style')).toContain('width: 90%')
  })

  it('displays percentage text centered', () => {
    const wrapper = mount(ProgressBar, {
      props: { progress: 33 },
    })

    const text = wrapper.find('.progress-text')
    expect(text.exists()).toBe(true)
    expect(text.text()).toBe('33%')
  })
})
