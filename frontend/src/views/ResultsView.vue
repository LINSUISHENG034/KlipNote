<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'
import SubtitleList from '@/components/SubtitleList.vue'
import ExportModal from '@/components/ExportModal.vue'

const route = useRoute()
const router = useRouter()
const store = useTranscriptionStore()

const jobId = ref(route.params.job_id as string)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const isExportModalOpen = ref(false)

onMounted(async () => {
  // Check if segments already loaded (from Story 1.6 auto-nav)
  if (store.segments.length === 0) {
    isLoading.value = true
    try {
      await store.fetchResult(jobId.value)
    } catch (error) {
      errorMessage.value = 'Failed to load transcription results. Please try again.'
    } finally {
      isLoading.value = false
    }
  }
})

async function handleRetry() {
  errorMessage.value = null
  isLoading.value = true
  try {
    await store.fetchResult(jobId.value)
  } catch (error) {
    errorMessage.value = 'Failed to load transcription results. Please try again.'
  } finally {
    isLoading.value = false
  }
}

function handleBack() {
  router.push('/')
}

function handleExport() {
  isExportModalOpen.value = true
}

function handleCloseModal() {
  isExportModalOpen.value = false
}

function handleExportFormat(format: 'txt' | 'srt') {
  // TODO: Implement actual export logic in Epic 2
  console.log(`Exporting as ${format.toUpperCase()} - functionality coming in Epic 2`)
}
</script>

<template>
  <div class="min-h-screen w-full flex flex-col bg-dark-bg">
    <!-- Top App Bar -->
    <div class="sticky top-0 z-10 bg-dark-bg/80 backdrop-blur-sm border-b border-zinc-700/30">
      <div class="flex items-center p-4 pb-2 justify-between">
        <button
          @click="handleBack"
          class="flex size-12 shrink-0 items-center justify-center text-white hover:bg-white/10 rounded-lg transition-colors"
        >
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <h2 data-testid="top-bar-title" class="text-white text-lg font-bold leading-tight tracking-tight flex-1 text-center">
          KlipNote Demo
        </h2>
        <div class="flex w-12 items-center justify-end">
          <button data-testid="menu-button" class="flex items-center justify-center h-12 bg-transparent text-white hover:bg-white/10 rounded-lg transition-colors p-2">
            <span class="material-symbols-outlined">more_vert</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" data-testid="loading-state" class="flex flex-1 flex-col items-center justify-center p-6">
      <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-4"></div>
      <p class="text-slate-400 text-base">Loading transcription...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" data-testid="error-state" class="flex flex-1 flex-col items-center justify-center p-6">
      <div class="w-full max-w-md rounded-xl bg-red-900/30 border border-red-500/50 p-6">
        <p data-testid="error-message" class="text-red-300 text-sm mb-4 text-center">{{ errorMessage }}</p>
        <button
          @click="handleRetry"
          data-testid="retry-button"
          class="w-full flex items-center justify-center gap-2 rounded-lg bg-primary py-3 px-6 text-base font-bold text-white transition-all hover:bg-primary/90 active:scale-95"
        >
          <span class="material-symbols-outlined text-xl">refresh</span>
          <span>Retry</span>
        </button>
      </div>
    </div>

    <!-- Results Display -->
    <div v-else-if="store.segments.length > 0" class="flex-1 pb-24">
      <!-- Media Player Placeholder -->
      <div class="sticky top-[72px] z-10 bg-dark-bg px-4 pt-2 pb-4">
        <!-- 16:9 Video Container -->
        <div class="relative flex w-full flex-col items-center justify-center rounded-xl bg-zinc-800 aspect-video overflow-hidden">
          <!-- Placeholder Content -->
          <div class="flex flex-col items-center justify-center gap-3">
            <span class="material-symbols-outlined text-6xl text-zinc-600">videocam_off</span>
            <p class="text-zinc-400 text-sm font-medium">Media Player (Coming in Epic 2)</p>
          </div>

          <!-- Placeholder Progress Bar (bottom overlay) -->
          <div class="absolute inset-x-0 bottom-0 px-4 py-3 bg-gradient-to-t from-black/60 to-transparent opacity-50">
            <div class="flex items-center justify-center gap-2">
              <div class="h-1 flex-1 rounded-full bg-primary"></div>
              <div class="relative">
                <div class="absolute -left-2 -top-2 size-4 rounded-full bg-white shadow"></div>
              </div>
              <div class="h-1 flex-1 rounded-full bg-white/40"></div>
            </div>
            <div class="flex items-center justify-between mt-1">
              <p class="text-white text-xs font-medium">0:00</p>
              <p class="text-white text-xs font-medium">0:00</p>
            </div>
          </div>
        </div>

        <!-- Placeholder Controls -->
        <div class="mt-4 flex items-center justify-evenly text-white opacity-50">
          <button disabled class="flex size-12 items-center justify-center rounded-full cursor-not-allowed">
            <span class="material-symbols-outlined text-3xl">replay_10</span>
          </button>
          <button disabled class="flex size-16 items-center justify-center rounded-full bg-primary/50 text-white shadow-lg cursor-not-allowed">
            <span class="material-symbols-outlined text-5xl">play_arrow</span>
          </button>
          <button disabled class="flex size-12 items-center justify-center rounded-full cursor-not-allowed">
            <span class="material-symbols-outlined text-3xl">forward_10</span>
          </button>
        </div>
      </div>

      <!-- Subtitle List -->
      <div class="px-4 space-y-3 pb-4">
        <SubtitleList :segments="store.segments" />
      </div>

      <!-- Bottom Fixed Export Button -->
      <div class="fixed bottom-0 left-0 right-0 z-20 h-20 bg-dark-bg/80 backdrop-blur-sm border-t border-zinc-700/50 flex items-center justify-end px-4">
        <button
          @click="handleExport"
          data-testid="export-button"
          class="flex items-center justify-center gap-2 h-12 min-w-[56px] px-6 bg-primary text-white rounded-full shadow-lg hover:bg-primary/90 transition-all text-base font-medium"
        >
          <span class="material-symbols-outlined">ios_share</span>
          <span>Export</span>
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else data-testid="empty-state" class="flex flex-1 flex-col items-center justify-center p-6">
      <p class="text-slate-400 text-base">No transcription results available.</p>
    </div>

    <!-- Export Modal -->
    <ExportModal
      :is-open="isExportModalOpen"
      @close="handleCloseModal"
      @export="handleExportFormat"
    />
  </div>
</template>

<style scoped>
/* Minimal scoped styles - prefer Tailwind utility classes */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
