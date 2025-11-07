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

// Expose for testing
defineExpose({
  errorMessage
})
</script>

<template>
  <div class="min-h-screen w-full flex items-center justify-center bg-dark-bg p-4">
    <main class="w-full max-w-md">
      <!-- Glass-morphism card -->
      <div class="flex flex-col items-stretch justify-start rounded-xl bg-white/10 dark:bg-zinc-900/40 p-6 md:p-8 shadow-xl backdrop-blur-lg">
        <!-- Header section -->
        <div class="flex w-full flex-col items-stretch justify-center gap-4 text-center">
          <h1 class="text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
            KlipNote - AI Transcription
          </h1>
          <p class="text-base leading-relaxed text-slate-400">
            Upload your audio or video file to generate a transcription
          </p>
          <p class="text-sm text-slate-500">
            Supported formats: MP3, MP4, WAV, M4A
          </p>
        </div>

        <!-- FileUpload component (drag-and-drop area) -->
        <div class="mt-6">
          <FileUpload @file-selected="handleFileSelected" />
        </div>

        <!-- Upload button with Material Symbol icon -->
        <div class="mt-8 flex justify-center">
          <button
            @click="handleUpload"
            :disabled="!selectedFile || isUploading"
            data-testid="upload-button"
            class="flex h-12 min-w-[84px] w-full max-w-xs items-center justify-center gap-2 overflow-hidden rounded-full bg-primary px-5 text-base font-bold leading-normal tracking-[0.015em] text-white shadow-lg transition-transform hover:scale-105 active:scale-100 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <span class="material-symbols-outlined text-xl">upload_file</span>
            <span class="truncate">
              {{ isUploading ? 'Uploading...' : 'Upload and Transcribe' }}
            </span>
          </button>
        </div>

        <!-- Error message display -->
        <div v-if="errorMessage" data-testid="error-message" class="mt-4 p-3 bg-red-900/30 border border-red-500/50 text-red-300 rounded-lg text-sm">
          {{ errorMessage }}
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Minimal scoped styles - prefer Tailwind utility classes */
</style>
