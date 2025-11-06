import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUpload from '@/components/FileUpload.vue'

describe('FileUpload Component', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    wrapper = mount(FileUpload)
  })

  describe('Rendering', () => {
    it('renders upload zone with instructions', () => {
      expect(wrapper.find('.file-upload').exists()).toBe(true)
      expect(wrapper.text()).toContain('Drag and drop your file here')
      expect(wrapper.text()).toContain('Choose File')
    })

    it('renders file input with accept attribute', () => {
      const fileInput = wrapper.find('input[type="file"]')
      expect(fileInput.exists()).toBe(true)
      expect(fileInput.attributes('accept')).toBe('audio/*,video/*')
    })
  })

  describe('File Selection via Input', () => {
    it('emits file-selected event with File object when audio file is selected', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false,
      })

      await fileInput.trigger('change')

      expect(wrapper.emitted('file-selected')).toBeTruthy()
      expect(wrapper.emitted('file-selected')?.[0]).toEqual([file])
    })

    it('emits file-selected event when video file is selected', async () => {
      const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false,
      })

      await fileInput.trigger('change')

      expect(wrapper.emitted('file-selected')).toBeTruthy()
      expect(wrapper.emitted('file-selected')?.[0]).toEqual([file])
    })

    it('displays validation error and does not emit when unsupported file type is selected', async () => {
      const file = new File(['exe content'], 'virus.exe', { type: 'application/x-msdownload' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false,
      })

      await fileInput.trigger('change')

      expect(wrapper.emitted('file-selected')).toBeFalsy()
      expect(wrapper.text()).toContain('Please upload an audio or video file')
    })

    it('displays validation error for text files', async () => {
      const file = new File(['text content'], 'document.txt', { type: 'text/plain' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false,
      })

      await fileInput.trigger('change')

      expect(wrapper.emitted('file-selected')).toBeFalsy()
      expect(wrapper.find('.validation-error').exists()).toBe(true)
    })
  })

  describe('Drag and Drop', () => {
    it('adds drag-over class when file is dragged over', async () => {
      const uploadZone = wrapper.find('.file-upload')

      await uploadZone.trigger('dragover', {
        preventDefault: vi.fn(),
      })

      expect(uploadZone.classes()).toContain('drag-over')
    })

    it('removes drag-over class when file is dragged away', async () => {
      const uploadZone = wrapper.find('.file-upload')

      await uploadZone.trigger('dragover', {
        preventDefault: vi.fn(),
      })
      expect(uploadZone.classes()).toContain('drag-over')

      await uploadZone.trigger('dragleave')
      expect(uploadZone.classes()).not.toContain('drag-over')
    })

    it('emits file-selected event when audio file is dropped', async () => {
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
      const uploadZone = wrapper.find('.file-upload')

      await uploadZone.trigger('drop', {
        preventDefault: vi.fn(),
        dataTransfer: {
          files: [file],
        },
      })

      expect(wrapper.emitted('file-selected')).toBeTruthy()
      expect(wrapper.emitted('file-selected')?.[0]).toEqual([file])
      expect(uploadZone.classes()).not.toContain('drag-over')
    })

    it('displays validation error when invalid file is dropped', async () => {
      const file = new File(['exe content'], 'virus.exe', { type: 'application/x-msdownload' })
      const uploadZone = wrapper.find('.file-upload')

      await uploadZone.trigger('drop', {
        preventDefault: vi.fn(),
        dataTransfer: {
          files: [file],
        },
      })

      expect(wrapper.emitted('file-selected')).toBeFalsy()
      expect(wrapper.find('.validation-error').exists()).toBe(true)
    })
  })

  describe('Selected File Display', () => {
    it('displays selected file name after file selection', async () => {
      const file = new File(['audio content'], 'my-podcast.mp3', { type: 'audio/mpeg' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false,
      })

      await fileInput.trigger('change')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Selected: my-podcast.mp3')
    })
  })

  describe('Format Validation', () => {
    const audioFormats = [
      { name: 'MP3', type: 'audio/mpeg', filename: 'test.mp3' },
      { name: 'WAV', type: 'audio/wav', filename: 'test.wav' },
      { name: 'M4A', type: 'audio/x-m4a', filename: 'test.m4a' },
    ]

    audioFormats.forEach(({ name, type, filename }) => {
      it(`accepts ${name} files`, async () => {
        const file = new File(['content'], filename, { type })
        const fileInput = wrapper.find('input[type="file"]')

        Object.defineProperty(fileInput.element, 'files', {
          value: [file],
          writable: false,
        })

        await fileInput.trigger('change')

        expect(wrapper.emitted('file-selected')).toBeTruthy()
        expect(wrapper.find('.validation-error').exists()).toBe(false)
      })
    })

    const videoFormats = [
      { name: 'MP4', type: 'video/mp4', filename: 'test.mp4' },
      { name: 'MOV', type: 'video/quicktime', filename: 'test.mov' },
    ]

    videoFormats.forEach(({ name, type, filename }) => {
      it(`accepts ${name} files`, async () => {
        const file = new File(['content'], filename, { type })
        const fileInput = wrapper.find('input[type="file"]')

        Object.defineProperty(fileInput.element, 'files', {
          value: [file],
          writable: false,
        })

        await fileInput.trigger('change')

        expect(wrapper.emitted('file-selected')).toBeTruthy()
        expect(wrapper.find('.validation-error').exists()).toBe(false)
      })
    })
  })
})
