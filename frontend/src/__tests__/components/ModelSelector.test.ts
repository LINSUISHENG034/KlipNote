import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ModelSelector from '@/components/ModelSelector.vue'
import { useTranscriptionStore } from '@/stores/transcription'

describe('ModelSelector Component', () => {
  let wrapper: ReturnType<typeof mount>
  let store: ReturnType<typeof useTranscriptionStore>

  beforeEach(() => {
    // Setup Pinia
    setActivePinia(createPinia())
    store = useTranscriptionStore()

    // Clear localStorage before each test
    localStorage.clear()

    // Mount component
    wrapper = mount(ModelSelector)
  })

  afterEach(() => {
    wrapper.unmount()
    localStorage.clear()
  })

  describe('AC#1: Rendering', () => {
    it('renders model selector with fieldset legend', () => {
      expect(wrapper.find('fieldset').exists()).toBe(true)
      expect(wrapper.find('legend').text()).toBe('Transcription Model')
    })

    it('renders two model options (BELLE-2 and WhisperX)', () => {
      const radioInputs = wrapper.findAll('input[type="radio"]')
      expect(radioInputs).toHaveLength(2)

      const labels = wrapper.findAll('label')
      expect(labels.length).toBeGreaterThanOrEqual(2)

      const labelTexts = wrapper.text()
      expect(labelTexts).toContain('BELLE-2')
      expect(labelTexts).toContain('WhisperX')
    })

    it('displays model-specific labels and descriptions (AC#7)', () => {
      const componentText = wrapper.text()

      // BELLE-2 label and description
      expect(componentText).toContain('BELLE-2 (Mandarin-optimized)')
      expect(componentText).toContain('Optimized for Chinese/Mandarin')

      // WhisperX label and description
      expect(componentText).toContain('WhisperX (Multi-language)')
      expect(componentText).toContain('Multi-language support')
    })
  })

  describe('AC#3: Default Selection', () => {
    it('selects BELLE-2 by default when no localStorage value exists', () => {
      expect(store.selectedModel).toBe('belle2')

      const belle2Radio = wrapper.find('input[value="belle2"]')
      expect((belle2Radio.element as HTMLInputElement).checked).toBe(true)
    })

    it('applies visual styling to default selected option', () => {
      const belle2Label = wrapper.find('label[for="model-belle2"]')
      expect(belle2Label.classes()).toContain('border-primary')
    })
  })

  describe('AC#4: Model Selection', () => {
    it('updates store when BELLE-2 radio is selected', async () => {
      const belle2Radio = wrapper.find('input[value="belle2"]')
      await belle2Radio.trigger('change')

      expect(store.selectedModel).toBe('belle2')
    })

    it('updates store when WhisperX radio is selected', async () => {
      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      await whisperxRadio.trigger('change')

      expect(store.selectedModel).toBe('whisperx')
    })

    it('applies selected styling when WhisperX is chosen', async () => {
      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      await whisperxRadio.trigger('change')
      await wrapper.vm.$nextTick()

      const whisperxLabel = wrapper.find('label[for="model-whisperx"]')
      expect(whisperxLabel.classes()).toContain('border-primary')
    })

    it('removes selected styling from previously selected model', async () => {
      // Start with BELLE-2 selected (default)
      const belle2Label = wrapper.find('label[for="model-belle2"]')
      expect(belle2Label.classes()).toContain('border-primary')

      // Select WhisperX
      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      await whisperxRadio.trigger('change')
      await wrapper.vm.$nextTick()

      // BELLE-2 should no longer have primary border
      expect(belle2Label.classes()).not.toContain('border-primary')
    })
  })

  describe('AC#6: localStorage Persistence', () => {
    it('saves model selection to localStorage when changed', async () => {
      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      await whisperxRadio.trigger('change')

      expect(localStorage.getItem('klipnote_selected_model')).toBe('whisperx')
    })

    it('loads model from localStorage on component mount', async () => {
      // Set localStorage before mounting
      localStorage.setItem('klipnote_selected_model', 'whisperx')

      // Remount component
      wrapper.unmount()
      wrapper = mount(ModelSelector)
      await wrapper.vm.$nextTick()  // Wait for onMounted to complete

      expect(store.selectedModel).toBe('whisperx')

      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      expect((whisperxRadio.element as HTMLInputElement).checked).toBe(true)
    })

    it('falls back to default (BELLE-2) when localStorage has invalid value', () => {
      localStorage.setItem('klipnote_selected_model', 'invalid-model')

      // Remount component to trigger loadModelFromLocalStorage
      wrapper.unmount()
      wrapper = mount(ModelSelector)

      expect(store.selectedModel).toBe('belle2')
      expect(localStorage.getItem('klipnote_selected_model')).toBeNull()
    })

    it('persists selection across component unmount/remount cycles', async () => {
      // Select WhisperX
      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      await whisperxRadio.trigger('change')

      // Unmount and remount
      wrapper.unmount()
      wrapper = mount(ModelSelector)

      // Should still be WhisperX
      expect(store.selectedModel).toBe('whisperx')
      const whisperxRadioAfterRemount = wrapper.find('input[value="whisperx"]')
      expect((whisperxRadioAfterRemount.element as HTMLInputElement).checked).toBe(true)
    })
  })

  describe('AC#8: Accessibility and Responsive Design', () => {
    it('has accessible fieldset/legend structure', () => {
      const fieldset = wrapper.find('fieldset')
      const legend = wrapper.find('legend')

      expect(fieldset.exists()).toBe(true)
      expect(legend.exists()).toBe(true)
      expect(legend.text()).toBeTruthy()
    })

    it('has unique id attributes for radio inputs', () => {
      const belle2Radio = wrapper.find('#model-belle2')
      const whisperxRadio = wrapper.find('#model-whisperx')

      expect(belle2Radio.exists()).toBe(true)
      expect(whisperxRadio.exists()).toBe(true)
    })

    it('associates labels with radio inputs via for attribute', () => {
      const belle2Label = wrapper.find('label[for="model-belle2"]')
      const whisperxLabel = wrapper.find('label[for="model-whisperx"]')

      expect(belle2Label.exists()).toBe(true)
      expect(whisperxLabel.exists()).toBe(true)
    })

    it('has minimum touch target size (44px) for mobile accessibility', () => {
      const labels = wrapper.findAll('label')

      labels.forEach(label => {
        // Check for min-h-[44px] class
        expect(label.classes().join(' ')).toContain('min-h-[44px]')
      })
    })

    it('supports keyboard navigation (radio inputs are focusable)', () => {
      const belle2Radio = wrapper.find('input[value="belle2"]')
      const whisperxRadio = wrapper.find('input[value="whisperx"]')

      // Radio inputs should have tabindex implicitly (not -1)
      expect(belle2Radio.attributes('tabindex')).not.toBe('-1')
      expect(whisperxRadio.attributes('tabindex')).not.toBe('-1')
    })
  })

  describe('AC#9: Integration with Upload Flow', () => {
    it('updates store.selectedModel state used by upload API', async () => {
      // Verify initial state
      expect(store.selectedModel).toBe('belle2')

      // Change to WhisperX
      const whisperxRadio = wrapper.find('input[value="whisperx"]')
      await whisperxRadio.trigger('change')

      // Verify store updated (this value will be used by uploadFile API call)
      expect(store.selectedModel).toBe('whisperx')
    })
  })
})
