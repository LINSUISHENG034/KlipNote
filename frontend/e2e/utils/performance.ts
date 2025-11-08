import type { Page } from '@playwright/test'

/**
 * Performance Measurement Utilities for KlipNote E2E Tests
 *
 * Story 2.7: Performance Validation (AC #4)
 * NFR001 Targets:
 * - UI Load Time: <3 seconds
 * - Media Playback Start: <2 seconds
 * - Click-to-Timestamp Response: <1 second
 */

/**
 * Measure page load time using Navigation Timing API
 * Target: <3000ms (NFR001)
 */
export async function measureLoadTime(page: Page): Promise<number> {
  const navigationTiming = await page.evaluate(() => {
    const perf = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (!perf) {
      return 0
    }
    return perf.domContentLoadedEventEnd - perf.fetchStart
  })
  return Math.round(navigationTiming)
}

/**
 * Measure media playback start time (click play → audio/video starts)
 * Target: <2000ms (NFR001)
 */
export async function measurePlaybackStartTime(
  page: Page,
  playerSelector: string = 'video, audio'
): Promise<number> {
  const start = Date.now()

  // Trigger play
  const player = page.locator(playerSelector)
  await player.click()

  // Wait for 'playing' event
  await page.waitForFunction(
    (sel) => {
      const media = document.querySelector(sel) as HTMLMediaElement
      return media && !media.paused && media.readyState >= 2
    },
    playerSelector,
    { timeout: 5000 }
  )

  return Date.now() - start
}

/**
 * Measure click-to-timestamp seek response time
 * Target: <1000ms (NFR001)
 */
export async function measureSeekTime(
  page: Page,
  subtitleSelector: string,
  playerSelector: string = 'video, audio'
): Promise<number> {
  const start = Date.now()

  // Click subtitle to trigger seek
  await page.click(subtitleSelector)

  // Wait for seek to complete
  await page.waitForFunction(
    (sel) => {
      const media = document.querySelector(sel) as HTMLMediaElement
      return media && !media.seeking
    },
    playerSelector,
    { timeout: 5000 }
  )

  return Date.now() - start
}

/**
 * Performance metrics interface
 */
export interface PerformanceMetrics {
  uiLoadTime: number
  playbackStartTime: number
  seekTime: number
  timestamp: string
}

/**
 * Collect all NFR001 performance metrics
 */
export async function collectPerformanceMetrics(
  page: Page,
  subtitleSelector?: string
): Promise<PerformanceMetrics> {
  const uiLoadTime = await measureLoadTime(page)

  let playbackStartTime = 0
  let seekTime = 0

  // Only measure playback and seek if we're on the results page
  if (subtitleSelector) {
    try {
      playbackStartTime = await measurePlaybackStartTime(page)
      seekTime = await measureSeekTime(page, subtitleSelector)
    } catch (error) {
      console.warn('Failed to measure playback/seek metrics:', error)
    }
  }

  return {
    uiLoadTime,
    playbackStartTime,
    seekTime,
    timestamp: new Date().toISOString(),
  }
}

/**
 * Format performance metrics for display
 */
export function formatPerformanceMetrics(metrics: PerformanceMetrics): string {
  const nfr001Targets = {
    uiLoadTime: 3000,
    playbackStartTime: 2000,
    seekTime: 1000,
  }

  const checkMark = (value: number, target: number) => (value <= target ? '✓' : '✗')

  return `
Performance Metrics (NFR001 Validation):
- UI Load Time: ${metrics.uiLoadTime}ms ${checkMark(metrics.uiLoadTime, nfr001Targets.uiLoadTime)} (Target: <${nfr001Targets.uiLoadTime}ms)
- Playback Start: ${metrics.playbackStartTime}ms ${checkMark(metrics.playbackStartTime, nfr001Targets.playbackStartTime)} (Target: <${nfr001Targets.playbackStartTime}ms)
- Click-to-Timestamp: ${metrics.seekTime}ms ${checkMark(metrics.seekTime, nfr001Targets.seekTime)} (Target: <${nfr001Targets.seekTime}ms)
Measured at: ${metrics.timestamp}
  `.trim()
}
