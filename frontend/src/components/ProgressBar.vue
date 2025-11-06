<script setup lang="ts">
defineProps<{
  progress: number // 0-100
}>()
</script>

<template>
  <div class="progress-bar-container">
    <div class="progress-bar">
      <div class="progress-bar-fill" :style="{ width: `${progress}%` }" />
    </div>
    <p class="progress-text">{{ progress }}%</p>
  </div>
</template>

<style scoped>
.progress-bar-container {
  margin: 2rem 0;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background-color: #e0e0e0;
  border-radius: 15px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: #42b983;
  transition: width 0.3s ease;
}

.progress-text {
  margin-top: 0.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  text-align: center;
}
</style>
