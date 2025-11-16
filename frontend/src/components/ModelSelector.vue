<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()

// Model options configuration
const modelOptions = [
  {
    value: 'belle2',
    label: 'BELLE-2 (Mandarin-optimized)',
    description: 'Optimized for Chinese/Mandarin transcription with superior accuracy and natural segment lengths. Best choice for Chinese meetings and content.'
  },
  {
    value: 'whisperx',
    label: 'WhisperX (Multi-language)',
    description: 'Multi-language support with forced alignment for precise word-level timestamps. Suitable for English and other languages.'
  }
]

// Load model from localStorage on mount
onMounted(() => {
  store.loadModelFromLocalStorage()
})

// Watch for model changes and save to localStorage
watch(() => store.selectedModel, () => {
  store.saveModelToLocalStorage()
})

// Handle model selection change
function handleModelChange(value: string) {
  store.setSelectedModel(value as 'belle2' | 'whisperx')
}
</script>

<template>
  <div class="model-selector">
    <fieldset class="flex flex-col gap-3">
      <legend class="text-base font-semibold text-slate-200 mb-2">
        Transcription Model
      </legend>

      <div class="flex flex-col gap-2">
        <div
          v-for="option in modelOptions"
          :key="option.value"
          class="model-option group relative"
        >
          <label
            :for="`model-${option.value}`"
            :class="[
              'flex items-start gap-3 p-4 rounded-lg border-2 transition-all cursor-pointer',
              'min-h-[44px]', // Touch target size (AC#8)
              store.selectedModel === option.value
                ? 'border-primary bg-primary/10'
                : 'border-slate-600/50 bg-slate-800/30 hover:border-slate-500'
            ]"
          >
            <input
              :id="`model-${option.value}`"
              type="radio"
              :value="option.value"
              :checked="store.selectedModel === option.value"
              @change="handleModelChange(option.value)"
              class="mt-0.5 h-4 w-4 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-0 focus:ring-offset-dark-bg"
            />

            <div class="flex-1">
              <div class="text-sm font-medium text-slate-100">
                {{ option.label }}
              </div>

              <!-- Tooltip/Help text (AC#7) -->
              <div class="mt-1 text-xs text-slate-400 leading-relaxed">
                {{ option.description }}
              </div>
            </div>
          </label>
        </div>
      </div>
    </fieldset>
  </div>
</template>

<style scoped>
/* Ensure radio inputs are accessible */
input[type="radio"] {
  cursor: pointer;
}

input[type="radio"]:focus {
  outline: 2px solid #00c4a7;  /* primary color */
  outline-offset: 2px;
}

/* Responsive design handled by Tailwind classes (AC#8) */
</style>
