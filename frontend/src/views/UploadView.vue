<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FileUpload from '@/components/FileUpload.vue'
import { uploadFile } from '@/services/api'

const router = useRouter()
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)
const errorMessage = ref<string | null>(null)

function handleFileSelected(file: File) {
  selectedFile.value = file
  errorMessage.value = null
}

async function handleUpload() {
  if (!selectedFile.value) {
    errorMessage.value = 'Please select a file first'
    return
  }

  isUploading.value = true
  errorMessage.value = null

  try {
    const response = await uploadFile(selectedFile.value)
    // Navigate to progress page with job_id
    router.push(`/progress/${response.job_id}`)
  } catch (error) {
    errorMessage.value = error instanceof Error
      ? error.message
      : 'Upload failed. Please try again.'
    console.error('Upload error:', error)
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <div class="upload-view">
    <h1>KlipNote - AI Transcription</h1>
    <p>Upload your audio or video file to generate a transcription</p>
    <p class="supported-formats">Supported formats: MP3, MP4, WAV, M4A</p>

    <FileUpload @file-selected="handleFileSelected" />

    <button
      @click="handleUpload"
      :disabled="!selectedFile || isUploading"
      class="upload-button"
    >
      {{ isUploading ? 'Uploading...' : 'Upload and Transcribe' }}
    </button>

    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<style scoped>
.upload-view {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
}

h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

p {
  color: #34495e;
  line-height: 1.6;
}

.supported-formats {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.upload-button {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.upload-button:hover:not(:disabled) {
  background-color: #359268;
}

.upload-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #ffebee;
  color: #c62828;
  border-radius: 4px;
}

/* Responsive design - Mobile-first approach */
/* Mobile (320px-767px) */
@media (max-width: 767px) {
  .upload-view {
    padding: 1rem;
    margin: 1rem auto;
  }

  h1 {
    font-size: 1.5rem;
  }

  .upload-button {
    width: 100%;
    padding: 1rem;
    font-size: 1.1rem;
  }
}

/* Tablet (768px-1023px) */
@media (min-width: 768px) and (max-width: 1023px) {
  .upload-view {
    padding: 1.5rem;
  }

  h1 {
    font-size: 1.75rem;
  }
}

/* Desktop (1024px+) - default styles above already apply */
</style>
