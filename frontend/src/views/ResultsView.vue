<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'
import SubtitleList from '@/components/SubtitleList.vue'

const route = useRoute()
const router = useRouter()
const store = useTranscriptionStore()

const jobId = ref(route.params.job_id as string)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

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
</script>

<template>
  <div class="results-view">
    <!-- Top App Bar -->
    <div class="top-bar">
      <div class="top-bar-content">
        <button @click="handleBack" class="icon-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <h2 class="top-bar-title">Transcription Results</h2>
        <div class="icon-button-placeholder"></div>
      </div>
    </div>

    <!-- Content -->
    <div class="content">
      <!-- Loading State -->
      <div v-if="isLoading" class="state-container">
        <div class="spinner"></div>
        <p class="state-message">Loading transcription...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="errorMessage" class="state-container">
        <p class="error-message">{{ errorMessage }}</p>
        <button @click="handleRetry" class="retry-button">Retry</button>
      </div>

      <!-- Results Display -->
      <SubtitleList v-else-if="store.segments.length > 0" :segments="store.segments" />

      <!-- Empty State -->
      <div v-else class="state-container">
        <p class="state-message">No transcription results available.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.results-view {
  min-height: 100vh;
  background: #101922;
  color: #e4e4e7;
}

/* Top App Bar */
.top-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(16, 25, 34, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(63, 63, 70, 0.3);
}

.top-bar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  max-width: 900px;
  margin: 0 auto;
}

.icon-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: transparent;
  border: none;
  color: #e4e4e7;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.icon-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.icon-button-placeholder {
  width: 48px;
  height: 48px;
}

.top-bar-title {
  flex: 1;
  text-align: center;
  font-size: 1.125rem;
  font-weight: 700;
  color: #e4e4e7;
  margin: 0;
}

/* Content */
.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 1rem;
  padding-bottom: 7rem;
}

/* State Containers */
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
}

.state-message {
  color: #a1a1aa;
  font-size: 1rem;
  margin: 0;
}

/* Spinner */
.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(19, 127, 236, 0.2);
  border-top-color: #137fec;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Error State */
.error-message {
  color: #ef4444;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.retry-button {
  padding: 0.75rem 2rem;
  background: #137fec;
  color: white;
  border: none;
  border-radius: 9999px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background: #0e6ac9;
}

/* Responsive */
@media (max-width: 768px) {
  .content {
    padding: 0.75rem;
    padding-bottom: 7rem;
  }

  .top-bar-title {
    font-size: 1rem;
  }
}
</style>
