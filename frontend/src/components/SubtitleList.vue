<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import type { Segment } from '@/types/api'
import { formatTime } from '@/utils/formatters'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()
const segmentRefs = ref<HTMLDivElement[]>([])

// Story 2.4: Auto-scroll control
const userScrolling = ref(false)
const scrollContainer = ref<HTMLElement | null>(null)
let scrollTimeout: number | null = null

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

// Story 2.4: Editing handlers
function handleDoubleClick(index: number) {
  store.setEditingSegment(index)
  // Focus the contenteditable after Vue renders it
  nextTick(() => {
    const editor = document.querySelector(`[data-editing-index="${index}"]`) as HTMLElement
    if (editor) {
      // Set initial text content only once
      editor.textContent = store.segments[index].text
      editor.focus()
      // Position cursor at the end of text for natural editing
      const range = document.createRange()
      const selection = window.getSelection()
      range.selectNodeContents(editor)
      range.collapse(false) // Collapse to end
      selection?.removeAllRanges()
      selection?.addRange(range)
    }
  })
}

function handleInput(index: number, event: Event) {
  const target = event.target as HTMLElement
  const newText = target.textContent || ''

  // Save cursor position
  const selection = window.getSelection()
  const cursorPos = selection?.focusOffset || 0
  const focusNode = selection?.focusNode

  // Update store (this will NOT trigger re-render of contenteditable)
  store.updateSegmentText(index, newText)

  // Restore cursor position if it was lost
  nextTick(() => {
    if (focusNode && selection && target.contains(focusNode)) {
      try {
        const range = document.createRange()
        range.setStart(focusNode, Math.min(cursorPos, focusNode.textContent?.length || 0))
        range.collapse(true)
        selection.removeAllRanges()
        selection.addRange(range)
      } catch (e) {
        // Cursor restoration failed, ignore
      }
    }
  })
}

function handleKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Tab' || event.key === 'Enter') {
    event.preventDefault()

    // Save current edit and move to next
    store.setEditingSegment(null)

    // Move to next segment (if not last)
    if (index < store.segments.length - 1) {
      nextTick(() => {
        handleDoubleClick(index + 1)
      })
    }
  } else if (event.key === 'Escape') {
    event.preventDefault()

    // Cancel edit and revert
    store.cancelEdit(index)
  }
}

function handleBlur(index: number) {
  // Exit edit mode when focus lost
  if (store.editingSegmentId === index) {
    store.setEditingSegment(null)
  }
}

function isEdited(index: number): boolean {
  return store.originalSegments[index] &&
         store.segments[index].text !== store.originalSegments[index].text
}

// Story 2.4: Detect manual scroll
function handleScroll() {
  userScrolling.value = true

  // Clear existing timeout
  if (scrollTimeout !== null) {
    window.clearTimeout(scrollTimeout)
  }

  // Resume auto-scroll after 3 seconds of no manual scrolling
  scrollTimeout = window.setTimeout(() => {
    userScrolling.value = false
  }, 3000)
}

// Task 4: Auto-scroll active segment into view (with user-scroll detection)
watch(() => store.activeSegmentIndex, async (newIndex) => {
  if (newIndex === -1 || !segmentRefs.value[newIndex]) return

  // Don't auto-scroll if user is editing or manually scrolling
  if (store.editingSegmentId !== null || userScrolling.value) return

  await nextTick()  // Ensure DOM updated before scrolling

  segmentRefs.value[newIndex]?.scrollIntoView({
    behavior: 'smooth',
    block: 'center'  // Keep active subtitle centered in viewport
  })
})

// Lifecycle: Setup scroll listener
onMounted(() => {
  const container = document.querySelector('[data-testid="subtitle-list"]') as HTMLElement
  if (container) {
    scrollContainer.value = container
    container.addEventListener('scroll', handleScroll, { passive: true })
  }
})

onUnmounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.removeEventListener('scroll', handleScroll)
  }
  if (scrollTimeout !== null) {
    window.clearTimeout(scrollTimeout)
  }
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
        'bg-yellow-900/30 border-l-4 border-yellow-500': index === store.editingSegmentId,
        'bg-zinc-800/50 hover:bg-zinc-800/70': index !== store.activeSegmentIndex && store.editingSegmentId !== index,
        'cursor-pointer': store.editingSegmentId === null,
        'cursor-not-allowed opacity-60': store.editingSegmentId !== null && store.editingSegmentId !== index
      }"
      class="flex items-start gap-3 p-4 rounded-lg transition-all duration-150"
      @click="handleClick(segment, index)"
      @dblclick="handleDoubleClick(index)"
    >
      <p
        data-testid="timestamp"
        :class="{
          'text-blue-400': index === store.activeSegmentIndex,
          'text-yellow-400': index === store.editingSegmentId,
          'text-primary': index !== store.activeSegmentIndex && index !== store.editingSegmentId
        }"
        class="text-sm font-bold leading-normal mt-1 min-w-[3.5rem] font-mono"
      >
        {{ formatTime(segment.start) }}
      </p>
      <div class="w-full">
        <!-- Non-editing mode -->
        <p
          v-if="index !== store.editingSegmentId"
          data-testid="text"
          :class="{
            'text-zinc-100': index === store.activeSegmentIndex,
            'text-zinc-300': index !== store.activeSegmentIndex
          }"
          class="text-base font-normal leading-relaxed"
        >
          {{ segment.text }}
          <span v-if="isEdited(index)" class="text-orange-400 ml-2 text-xs">●</span>
        </p>

        <!-- Editing mode -->
        <div
          v-else
          :data-editing-index="index"
          contenteditable="true"
          data-testid="text-editor"
          class="text-base font-normal leading-relaxed text-zinc-100 bg-zinc-900/80 p-2 rounded border-2 border-yellow-500 outline-none focus:border-yellow-400"
          @input="handleInput(index, $event)"
          @keydown="handleKeydown(index, $event)"
          @blur="handleBlur(index)"
        ></div>
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
