<script setup lang="ts">
import type { Segment } from '@/types/api'
import { formatTime } from '@/utils/formatters'

defineProps<{
  segments: Segment[]
}>()
</script>

<template>
  <div class="flex flex-col gap-3" data-testid="subtitle-list">
    <div
      v-for="(segment, index) in segments"
      :key="index"
      data-testid="subtitle-segment"
      class="flex items-start gap-3 bg-zinc-800/50 p-4 rounded-lg hover:bg-zinc-800/70 transition-colors cursor-pointer"
    >
      <p data-testid="timestamp" class="text-primary text-sm font-bold leading-normal mt-1 min-w-[3.5rem] font-mono">
        {{ formatTime(segment.start) }}
      </p>
      <div class="w-full">
        <p data-testid="text" class="text-zinc-300 text-base font-normal leading-relaxed">
          {{ segment.text }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Minimal scoped styles - prefer Tailwind utility classes */
</style>
