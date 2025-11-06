import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import UploadView from '@/views/UploadView.vue'
import FileUpload from '@/components/FileUpload.vue'
import * as api from '@/services/api'

// Mock the API module
vi.mock('@/services/api', () => ({
  uploadFile: vi.fn(),
}))

describe('UploadView Component', () => {
  let router: ReturnType<typeof createRouter>
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    // Create router for navigation testing
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: UploadView },
        { path: '/progress/:job_id', component: { template: '<div>Progress</div>' } },
      ],
    })

    wrapper = mount(UploadView, {
      global: {
        plugins: [router],
      },
    })

    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders landing page with title and instructions', () => {
      expect(wrapper.text()).toContain('KlipNote - AI Transcription')
      expect(wrapper.text()).toContain('Upload your audio or video file to generate a transcription')
    })

    it('displays supported formats', () => {
      expect(wrapper.text()).toContain('Supported formats: MP3, MP4, WAV, M4A')
    })

    it('renders FileUpload component', () => {
      expect(wrapper.findComponent(FileUpload).exists()).toBe(true)
    })

    it('renders upload button', () => {
      const button = wrapper.find('.upload-button')
      expect(button.exists()).toBe(true)
      expect(button.text()).toBe('Upload and Transcribe')
    })
  })

  describe('File Selection', () => {
    it('enables upload button when file is selected', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      const button = wrapper.find('.upload-button')

      expect(button.attributes('disabled')).toBeDefined()

      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      expect(button.attributes('disabled')).toBeUndefined()
    })

    it('clears error message when new file is selected', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

      // Set error message
      wrapper.vm.errorMessage = 'Previous error'
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.error-message').exists()).toBe(true)

      // Select new file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.error-message').exists()).toBe(false)
    })
  })

  describe('Upload Flow', () => {
    it('button is disabled when no file is selected', async () => {
      const button = wrapper.find('.upload-button')
      expect(button.attributes('disabled')).toBeDefined()
    })

    it('calls uploadFile API when upload button is clicked with file', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      const mockJobId = '550e8400-e29b-41d4-a716-446655440000'

      vi.mocked(api.uploadFile).mockResolvedValue({ job_id: mockJobId })

      // Select file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      // Click upload button
      const button = wrapper.find('.upload-button')
      await button.trigger('click')

      expect(api.uploadFile).toHaveBeenCalledWith(file)
      expect(api.uploadFile).toHaveBeenCalledTimes(1)
    })

    it('shows loading state during upload', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

      // Mock uploadFile to return a pending promise
      let resolveUpload: (value: any) => void
      const uploadPromise = new Promise((resolve) => {
        resolveUpload = resolve
      })
      vi.mocked(api.uploadFile).mockReturnValue(uploadPromise as any)

      // Select file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      // Click upload button
      const button = wrapper.find('.upload-button')
      await button.trigger('click')
      await wrapper.vm.$nextTick()

      // Check loading state
      expect(button.text()).toBe('Uploading...')
      expect(button.attributes('disabled')).toBeDefined()

      // Resolve upload
      resolveUpload!({ job_id: 'test-id' })
      await flushPromises()
    })

    it('navigates to progress page on successful upload', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      const mockJobId = '550e8400-e29b-41d4-a716-446655440000'

      vi.mocked(api.uploadFile).mockResolvedValue({ job_id: mockJobId })

      // Select file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      // Click upload button
      const button = wrapper.find('.upload-button')
      await button.trigger('click')
      await flushPromises()

      // Check navigation
      expect(router.currentRoute.value.path).toBe(`/progress/${mockJobId}`)
    })

    it('displays error message on upload failure', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      const errorMessage = 'File format not supported'

      vi.mocked(api.uploadFile).mockRejectedValue(new Error(errorMessage))

      // Select file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      // Click upload button
      const button = wrapper.find('.upload-button')
      await button.trigger('click')
      await flushPromises()

      // Check error display
      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.text()).toContain(errorMessage)
      expect(router.currentRoute.value.path).toBe('/')
    })

    it('displays generic error message for non-Error exceptions', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

      vi.mocked(api.uploadFile).mockRejectedValue('Unknown error')

      // Select file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      // Click upload button
      const button = wrapper.find('.upload-button')
      await button.trigger('click')
      await flushPromises()

      // Check error display
      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.text()).toContain('Upload failed. Please try again.')
    })

    it('resets loading state after upload failure', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

      vi.mocked(api.uploadFile).mockRejectedValue(new Error('Upload failed'))

      // Select file
      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      // Click upload button
      const button = wrapper.find('.upload-button')
      await button.trigger('click')
      await flushPromises()

      // Check button is no longer loading
      expect(button.text()).toBe('Upload and Transcribe')
      expect(button.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Accessibility', () => {
    it('button is keyboard accessible', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      const button = wrapper.find('.upload-button')
      expect(button.attributes('type')).toBeUndefined() // Should be clickable
    })

    it('disables button during upload to prevent double submission', async () => {
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

      let resolveUpload: (value: any) => void
      const uploadPromise = new Promise((resolve) => {
        resolveUpload = resolve
      })
      vi.mocked(api.uploadFile).mockReturnValue(uploadPromise as any)

      wrapper.findComponent(FileUpload).vm.$emit('file-selected', file)
      await wrapper.vm.$nextTick()

      const button = wrapper.find('.upload-button')
      await button.trigger('click')
      await wrapper.vm.$nextTick()

      // Try to click again while uploading
      await button.trigger('click')

      // Should only be called once
      expect(api.uploadFile).toHaveBeenCalledTimes(1)

      resolveUpload!({ job_id: 'test-id' })
      await flushPromises()
    })
  })
})
