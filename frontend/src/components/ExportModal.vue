<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

interface Props {
  isOpen: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  export: [format: 'txt' | 'srt']
}>()

function handleExport(format: 'txt' | 'srt') {
  // TODO: Implement export functionality in Epic 2
  console.log(`Export as ${format.toUpperCase()} - functionality coming in Epic 2`)
  emit('export', format)
  emit('close')
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

        <!-- Export Options -->
        <div class="mt-6 flex flex-col space-y-3">
          <button
            @click="handleExport('txt')"
            class="w-full text-center px-4 py-2 text-primary font-medium rounded-full hover:bg-primary/10 transition-colors"
          >
            Export as .TXT
          </button>
          <button
            @click="handleExport('srt')"
            class="w-full text-center px-4 py-2 text-primary font-medium rounded-full hover:bg-primary/10 transition-colors"
          >
            Export as .SRT
          </button>
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
