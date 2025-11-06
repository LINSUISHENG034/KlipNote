<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'
import ProgressBar from '@/components/ProgressBar.vue'

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
  <div class="progress-view">
    <h1>Processing Your Transcription</h1>
    <p class="job-id">Job ID: {{ jobId }}</p>

    <ProgressBar :progress="store.progress" />

    <p class="status-message">{{ store.message }}</p>

    <div v-if="errorMessage || store.isFailed" class="error-section">
      <p class="error-message">{{ errorMessage || store.message }}</p>
      <button @click="handleRetry" class="retry-button">Retry with New File</button>
    </div>

    <p class="tip">
      You can safely navigate away from this page. Bookmark this URL to check progress later.
    </p>
  </div>
</template>

<style scoped>
.progress-view {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
}

.job-id {
  font-size: 0.9rem;
  color: #666;
  font-family: monospace;
}

.status-message {
  margin: 1.5rem 0;
  font-size: 1.1rem;
  color: #333;
  text-align: center;
}

.error-section {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #ffebee;
  border-radius: 4px;
}

.error-message {
  color: #c62828;
  margin-bottom: 1rem;
}

.retry-button {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background-color: #359268;
}

.tip {
  margin-top: 2rem;
  font-size: 0.9rem;
  color: #999;
  text-align: center;
}

@media (max-width: 768px) {
  .progress-view {
    padding: 1rem;
  }
}
</style>
