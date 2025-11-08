import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import MediaPlayer from './MediaPlayer.vue'
import { useTranscriptionStore } from '@/stores/transcription'

describe('MediaPlayer Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('renders video element for MP4 files', () => {
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp4',
        jobId: 'test-job-123',
      },
    })

    expect(wrapper.find('video').exists()).toBe(true)
    expect(wrapper.find('audio').exists()).toBe(false)
    expect(wrapper.find('video').attributes('src')).toBe(
      'http://localhost:8000/media/test-job-123.mp4'
    )
  })

  it('renders audio element for MP3 files', () => {
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    expect(wrapper.find('audio').exists()).toBe(true)
    expect(wrapper.find('video').exists()).toBe(false)
    expect(wrapper.find('audio').attributes('src')).toBe(
      'http://localhost:8000/media/test-job-123.mp3'
    )
  })

  it('renders audio element for WAV files', () => {
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.wav',
        jobId: 'test-job-123',
      },
    })

    expect(wrapper.find('audio').exists()).toBe(true)
    expect(wrapper.find('video').exists()).toBe(false)
  })

  it('renders audio element for M4A files', () => {
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.m4a',
        jobId: 'test-job-123',
      },
    })

    expect(wrapper.find('audio').exists()).toBe(true)
    expect(wrapper.find('video').exists()).toBe(false)
  })

  it('has controls attribute enabled', () => {
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio')
    expect(audio.attributes('controls')).toBeDefined()
  })

  it('seeks player when store.currentTime changes significantly (>0.5s)', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element as HTMLAudioElement
    audio.currentTime = 0

    // Simulate store.currentTime change beyond threshold
    store.currentTime = 10.5
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(audio.currentTime).toBe(10.5)
  })

  it('does not seek player when time difference is small (<0.5s)', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element as HTMLAudioElement
    audio.currentTime = 5.0

    // Simulate small store.currentTime change within threshold
    store.currentTime = 5.3 // Only 0.3s difference
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Should NOT update player time (difference < 0.5s)
    expect(audio.currentTime).toBe(5.0)
  })

  it('updates store.playbackTime on timeupdate event (throttled)', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element as HTMLAudioElement

    // Simulate playback position update
    audio.currentTime = 5.0
    await audio.dispatchEvent(new Event('timeupdate'))

    // Fast-forward throttle timer (250ms)
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(store.playbackTime).toBe(5.0)
  })

  it('updates store.isPlaying on play event', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element

    // Simulate play event
    await audio.dispatchEvent(new Event('play'))
    await flushPromises()

    expect(store.isPlaying).toBe(true)
  })

  it('updates store.isPlaying on pause event', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element

    // Set initial playing state
    store.setIsPlaying(true)
    expect(store.isPlaying).toBe(true)

    // Simulate pause event
    await audio.dispatchEvent(new Event('pause'))
    await flushPromises()

    expect(store.isPlaying).toBe(false)
  })

  it('updates store.isPlaying on ended event', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element

    // Set initial playing state
    store.setIsPlaying(true)
    expect(store.isPlaying).toBe(true)

    // Simulate ended event
    await audio.dispatchEvent(new Event('ended'))
    await flushPromises()

    expect(store.isPlaying).toBe(false)
  })

  it('respects isPlaying state when seeking (does not auto-play when paused)', async () => {
    const store = useTranscriptionStore()
    store.isPlaying = false // User paused

    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element as HTMLAudioElement
    const playSpy = vi.spyOn(audio, 'play')
    audio.currentTime = 0

    // Simulate seek while paused
    store.currentTime = 10.5
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Player should seek but NOT auto-play
    expect(audio.currentTime).toBe(10.5)
    expect(playSpy).not.toHaveBeenCalled()
  })

  it('auto-plays after seeking when isPlaying is true', async () => {
    const store = useTranscriptionStore()
    store.isPlaying = true // User was playing

    const wrapper = mount(MediaPlayer, {
      props: {
        mediaUrl: 'http://localhost:8000/media/test-job-123.mp3',
        jobId: 'test-job-123',
      },
    })

    const audio = wrapper.find('audio').element as HTMLAudioElement
    const playSpy = vi.spyOn(audio, 'play')
    audio.currentTime = 0

    // Simulate seek while playing
    store.currentTime = 10.5
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Player should seek AND auto-play
    expect(audio.currentTime).toBe(10.5)
    expect(playSpy).toHaveBeenCalled()
  })
})
