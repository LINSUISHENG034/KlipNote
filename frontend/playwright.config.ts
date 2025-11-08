import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E Test Configuration for KlipNote MVP Validation
 *
 * Story 2.7: MVP Release Checklist & Final Validation
 * - Cross-browser testing: Chrome, Firefox, Safari (webkit), Edge, Mobile
 * - Sequential execution to avoid concurrent job conflicts
 * - Extended timeouts for transcription tests
 */
export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false, // Run sequentially for transcription tests
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // One worker to avoid concurrent job conflicts
  reporter: [
    ['html'],
    ['list']
  ],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  // Test timeout: 2 minutes for transcription tests
  timeout: 120000,

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],

  // Start backend and frontend servers before tests
  webServer: [
    {
      command: 'cd ../backend && docker-compose up',
      url: 'http://localhost:8000/docs',
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
  ],
})
