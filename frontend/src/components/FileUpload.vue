<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  'file-selected': [file: File]
}>()

const isDragOver = ref(false)
const validationError = ref<string | null>(null)
const selectedFileName = ref<string | null>(null)

const ALLOWED_TYPES = ['audio/', 'video/']

function validateFile(file: File): boolean {
  const isValid = ALLOWED_TYPES.some(type => file.type.startsWith(type))

  if (!isValid) {
    validationError.value = 'Please upload an audio or video file (MP3, MP4, WAV, M4A)'
    return false
  }

  validationError.value = null
  return true
}

function handleFileInput(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file && validateFile(file)) {
    selectedFileName.value = file.name
    emit('file-selected', file)
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false

  const file = event.dataTransfer?.files[0]
  if (file && validateFile(file)) {
    selectedFileName.value = file.name
    emit('file-selected', file)
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}
</script>

<template>
  <div
    class="file-upload"
    :class="{ 'drag-over': isDragOver }"
    @drop="handleDrop"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
  >
    <input
      type="file"
      id="file-input"
      accept="audio/*,video/*"
      @change="handleFileInput"
      hidden
    />

    <label for="file-input" class="file-label">
      <div class="upload-icon">📁</div>
      <p class="main-text">Drag and drop your file here</p>
      <p class="or-text">or</p>
      <span class="choose-file-button">
        Choose File
      </span>
    </label>

    <div v-if="selectedFileName" class="selected-file">
      Selected: {{ selectedFileName }}
    </div>

    <div v-if="validationError" class="validation-error">
      {{ validationError }}
    </div>
  </div>
</template>

<style scoped>
.file-upload {
  border: 2px dashed rgb(71 85 105); /* slate-600 */
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background-color: rgb(15 23 42 / 0.3); /* dark semi-transparent */
}

.file-upload.drag-over {
  border-color: rgb(34 197 94); /* green-500 for primary */
  background-color: rgb(34 197 94 / 0.1);
  transform: scale(1.02);
}

.file-upload:hover {
  border-color: rgb(34 197 94); /* green-500 for primary */
}

.file-label {
  cursor: pointer;
  display: block;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.main-text {
  color: rgb(148 163 184); /* slate-400 */
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.or-text {
  color: rgb(100 116 139); /* slate-500 */
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.choose-file-button {
  display: inline-block;
  padding: 0.5rem 1.5rem;
  background-color: rgb(34 197 94); /* green-500 primary */
  color: white;
  border-radius: 9999px; /* rounded-full */
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.choose-file-button:hover {
  background-color: rgb(22 163 74); /* green-600 */
  transform: scale(1.05);
}

.selected-file {
  margin-top: 1rem;
  padding: 0.5rem;
  background-color: rgb(34 197 94 / 0.2);
  color: rgb(134 239 172); /* green-300 */
  border-radius: 4px;
  font-size: 0.9rem;
}

.validation-error {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: rgb(220 38 38 / 0.2);
  color: rgb(252 165 165); /* red-300 */
  border-radius: 4px;
  font-size: 0.9rem;
}

/* Touch-friendly sizing for mobile */
@media (max-width: 768px) {
  .file-upload {
    padding: 1.5rem;
  }

  .upload-icon {
    font-size: 2.5rem;
  }

  .choose-file-button {
    padding: 0.75rem 2rem;
    font-size: 1rem;
    /* Ensure touch target is at least 44x44px */
    min-height: 44px;
    min-width: 150px;
  }

  .main-text {
    font-size: 0.95rem;
  }
}

/* Extra small mobile */
@media (max-width: 480px) {
  .file-upload {
    padding: 1rem;
  }

  .choose-file-button {
    width: 100%;
  }
}
</style>
