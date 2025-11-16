/**
 * Story 4.1b Integration Tests: Frontend Model Selection
 * Tests the complete flow from model selection UI → upload API call → backend processing
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import UploadView from '@/views/UploadView.vue'
import { useTranscriptionStore } from '@/stores/transcription'
import * as api from '@/services/api'

describe('Story 4.1b: Model Selection Integration', () => {
  let router: ReturnType<typeof createRouter>
  let wrapper: ReturnType<typeof mount>
  let store: ReturnType<typeof useTranscriptionStore>

  beforeEach(async () => {
    // Setup router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: UploadView },
        { path: '/progress/:jobId', name: 'progress', component: { template: '<div>Progress</div>' } }
      ]
    })

    // Setup Pinia
    setActivePinia(createPinia())
    store = useTranscriptionStore()

    // Clear localStorage
    localStorage.clear()

    // Mount UploadView
    wrapper = mount(UploadView, {
      global: {
        plugins: [router]
      }
    })

    await router.isReady()
  })

  afterEach(() => {
    wrapper.unmount()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  describe('AC#5: Upload API Integration', () => {
    it('passes selected model (BELLE-2) to upload API when file is uploaded', async () => {
      // Mock uploadFile API
      const uploadFileSpy = vi.spyOn(api, 'uploadFile').mockResolvedValue({ job_id: 'test-job-id' })

      // Ensure BELLE-2 is selected (default)
      expect(store.selectedModel).toBe('belle2')

      // Select and upload a file
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false
      })

      await fileInput.trigger('change')
      await wrapper.vm.$nextTick()

      // Verify uploadFile called with model parameter
      expect(uploadFileSpy).toHaveBeenCalledWith(file, 'belle2')
    })

    it('passes selected model (WhisperX) to upload API when file is uploaded', async () => {
      // Mock uploadFile API
      const uploadFileSpy = vi.spyOn(api, 'uploadFile').mockResolvedValue({ job_id: 'test-job-id' })

      // Change model to WhisperX
      store.setSelectedModel('whisperx')
      await wrapper.vm.$nextTick()

      expect(store.selectedModel).toBe('whisperx')

      // Select and upload a file
      const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false
      })

      await fileInput.trigger('change')
      await wrapper.vm.$nextTick()

      // Verify uploadFile called with WhisperX model
      expect(uploadFileSpy).toHaveBeenCalledWith(file, 'whisperx')
    })

    it('preserves model selection across page navigation', async () => {
      // Select WhisperX
      store.setSelectedModel('whisperx')
      await wrapper.vm.$nextTick()

      // Simulate navigation away and back
      await router.push('/progress/some-job')
      await router.push('/')
      await wrapper.vm.$nextTick()

      // Model should still be WhisperX (persisted in localStorage)
      expect(store.selectedModel).toBe('whisperx')
    })
  })

  describe('AC#2: UI Integration with UploadView', () => {
    it('renders ModelSelector component in UploadView', () => {
      // ModelSelector should be present in UploadView
      expect(wrapper.find('.model-selector').exists()).toBe(true)
    })

    it('model selector is visible before upload button', () => {
      const modelSelector = wrapper.find('.model-selector')
      const uploadButton = wrapper.find('[data-testid="upload-button"]')

      expect(modelSelector.exists()).toBe(true)
      expect(uploadButton.exists()).toBe(true)

      // ModelSelector should appear before upload button in DOM order
      const modelSelectorEl = modelSelector.element
      const uploadButtonEl = uploadButton.element

      const comparePosition = modelSelectorEl.compareDocumentPosition(uploadButtonEl)
      expect(comparePosition & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    })
  })

  describe('AC#6: localStorage Persistence Integration', () => {
    it('restores model selection from localStorage on page reload', async () => {
      // Set localStorage before component mount
      localStorage.setItem('klipnote_selected_model', 'whisperx')

      // Remount UploadView (simulating page reload)
      wrapper.unmount()
      wrapper = mount(UploadView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()

      // Model should be restored to WhisperX
      expect(store.selectedModel).toBe('whisperx')
    })

    it('defaults to BELLE-2 when localStorage is empty', async () => {
      // Ensure localStorage is cleared
      localStorage.clear()

      // Remount UploadView
      wrapper.unmount()
      wrapper = mount(UploadView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()

      // Should default to BELLE-2
      expect(store.selectedModel).toBe('belle2')
    })
  })

  describe('End-to-End User Flow', () => {
    it('completes full user flow: select model → upload file → API called with correct model', async () => {
      // Mock uploadFile API
      const uploadFileSpy = vi.spyOn(api, 'uploadFile').mockResolvedValue({ job_id: 'test-job-123' })
      const routerPushSpy = vi.spyOn(router, 'push')

      // Step 1: User selects WhisperX model
      store.setSelectedModel('whisperx')
      await wrapper.vm.$nextTick()

      // Step 2: User uploads a file
      const file = new File(['test audio'], 'meeting.mp3', { type: 'audio/mpeg' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false
      })

      await fileInput.trigger('change')
      await wrapper.vm.$nextTick()

      // Step 3: Verify API called with correct model
      expect(uploadFileSpy).toHaveBeenCalledWith(file, 'whisperx')
      expect(uploadFileSpy).toHaveBeenCalledTimes(1)

      // Step 4: Verify navigation to progress page
      await vi.waitFor(() => {
        expect(routerPushSpy).toHaveBeenCalledWith('/progress/test-job-123')
      })
    })

    it('model selection persists after failed upload attempt', async () => {
      // Mock uploadFile to fail
      vi.spyOn(api, 'uploadFile').mockRejectedValue(new Error('Upload failed'))

      // Select WhisperX
      store.setSelectedModel('whisperx')
      await wrapper.vm.$nextTick()

      // Attempt upload
      const file = new File(['test'], 'test.mp3', { type: 'audio/mpeg' })
      const fileInput = wrapper.find('input[type="file"]')

      Object.defineProperty(fileInput.element, 'files', {
        value: [file],
        writable: false
      })

      await fileInput.trigger('change')
      await wrapper.vm.$nextTick()

      // Wait for error to be handled
      await vi.waitFor(() => {
        expect(wrapper.vm.errorMessage).toBeTruthy()
      })

      // Model selection should still be WhisperX
      expect(store.selectedModel).toBe('whisperx')
    })
  })
})
