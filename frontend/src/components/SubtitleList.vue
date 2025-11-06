<script setup lang="ts">
import type { Segment } from '@/types/api'
import { formatTime } from '@/utils/formatters'

defineProps<{
  segments: Segment[]
}>()
</script>

<template>
  <div class="subtitle-list">
    <div
      v-for="(segment, index) in segments"
      :key="index"
      class="subtitle-segment"
    >
      <div class="segment-content">
        <p class="timestamp">{{ formatTime(segment.start) }}</p>
        <p class="text">{{ segment.text }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.subtitle-segment {
  background: rgba(39, 39, 42, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
  min-height: 72px;
  display: flex;
  align-items: center;
  transition: background-color 0.2s;
}

.subtitle-segment:hover {
  background: rgba(39, 39, 42, 0.7);
  cursor: pointer;
}

.segment-content {
  width: 100%;
}

.timestamp {
  color: #137fec;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.5;
  margin: 0 0 0.25rem 0;
}

.text {
  color: #d4d4d8;
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.5;
  margin: 0;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .subtitle-segment {
    padding: 0.875rem;
  }

  .timestamp {
    font-size: 0.8125rem;
  }

  .text {
    font-size: 0.9375rem;
  }
}
</style>
