<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Segment } from '@/types/api'
import { formatTime } from '@/utils/formatters'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()
const segmentRefs = ref<HTMLDivElement[]>([])

// Task 2: Click handler for timestamp navigation
function handleClick(segment: Segment, index: number) {
  // Guard: Prevent seek during editing (Story 2.4 integration)
  if (store.editingSegmentId !== null) {
    console.warn('Cannot seek while editing. Please finish editing first.')
    return
  }

  // Command seek via store (MediaPlayer watches currentTime)
  store.seekTo(segment.start)
}

// Task 4: Auto-scroll active segment into view
watch(() => store.activeSegmentIndex, async (newIndex) => {
  if (newIndex === -1 || !segmentRefs.value[newIndex]) return

  await nextTick()  // Ensure DOM updated before scrolling

  segmentRefs.value[newIndex]?.scrollIntoView({
    behavior: 'smooth',
    block: 'center'  // Keep active subtitle centered in viewport
  })
})
</script>

<template>
  <div class="flex flex-col gap-3 max-h-[600px] overflow-y-auto" data-testid="subtitle-list">
    <div
      v-for="(segment, index) in store.segments"
      :key="index"
      :ref="(el) => { if (el) segmentRefs[index] = el as HTMLDivElement }"
      data-testid="subtitle-segment"
      :class="{
        'bg-blue-900/40 border-l-4 border-blue-500 font-semibold': index === store.activeSegmentIndex,
        'bg-zinc-800/50 hover:bg-zinc-800/70': index !== store.activeSegmentIndex && store.editingSegmentId === null,
        'cursor-pointer': store.editingSegmentId === null,
        'cursor-not-allowed opacity-60': store.editingSegmentId !== null
      }"
      class="flex items-start gap-3 p-4 rounded-lg transition-all duration-150"
      @click="handleClick(segment, index)"
    >
      <p
        data-testid="timestamp"
        :class="{
          'text-blue-400': index === store.activeSegmentIndex,
          'text-primary': index !== store.activeSegmentIndex
        }"
        class="text-sm font-bold leading-normal mt-1 min-w-[3.5rem] font-mono"
      >
        {{ formatTime(segment.start) }}
      </p>
      <div class="w-full">
        <p
          data-testid="text"
          :class="{
            'text-zinc-100': index === store.activeSegmentIndex,
            'text-zinc-300': index !== store.activeSegmentIndex
          }"
          class="text-base font-normal leading-relaxed"
        >
          {{ segment.text }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for subtitle list */
[data-testid="subtitle-list"]::-webkit-scrollbar {
  width: 8px;
}

[data-testid="subtitle-list"]::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

[data-testid="subtitle-list"]::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

[data-testid="subtitle-list"]::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
