<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'

const route = useRoute()
const router = useRouter()
const store = useTranscriptionStore()

const jobId = ref(route.params.job_id as string)
const pollingInterval = ref<number | null>(null)
const errorMessage = ref<string | null>(null)

// Start polling on mount
onMounted(() => {
  startPolling()
})

// Cleanup on unmount
onUnmounted(() => {
  stopPolling()
})

// Watch for completion - auto-navigate to results
watch(
  () => store.status,
  async (newStatus) => {
    if (newStatus === 'completed') {
      stopPolling()
      try {
        await store.fetchResult(jobId.value)
        router.push(`/results/${jobId.value}`)
      } catch (error) {
        errorMessage.value = 'Failed to load results. Please try again.'
      }
    } else if (newStatus === 'failed') {
      stopPolling()
      errorMessage.value = store.message || 'Transcription failed. Please try again.'
    }
  }
)

function startPolling() {
  // Poll immediately
  pollStatus()

  // Then poll every 3 seconds
  pollingInterval.value = window.setInterval(pollStatus, 3000)
}

function stopPolling() {
  if (pollingInterval.value !== null) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

async function pollStatus() {
  try {
    await store.fetchStatus(jobId.value)
  } catch (error) {
    console.error('Polling error:', error)
    // Continue polling on transient errors
  }
}

function handleRetry() {
  errorMessage.value = null
  store.reset()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen w-full flex flex-col bg-dark-bg">
    <!-- Top App Bar -->
    <div class="flex shrink-0 items-center p-4 justify-between">
      <button
        @click="router.push('/')"
        class="text-white flex size-10 shrink-0 items-center justify-center hover:bg-white/10 rounded-lg transition-colors"
      >
        <span class="material-symbols-outlined text-2xl">arrow_back</span>
      </button>
      <h1 class="text-white text-lg font-bold leading-tight tracking-tight">
        Transcribing Audio
      </h1>
      <div class="flex size-10 shrink-0 items-center"></div>
    </div>

    <!-- Main Content -->
    <div class="flex flex-1 flex-col items-center justify-center p-6 space-y-8">
      <!-- Audio Wave Animation Icon -->
      <div class="flex h-40 w-40 items-center justify-center rounded-full bg-primary/10">
        <div class="flex h-28 w-28 items-center justify-center rounded-full bg-primary/20">
          <span class="material-symbols-outlined text-5xl text-primary">graphic_eq</span>
        </div>
      </div>

      <!-- Progress Container with Glass-morphism -->
      <div class="w-full max-w-sm rounded-xl bg-white/5 p-6 shadow-lg backdrop-blur-sm">
        <!-- Status Message and Percentage -->
        <div class="flex gap-4 justify-between items-center mb-3">
          <p data-testid="status-message" class="text-slate-300 text-base font-medium leading-normal flex-1">
            {{ store.message || 'Processing...' }}
          </p>
          <p class="text-white text-base font-bold leading-normal">
            {{ store.progress }}%
          </p>
        </div>

        <!-- Progress Bar -->
        <div class="w-full rounded-full bg-slate-700 h-2">
          <div
            data-testid="progress-bar"
            class="h-2 rounded-full bg-primary transition-all duration-300"
            :style="`width: ${store.progress}%;`"
          ></div>
        </div>

        <!-- Job ID (small, monospace) -->
        <p data-testid="job-id" class="text-slate-500 text-xs font-mono mt-3 text-center">
          Job ID: {{ jobId }}
        </p>
      </div>

      <!-- Error State -->
      <div v-if="errorMessage || store.isFailed" class="w-full max-w-sm">
        <div data-testid="error-section" class="rounded-xl bg-red-900/30 border border-red-500/50 p-4">
          <p data-testid="error-message" class="text-red-300 text-sm mb-3 text-center">
            {{ errorMessage || store.message }}
          </p>
          <button
            @click="handleRetry"
            data-testid="retry-button"
            class="w-full flex items-center justify-center gap-2 rounded-lg bg-primary py-3 px-6 text-base font-bold text-white transition-all hover:bg-primary/90 active:scale-95"
          >
            <span class="material-symbols-outlined text-xl">refresh</span>
            <span>Retry with New File</span>
          </button>
        </div>
      </div>

      <!-- Tip (only show when processing) -->
      <p
        v-if="!errorMessage && !store.isFailed"
        class="text-slate-500 text-sm text-center max-w-sm"
      >
        You can safely navigate away from this page. Bookmark this URL to check progress later.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Minimal scoped styles - prefer Tailwind utility classes */
</style>
