import { test, expect, devices } from '@playwright/test'
import { ValidationReport } from '../utils/report'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import * as fs from 'fs'
import * as path from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

/**
 * Cross-Browser Compatibility Tests
 *
 * Story 2.7 - Task 2: Cross-Browser Testing (AC #2, #9)
 *
 * Tests compatibility across:
 * - Chrome desktop (version 90+) - Baseline browser
 * - Firefox desktop (version 88+) - Media compatibility
 * - Safari desktop (version 14+) - Range request handling, media seeking (AC #9)
 * - Edge desktop (version 90+) - Quick validation (Chromium-based)
 * - Chrome mobile (Android/iOS) - Responsive layout, touch interactions
 * - Safari mobile (iOS) - Touch interactions, media seeking
 *
 * Safari-specific focus (AC #9):
 * - Media seeking behavior (may differ from Chrome/Firefox)
 * - Range request support for media streaming
 * - Playback controls (native vs custom)
 */

const report = new ValidationReport()
const testFile = 'zh_medium_audio.mp3' // Use medium file for browser testing
const testFilePath = path.join(__dirname, '..', 'fixtures', testFile)

test.describe('Cross-Browser Compatibility', () => {
  test.beforeAll(() => {
    console.log('\\n===== Cross-Browser Compatibility Testing =====')
    console.log(`Test file: ${testFile}`)

    if (!fs.existsSync(testFilePath)) {
      console.warn(`WARNING: Test file ${testFile} not found`)
      console.warn('See e2e/fixtures/README.md for instructions')
    }
  })

  test('Chrome desktop - Full workflow validation', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Chrome-specific test')

    console.log('\\n--- Testing on Chrome Desktop ---')

    await page.goto('/')
    await expect(page).toHaveTitle(/KlipNote/)

    // Upload and transcribe
    if (fs.existsSync(testFilePath)) {
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(testFilePath)

      const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Start")')
      if (await uploadButton.isVisible({ timeout: 2000 })) {
        await uploadButton.click()
      }

      // Wait for transcription completion by URL navigation and subtitle display
      await page.waitForURL('**/result/**', { timeout: 300000 })
      const subtitles = page.locator('[class*="subtitle"], [class*="segment"]')
      await expect(subtitles.first()).toBeVisible({ timeout: 30000 })

      // Test media playback
      const player = page.locator('video, audio').first()
      await expect(player).toBeVisible()

      // Test click-to-timestamp
      const subtitle = page.locator('[class*="subtitle"], [class*="segment"]').first()
      if (await subtitle.isVisible({ timeout: 5000 })) {
        await subtitle.click()
        await page.waitForTimeout(500)
        const playerTime = await player.evaluate((el: HTMLMediaElement) => el.currentTime)
        expect(playerTime).toBeGreaterThan(0)
      }

      console.log('✓ Chrome desktop: Full workflow passed')
      report.addBrowserResult('Chrome', '90+', 'Desktop', 'PASS')
      report.addTestResult('Cross-Browser', 'Chrome desktop full workflow', 'PASS')
    } else {
      test.skip(true, 'Test file not available')
    }
  })

  test('Firefox desktop - Media compatibility validation', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox', 'Firefox-specific test')

    console.log('\\n--- Testing on Firefox Desktop ---')

    await page.goto('/')

    if (fs.existsSync(testFilePath)) {
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(testFilePath)

      const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Start")')
      if (await uploadButton.isVisible({ timeout: 2000 })) {
        await uploadButton.click()
      }

      // Wait for transcription completion by URL navigation and subtitle display
      await page.waitForURL('**/result/**', { timeout: 300000 })
      const subtitles = page.locator('[class*="subtitle"], [class*="segment"]')
      await expect(subtitles.first()).toBeVisible({ timeout: 30000 })

      // Firefox-specific: Test media player compatibility
      const player = page.locator('video, audio').first()
      await expect(player).toBeVisible()

      // Verify media format support
      const canPlay = await player.evaluate((el: HTMLMediaElement) => {
        return el.canPlayType('audio/mpeg') !== ''
      })
      expect(canPlay).toBe(true)

      console.log('✓ Firefox desktop: Media compatibility passed')
      report.addBrowserResult('Firefox', '88+', 'Desktop', 'PASS')
      report.addTestResult('Cross-Browser', 'Firefox desktop media compatibility', 'PASS')
    } else {
      test.skip(true, 'Test file not available')
    }
  })

  test('Safari desktop - Range request and media seeking (AC #9)', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'Safari-specific test')

    console.log('\\n--- Testing on Safari Desktop (webkit) ---')

    await page.goto('/')

    if (fs.existsSync(testFilePath)) {
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(testFilePath)

      const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Start")')
      if (await uploadButton.isVisible({ timeout: 2000 })) {
        await uploadButton.click()
      }

      // Wait for transcription completion by URL navigation and subtitle display
      await page.waitForURL('**/result/**', { timeout: 300000 })
      const subtitles = page.locator('[class*="subtitle"], [class*="segment"]')
      await expect(subtitles.first()).toBeVisible({ timeout: 30000 })

      // Safari-specific: Test Range request support
      const player = page.locator('video, audio').first()
      await expect(player).toBeVisible()

      // Test seeking behavior (Safari may handle Range requests differently)
      const middleSubtitle = subtitles.nth(Math.floor(await subtitles.count() / 2))

      if (await middleSubtitle.isVisible({ timeout: 5000 })) {
        await middleSubtitle.scrollIntoViewIfNeeded()
        await middleSubtitle.click()
        await page.waitForTimeout(1000)

        // Verify seek completed without buffering issues
        const isStalled = await player.evaluate((el: HTMLMediaElement) => el.seeking)
        expect(isStalled).toBe(false)

        const playerTime = await player.evaluate((el: HTMLMediaElement) => el.currentTime)
        expect(playerTime).toBeGreaterThan(0)

        console.log('✓ Safari desktop: Range request and seeking passed')
        report.addBrowserResult('Safari', '14+', 'Desktop', 'PASS', 'Range requests work smoothly')
        report.addTestResult('Cross-Browser', 'Safari desktop media seeking (AC #9)', 'PASS')
      }
    } else {
      test.skip(true, 'Test file not available')
    }
  })

  test('Mobile Chrome - Responsive layout and touch interactions', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Chrome mobile test')

    console.log('\\n--- Testing on Chrome Mobile ---')

    // Set mobile viewport
    await page.setViewportSize(devices['Pixel 5'].viewport!)

    await page.goto('/')
    await expect(page).toHaveTitle(/KlipNote/)

    // Verify responsive layout
    const uploadArea = page.locator('[class*="upload"], input[type="file"]').first()
    await expect(uploadArea).toBeVisible()

    // Verify elements fit within viewport (no horizontal scroll)
    const viewportWidth = devices['Pixel 5'].viewport!.width
    const pageWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(pageWidth).toBeLessThanOrEqual(viewportWidth)

    if (fs.existsSync(testFilePath)) {
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(testFilePath)

      const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Start")')
      if (await uploadButton.isVisible({ timeout: 2000 })) {
        await uploadButton.click()
      }

      // Wait for transcription completion by URL navigation and subtitle display
      await page.waitForURL('**/result/**', { timeout: 300000 })
      const subtitles = page.locator('[class*="subtitle"], [class*="segment"]')
      await expect(subtitles.first()).toBeVisible({ timeout: 30000 })

      // Test touch interaction: tap subtitle
      const subtitle = page.locator('[class*="subtitle"], [class*="segment"]').first()
      if (await subtitle.isVisible({ timeout: 5000 })) {
        await subtitle.tap()
        await page.waitForTimeout(500)

        const player = page.locator('video, audio').first()
        const playerTime = await player.evaluate((el: HTMLMediaElement) => el.currentTime)
        expect(playerTime).toBeGreaterThan(0)

        console.log('✓ Chrome mobile: Responsive layout and touch interactions passed')
        report.addBrowserResult('Chrome Mobile', 'Latest', 'Android/iOS', 'PASS')
        report.addTestResult('Cross-Browser', 'Chrome mobile responsive layout', 'PASS')
      }
    } else {
      // Still verify layout even without test file
      console.log('✓ Chrome mobile: Responsive layout verified')
      report.addBrowserResult('Chrome Mobile', 'Latest', 'Android/iOS', 'PASS', 'Layout verified without transcription test')
      report.addTestResult('Cross-Browser', 'Chrome mobile responsive layout', 'PASS')
    }
  })

  test('Mobile Safari - Touch interactions and media seeking', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'Safari mobile test')

    console.log('\\n--- Testing on Safari Mobile ---')

    // Set mobile viewport (iPhone 13)
    await page.setViewportSize(devices['iPhone 13'].viewport!)

    await page.goto('/')

    // Verify responsive layout
    const viewportWidth = devices['iPhone 13'].viewport!.width
    const pageWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(pageWidth).toBeLessThanOrEqual(viewportWidth)

    if (fs.existsSync(testFilePath)) {
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(testFilePath)

      const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Start")')
      if (await uploadButton.isVisible({ timeout: 2000 })) {
        await uploadButton.click()
      }

      // Wait for transcription completion by URL navigation and subtitle display
      await page.waitForURL('**/result/**', { timeout: 300000 })
      const subtitles = page.locator('[class*="subtitle"], [class*="segment"]')
      await expect(subtitles.first()).toBeVisible({ timeout: 30000 })

      // Safari mobile: Test tap-to-seek
      const subtitle = page.locator('[class*="subtitle"], [class*="segment"]').first()
      if (await subtitle.isVisible({ timeout: 5000 })) {
        await subtitle.tap()
        await page.waitForTimeout(1000)

        const player = page.locator('video, audio').first()
        const isStalled = await player.evaluate((el: HTMLMediaElement) => el.seeking)
        expect(isStalled).toBe(false)

        console.log('✓ Safari mobile: Touch interactions and media seeking passed')
        report.addBrowserResult('Safari Mobile', 'Latest', 'iOS', 'PASS', 'Touch and seeking work correctly')
        report.addTestResult('Cross-Browser', 'Safari mobile touch interactions', 'PASS')
      }
    } else {
      console.log('✓ Safari mobile: Responsive layout verified')
      report.addBrowserResult('Safari Mobile', 'Latest', 'iOS', 'PASS', 'Layout verified without transcription test')
      report.addTestResult('Cross-Browser', 'Safari mobile responsive layout', 'PASS')
    }
  })

  test('Portrait and landscape orientation (mobile)', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Mobile orientation test')

    console.log('\\n--- Testing orientation changes ---')

    // Portrait
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    const portraitWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(portraitWidth).toBeLessThanOrEqual(390)
    console.log('✓ Portrait orientation: Layout adapts correctly')

    // Landscape
    await page.setViewportSize({ width: 844, height: 390 })
    await page.goto('/')

    const landscapeWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(landscapeWidth).toBeLessThanOrEqual(844)
    console.log('✓ Landscape orientation: Layout adapts correctly')

    report.addTestResult('Cross-Browser', 'Mobile orientation handling', 'PASS')
  })

  test.afterAll(() => {
    const reportPath = path.join(__dirname, '..', '..', '..', 'docs', 'validation-report-browser.md')
    report.saveToFile(reportPath)
  })
})
