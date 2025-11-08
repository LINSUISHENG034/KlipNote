<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'
import { exportTranscription } from '@/services/api'

interface Props {
  isOpen: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

const store = useTranscriptionStore()

// State
const selectedFormat = ref<'srt' | 'txt'>('txt')  // Default: TXT for LLM use (AC #2)
const isExporting = ref(false)
const error = ref<string | null>(null)

/**
 * Trigger browser download for Blob content
 * Task 3: Browser download trigger using Blob API
 *
 * @param blob - File content as Blob
 * @param filename - Download filename
 */
function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Handle export button click
 * Tasks 4-6: Integration with Pinia store, error handling, multiple exports
 * Calls backend API and triggers browser download
 */
async function handleExport() {
  if (!store.jobId || store.segments.length === 0) {
    error.value = 'No transcription available to export.'
    return
  }

  // Reset previous error (Task 6: Support multiple exports)
  error.value = null
  isExporting.value = true

  try {
    const blob = await exportTranscription(
      store.jobId,
      store.segments,
      selectedFormat.value
    )

    const filename = `transcript-${store.jobId}.${selectedFormat.value}`
    triggerDownload(blob, filename)

    // Success - file downloaded
    // Do NOT close modal - allow sequential exports (AC #7, Task 6)
  } catch (err) {
    // Task 5: Display user-friendly error message
    if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = 'Export failed: Unknown error occurred.'
    }
  } finally {
    isExporting.value = false
  }
}

function handleCancel() {
  emit('close')
}

function handleOverlayClick(event: MouseEvent) {
  // Close only if clicking the overlay itself, not the dialog
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

function handleEscKey(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.isOpen) {
    emit('close')
  }
}

// Add/remove ESC key listener
onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
})
</script>

<template>
  <!-- Modal Overlay -->
  <Transition name="modal">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-30 flex items-center justify-center bg-black/50 p-4"
      @click="handleOverlayClick"
    >
      <!-- Modal Dialog -->
      <div
        class="bg-zinc-800 rounded-xl w-full max-w-sm p-6 shadow-2xl backdrop-blur-sm"
        @click.stop
      >
        <!-- Title -->
        <h3 class="text-xl font-semibold text-white">Export Transcript</h3>

        <!-- Subtitle -->
        <p class="mt-2 text-sm text-zinc-400">
          Choose a format to download.
        </p>

        <!-- Privacy Notice (Story 2.5) -->
        <div class="mt-4 px-3 py-2 bg-zinc-700/30 border border-zinc-600/30 rounded-lg">
          <p class="text-xs text-zinc-400 leading-relaxed">
            <span class="material-symbols-outlined text-sm align-middle mr-1" style="font-size: 14px;">info</span>
            Note: Edited transcriptions may be retained to improve our AI model.
          </p>
        </div>

        <!-- Task 2: Format Selection UI (AC #2) -->
        <div class="mt-6">
          <label class="block text-sm font-medium text-zinc-300 mb-3">Export Format:</label>
          <div class="space-y-2">
            <label class="flex items-center p-3 bg-zinc-700/30 border border-zinc-600/30 rounded-lg cursor-pointer hover:bg-zinc-700/50 transition-colors">
              <input
                type="radio"
                value="txt"
                v-model="selectedFormat"
                :disabled="isExporting"
                class="w-4 h-4 text-primary bg-zinc-700 border-zinc-500 focus:ring-primary focus:ring-2"
              />
              <span class="ml-3 text-sm text-zinc-200">
                <span class="font-medium">TXT</span>
                <span class="text-zinc-400 ml-1">(Plain text for LLMs)</span>
              </span>
            </label>
            <label class="flex items-center p-3 bg-zinc-700/30 border border-zinc-600/30 rounded-lg cursor-pointer hover:bg-zinc-700/50 transition-colors">
              <input
                type="radio"
                value="srt"
                v-model="selectedFormat"
                :disabled="isExporting"
                class="w-4 h-4 text-primary bg-zinc-700 border-zinc-500 focus:ring-primary focus:ring-2"
              />
              <span class="ml-3 text-sm text-zinc-200">
                <span class="font-medium">SRT</span>
                <span class="text-zinc-400 ml-1">(Subtitle format)</span>
              </span>
            </label>
          </div>
        </div>

        <!-- Task 2: Export Button (AC #1, #3) -->
        <div class="mt-6">
          <button
            @click="handleExport"
            :disabled="isExporting"
            class="w-full px-4 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <!-- Task 2: Loading state (AC #5) -->
            <span v-if="!isExporting">Export</span>
            <span v-else class="flex items-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Exporting...
            </span>
          </button>
        </div>

        <!-- Task 5: Error Display (AC #6) -->
        <div v-if="error" class="mt-4 p-3 bg-red-900/20 border border-red-700/50 rounded-lg">
          <div class="flex items-start">
            <span class="material-symbols-outlined text-red-400 mr-2" style="font-size: 18px;">error</span>
            <p class="text-sm text-red-400">{{ error }}</p>
          </div>
        </div>

        <!-- Cancel Button -->
        <div class="mt-4 flex justify-end">
          <button
            @click="handleCancel"
            class="px-4 py-2 text-primary font-medium rounded-full hover:bg-primary/10 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-zinc-800,
.modal-leave-active .bg-zinc-800 {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from .bg-zinc-800,
.modal-leave-to .bg-zinc-800 {
  transform: scale(0.95);
  opacity: 0;
}
</style>
