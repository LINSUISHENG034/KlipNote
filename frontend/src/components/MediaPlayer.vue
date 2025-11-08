<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { throttle } from 'lodash-es'
import { useTranscriptionStore } from '@/stores/transcription'

const props = defineProps<{
  mediaUrl: string
  jobId: string
}>()

const store = useTranscriptionStore()
const playerRef = ref<HTMLVideoElement | HTMLAudioElement | null>(null)

// Determine media type from URL extension
const isVideo = computed(() => {
  const url = props.mediaUrl.toLowerCase()
  return url.includes('.mp4') || url.includes('.avi') || url.includes('.mov') || url.includes('.webm')
})

// Task 4: Watch for commanded seeks from store (Story 2.3 will trigger these)
watch(() => store.currentTime, (newTime) => {
  if (playerRef.value && Math.abs(playerRef.value.currentTime - newTime) > 0.5) {
    playerRef.value.currentTime = newTime
    // Respect play/pause state
    if (store.isPlaying) {
      playerRef.value.play()
    }
  }
})

// Task 3: Throttled timeupdate to avoid excessive store updates
const throttledTimeUpdate = throttle((currentTime: number) => {
  store.updatePlaybackTime(currentTime)
}, 250) // Update every 250ms (4 times/second)

function onTimeUpdate() {
  if (playerRef.value) {
    throttledTimeUpdate(playerRef.value.currentTime)
  }
}

// Task 3: Sync native player state to store
function onPlay() {
  store.setIsPlaying(true)
}

function onPause() {
  store.setIsPlaying(false)
}
</script>

<template>
  <div class="media-player-container">
    <video
      v-if="isVideo"
      ref="playerRef"
      :src="mediaUrl"
      @timeupdate="onTimeUpdate"
      @play="onPlay"
      @pause="onPause"
      @ended="onPause"
      controls
      class="w-full aspect-video bg-black"
    />
    <audio
      v-else
      ref="playerRef"
      :src="mediaUrl"
      @timeupdate="onTimeUpdate"
      @play="onPlay"
      @pause="onPause"
      @ended="onPause"
      controls
      class="w-full"
    />
  </div>
</template>

<style scoped>
.media-player-container {
  width: 100%;
}
</style>
