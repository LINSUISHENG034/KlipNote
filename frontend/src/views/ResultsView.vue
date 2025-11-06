<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'

const route = useRoute()
const store = useTranscriptionStore()
const jobId = route.params.job_id as string
</script>

<template>
  <div class="results-view">
    <div class="placeholder-card">
      <div class="success-icon">✅</div>
      <h1>Transcription Complete!</h1>
      <p class="message">Your audio has been successfully transcribed.</p>

      <div class="job-info">
        <h2>Job ID:</h2>
        <code class="job-id">{{ jobId }}</code>
      </div>

      <div class="segments-preview" v-if="store.segments.length > 0">
        <h2>Preview ({{ store.segments.length }} segments)</h2>
        <div class="segment-list">
          <div v-for="(segment, index) in store.segments.slice(0, 3)" :key="index" class="segment">
            <span class="timestamp">{{ segment.start.toFixed(1) }}s - {{ segment.end.toFixed(1) }}s</span>
            <p class="text">{{ segment.text }}</p>
          </div>
          <p v-if="store.segments.length > 3" class="more-segments">
            ... and {{ store.segments.length - 3 }} more segments
          </p>
        </div>
      </div>

      <div class="placeholder-notice">
        <p><strong>Note:</strong> This is a temporary placeholder page.</p>
        <p>Story 1.7 will implement the full transcription display interface with editing capabilities.</p>
      </div>

      <router-link to="/" class="back-button">
        ← Upload Another File
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.results-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.placeholder-card {
  background: white;
  border-radius: 16px;
  padding: 3rem;
  max-width: 800px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: bounce 0.6s ease-out;
}

@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-20px);
  }
  60% {
    transform: translateY(-10px);
  }
}

h1 {
  color: #2c3e50;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.message {
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

.job-info {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.job-info h2 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.job-id {
  display: inline-block;
  background: #e9ecef;
  color: #495057;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  word-break: break-all;
}

.segments-preview {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: left;
}

.segments-preview h2 {
  font-size: 1rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.segment-list {
  max-height: 300px;
  overflow-y: auto;
}

.segment {
  background: white;
  padding: 1rem;
  margin-bottom: 0.5rem;
  border-radius: 4px;
  border-left: 3px solid #42b983;
}

.timestamp {
  display: block;
  font-size: 0.8rem;
  color: #42b983;
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-family: monospace;
}

.text {
  color: #2c3e50;
  margin: 0;
  line-height: 1.6;
}

.more-segments {
  text-align: center;
  color: #999;
  font-style: italic;
  margin-top: 1rem;
}

.placeholder-notice {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 1rem;
  margin-bottom: 2rem;
  text-align: left;
  border-radius: 4px;
}

.placeholder-notice p {
  margin: 0.5rem 0;
  color: #856404;
  font-size: 0.9rem;
}

.placeholder-notice strong {
  color: #856404;
}

.back-button {
  display: inline-block;
  padding: 0.75rem 2rem;
  background: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.back-button:hover {
  background: #359268;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.4);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .placeholder-card {
    padding: 2rem 1.5rem;
  }

  h1 {
    font-size: 1.5rem;
  }

  .success-icon {
    font-size: 3rem;
  }

  .job-id {
    font-size: 0.8rem;
    padding: 0.4rem 0.8rem;
  }
}
</style>
