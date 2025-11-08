import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ExportModal from './ExportModal.vue'
import { useTranscriptionStore } from '@/stores/transcription'
import * as api from '@/services/api'

describe('ExportModal', () => {
  beforeEach(() => {
    // Create a fresh Pinia instance for each test
    setActivePinia(createPinia())
  })

  describe('UI Rendering (AC #1, #2)', () => {
    it('renders export button and format selection when open', () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      expect(wrapper.find('h3').text()).toBe('Export Transcript')
      expect(wrapper.find('button').text()).toContain('Export')
    })

    it('renders format selection radio buttons', () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      const radioButtons = wrapper.findAll('input[type="radio"]')

      expect(radioButtons.length).toBe(2)
      expect(radioButtons[0].attributes('value')).toBe('txt')
      expect(radioButtons[1].attributes('value')).toBe('srt')
    })

    it('defaults to TXT format (AC #2)', () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      const txtRadio = wrapper.find('input[value="txt"]')
      expect((txtRadio.element as HTMLInputElement).checked).toBe(true)
    })

    it('displays privacy notice from Story 2.5', () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      expect(wrapper.text()).toContain('Edited transcriptions may be retained to improve our AI model')
    })

    it('does not render when isOpen is false', () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: false },
      })

      expect(wrapper.find('.bg-zinc-800').exists()).toBe(false)
    })
  })

  describe('Export Functionality (AC #3, #4)', () => {
    it('calls exportTranscription API on button click', async () => {
      const exportSpy = vi.spyOn(api, 'exportTranscription')
      exportSpy.mockResolvedValue(new Blob(['test'], { type: 'text/plain' }))

      const store = useTranscriptionStore()
      store.jobId = 'test-job-123'
      store.segments = [
        { start: 0.5, end: 3.2, text: 'Test subtitle' },
      ]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button (contains "Export" text, not "Cancel")
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')

      expect(exportSpy).toHaveBeenCalledWith(
        'test-job-123',
        store.segments,
        'txt'
      )
    })

    it('calls API with SRT format when SRT is selected', async () => {
      const exportSpy = vi.spyOn(api, 'exportTranscription')
      exportSpy.mockResolvedValue(new Blob(['test'], { type: 'application/x-subrip' }))

      const store = useTranscriptionStore()
      store.jobId = 'test-job-456'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Select SRT format
      const srtRadio = wrapper.find('input[value="srt"]')
      await srtRadio.setValue(true)

      // Find the Export button
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(exportSpy).toHaveBeenCalledWith('test-job-456', expect.any(Array), 'srt')
    })
  })

  describe('Loading State (AC #5)', () => {
    it('shows loading state during export', async () => {
      vi.spyOn(api, 'exportTranscription').mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve(new Blob()), 100))
      )

      const store = useTranscriptionStore()
      store.jobId = 'test-job-123'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')

      expect(wrapper.text()).toContain('Exporting...')
      expect((exportButton!.element as HTMLButtonElement).disabled).toBe(true)
    })

    it('disables radio buttons while exporting', async () => {
      vi.spyOn(api, 'exportTranscription').mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve(new Blob()), 100))
      )

      const store = useTranscriptionStore()
      store.jobId = 'test-job-123'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')

      const radioButtons = wrapper.findAll('input[type="radio"]')
      radioButtons.forEach(radio => {
        expect((radio.element as HTMLInputElement).disabled).toBe(true)
      })
    })
  })

  describe('Error Handling (AC #6)', () => {
    it('displays error message on API failure', async () => {
      vi.spyOn(api, 'exportTranscription').mockRejectedValue(
        new Error('Export failed: Server error. Please try again.')
      )

      const store = useTranscriptionStore()
      store.jobId = 'test-job-123'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Export failed: Server error. Please try again.')
    })

    it('displays error for 404 response', async () => {
      vi.spyOn(api, 'exportTranscription').mockRejectedValue(
        new Error('Export failed: Transcription not found.')
      )

      const store = useTranscriptionStore()
      store.jobId = 'invalid-job'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Export failed: Transcription not found.')
    })

    it('displays error when no transcription available', async () => {
      const store = useTranscriptionStore()
      store.jobId = null
      store.segments = []

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const buttons = wrapper.findAll('button')
      const exportButton = buttons.find(btn => btn.text().includes('Export'))

      await exportButton!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('No transcription available to export.')
    })
  })

  describe('Multiple Exports (AC #7)', () => {
    it('allows multiple sequential exports', async () => {
      const exportSpy = vi.spyOn(api, 'exportTranscription')
      exportSpy.mockResolvedValue(new Blob(['test'], { type: 'text/plain' }))

      const store = useTranscriptionStore()
      store.jobId = 'test-job-123'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const getExportButton = () => wrapper.findAll('button').find(btn => btn.text().includes('Export'))

      // First export (TXT)
      await getExportButton()!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(exportSpy).toHaveBeenCalledTimes(1)
      expect(exportSpy).toHaveBeenCalledWith('test-job-123', expect.any(Array), 'txt')

      // Change format to SRT
      const srtRadio = wrapper.find('input[value="srt"]')
      await srtRadio.setValue(true)

      // Second export (SRT)
      await getExportButton()!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(exportSpy).toHaveBeenCalledTimes(2)
      expect(exportSpy).toHaveBeenLastCalledWith('test-job-123', expect.any(Array), 'srt')
    })

    it('resets error state when starting new export', async () => {
      const exportSpy = vi.spyOn(api, 'exportTranscription')

      // First call: error
      exportSpy.mockRejectedValueOnce(new Error('Export failed: Server error. Please try again.'))

      const store = useTranscriptionStore()
      store.jobId = 'test-job-123'
      store.segments = [{ start: 0, end: 1, text: 'Test' }]

      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Export button
      const getExportButton = () => wrapper.findAll('button').find(btn => btn.text().includes('Export'))

      // First export (fails)
      await getExportButton()!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Export failed: Server error')

      // Second call: success
      exportSpy.mockResolvedValueOnce(new Blob(['test'], { type: 'text/plain' }))

      // Second export (succeeds)
      await getExportButton()!.trigger('click')
      await wrapper.vm.$nextTick()

      // Error should be cleared
      expect(wrapper.text()).not.toContain('Export failed: Server error')
    })
  })

  describe('Modal Behavior', () => {
    it('emits close event when cancel is clicked', async () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      // Find the Cancel button (contains "Cancel" text)
      const buttons = wrapper.findAll('button')
      const cancelButton = buttons.find(btn => btn.text().includes('Cancel'))

      await cancelButton!.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('emits close event when overlay is clicked', async () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      const overlay = wrapper.find('.fixed.inset-0')
      await overlay.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('does not close when clicking inside dialog', async () => {
      const wrapper = mount(ExportModal, {
        props: { isOpen: true },
      })

      const dialog = wrapper.find('.bg-zinc-800')
      await dialog.trigger('click')

      expect(wrapper.emitted('close')).toBeFalsy()
    })
  })
})
