import * as fs from 'fs'
import * as path from 'path'

/**
 * Validation Report Generator for KlipNote MVP Release
 *
 * Story 2.7: Critical Bug Assessment (AC #7)
 * Generates comprehensive validation report with go/no-go recommendation
 */

export type TestStatus = 'PASS' | 'FAIL' | 'SKIP'
export type BugSeverity = 'Critical' | 'Major' | 'Minor'

export interface TestResult {
  category: string
  testName: string
  status: TestStatus
  details?: string
  duration?: number
}

export interface Bug {
  severity: BugSeverity
  description: string
  category: string
  workaround?: string
}

export interface PerformanceMetric {
  metric: string
  actual: number
  target: number
  unit: string
  status: TestStatus
}

export interface BrowserTestResult {
  browser: string
  version: string
  platform: string
  status: TestStatus
  notes?: string
}

export class ValidationReport {
  private testResults: TestResult[] = []
  private bugs: Bug[] = []
  private performanceMetrics: PerformanceMetric[] = []
  private browserResults: BrowserTestResult[] = []
  private buildVersion: string = ''
  private testerName: string = 'BMAD Developer Agent'

  constructor() {
    this.buildVersion = this.getGitCommitHash()
  }

  /**
   * Add a test result
   */
  addTestResult(category: string, testName: string, status: TestStatus, details?: string, duration?: number) {
    this.testResults.push({ category, testName, status, details, duration })
  }

  /**
   * Add a bug report
   */
  addBug(severity: BugSeverity, description: string, category: string, workaround?: string) {
    this.bugs.push({ severity, description, category, workaround })
  }

  /**
   * Add a performance metric
   */
  addPerformanceMetric(metric: string, actual: number, target: number, unit: string) {
    const status: TestStatus = actual <= target ? 'PASS' : 'FAIL'
    this.performanceMetrics.push({ metric, actual, target, unit, status })
  }

  /**
   * Add browser test result
   */
  addBrowserResult(browser: string, version: string, platform: string, status: TestStatus, notes?: string) {
    this.browserResults.push({ browser, version, platform, status, notes })
  }

  /**
   * Get critical bug count
   */
  getCriticalBugCount(): number {
    return this.bugs.filter((b) => b.severity === 'Critical').length
  }

  /**
   * Get major bug count
   */
  getMajorBugCount(): number {
    return this.bugs.filter((b) => b.severity === 'Major').length
  }

  /**
   * Get minor bug count
   */
  getMinorBugCount(): number {
    return this.bugs.filter((b) => b.severity === 'Minor').length
  }

  /**
   * Calculate test pass rate
   */
  getPassRate(): number {
    const total = this.testResults.length
    if (total === 0) return 0
    const passed = this.testResults.filter((r) => r.status === 'PASS').length
    return Math.round((passed / total) * 100)
  }

  /**
   * Get GO/NO-GO recommendation
   */
  getRecommendation(): 'GO' | 'NO-GO' {
    const criticalBugs = this.getCriticalBugCount()
    const passRate = this.getPassRate()
    const performancePass = this.performanceMetrics.every((m) => m.status === 'PASS')

    if (criticalBugs > 0) {
      return 'NO-GO'
    }
    if (passRate < 90) {
      return 'NO-GO'
    }
    if (!performancePass) {
      return 'NO-GO'
    }
    return 'GO'
  }

  /**
   * Generate markdown report
   */
  generateMarkdown(): string {
    const date = new Date().toISOString().split('T')[0]
    const recommendation = this.getRecommendation()

    let md = `# KlipNote MVP Validation Report

**Date:** ${date}
**Tester:** ${this.testerName}
**Build Version:** ${this.buildVersion}

## Executive Summary

- **Overall Status:** ${recommendation === 'GO' ? 'PASS' : 'FAIL'}
- **Critical Bugs:** ${this.getCriticalBugCount()}
- **Major Bugs:** ${this.getMajorBugCount()}
- **Minor Bugs:** ${this.getMinorBugCount()}
- **Test Pass Rate:** ${this.getPassRate()}%
- **Recommendation:** **${recommendation}** for MVP release

`

    // Test Results by Category
    md += '## Test Results by Category\n\n'
    const categories = [...new Set(this.testResults.map((r) => r.category))]

    for (const category of categories) {
      const categoryResults = this.testResults.filter((r) => r.category === category)
      const passed = categoryResults.filter((r) => r.status === 'PASS').length
      const total = categoryResults.length

      md += `### ${category}\n\n`
      md += `- Pass Rate: ${passed}/${total} (${Math.round((passed / total) * 100)}%)\n`
      md += `- Status: ${passed === total ? 'PASS ✓' : 'FAIL ✗'}\n\n`

      if (categoryResults.some((r) => r.status === 'FAIL')) {
        md += '**Issues Found:**\n'
        categoryResults.filter((r) => r.status === 'FAIL').forEach((r) => {
          md += `- ${r.testName}: ${r.details || 'Test failed'}\n`
        })
        md += '\n'
      } else {
        md += '**Issues Found:** None\n\n'
      }
    }

    // Performance Summary
    if (this.performanceMetrics.length > 0) {
      md += '## Performance Summary (NFR001)\n\n'
      md += '| Metric | Actual | Target | Status |\n'
      md += '|--------|--------|--------|--------|\n'
      this.performanceMetrics.forEach((m) => {
        const statusIcon = m.status === 'PASS' ? '✓' : '✗'
        md += `| ${m.metric} | ${m.actual}${m.unit} | <${m.target}${m.unit} | ${m.status} ${statusIcon} |\n`
      })
      md += '\n'
    }

    // Browser Compatibility Summary
    if (this.browserResults.length > 0) {
      md += '## Browser Compatibility Summary\n\n'
      md += '| Browser | Version | Platform | Status | Notes |\n'
      md += '|---------|---------|----------|--------|-------|\n'
      this.browserResults.forEach((b) => {
        const statusIcon = b.status === 'PASS' ? '✓' : '✗'
        md += `| ${b.browser} | ${b.version} | ${b.platform} | ${b.status} ${statusIcon} | ${b.notes || '-'} |\n`
      })
      md += '\n'
    }

    // Critical Bugs
    md += '## Critical Bugs (Blocking)\n\n'
    const criticalBugs = this.bugs.filter((b) => b.severity === 'Critical')
    if (criticalBugs.length === 0) {
      md += '**None found** ✓\n\n'
    } else {
      criticalBugs.forEach((bug, i) => {
        md += `### ${i + 1}. ${bug.description}\n\n`
        md += `- Category: ${bug.category}\n`
        if (bug.workaround) {
          md += `- Workaround: ${bug.workaround}\n`
        }
        md += '\n'
      })
    }

    // Major Bugs
    md += '## Major Bugs (Workaround Exists)\n\n'
    const majorBugs = this.bugs.filter((b) => b.severity === 'Major')
    if (majorBugs.length === 0) {
      md += '**None found** ✓\n\n'
    } else {
      majorBugs.forEach((bug, i) => {
        md += `${i + 1}. **${bug.description}** (${bug.category})`
        if (bug.workaround) {
          md += ` - Workaround: ${bug.workaround}`
        }
        md += '\n'
      })
      md += '\n'
    }

    // Minor Bugs
    md += '## Minor Bugs (Cosmetic)\n\n'
    const minorBugs = this.bugs.filter((b) => b.severity === 'Minor')
    if (minorBugs.length === 0) {
      md += '**None found** ✓\n\n'
    } else {
      minorBugs.forEach((bug, i) => {
        md += `${i + 1}. ${bug.description} (${bug.category})\n`
      })
      md += '\n'
    }

    // Recommendations
    md += '## Recommendations\n\n'
    if (recommendation === 'GO') {
      md += `- **GO for MVP release:** Yes ✓\n`
      md += `- **Required fixes before release:** None\n`

      if (majorBugs.length > 0 || minorBugs.length > 0) {
        md += `- **Post-MVP backlog items:** ${majorBugs.length + minorBugs.length} issues to address in future releases\n`
      }
    } else {
      md += `- **GO for MVP release:** No ✗\n`
      md += `- **Required fixes before release:**\n`

      if (criticalBugs.length > 0) {
        criticalBugs.forEach((bug) => {
          md += `  - [CRITICAL] ${bug.description}\n`
        })
      }

      const failedTests = this.testResults.filter((r) => r.status === 'FAIL')
      if (failedTests.length > 0) {
        md += `  - Fix ${failedTests.length} failed tests\n`
      }

      const failedPerformance = this.performanceMetrics.filter((m) => m.status === 'FAIL')
      if (failedPerformance.length > 0) {
        md += `  - Improve performance for: ${failedPerformance.map((m) => m.metric).join(', ')}\n`
      }
    }

    md += '\n## Sign-off\n\n'
    md += `- Tester: ${this.testerName} - ${date}\n`
    md += `- Product Owner: __________________ - Date: _______\n`
    md += `- Tech Lead: __________________ - Date: _______\n`

    return md
  }

  /**
   * Save report to file
   */
  saveToFile(filePath: string) {
    const markdown = this.generateMarkdown()
    const dir = path.dirname(filePath)

    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }

    fs.writeFileSync(filePath, markdown, 'utf-8')
    console.log(`Validation report saved to: ${filePath}`)
  }

  /**
   * Get git commit hash for build version
   */
  private getGitCommitHash(): string {
    try {
      const { execSync } = require('child_process')
      const hash = execSync('git rev-parse --short HEAD').toString().trim()
      return hash
    } catch {
      return 'unknown'
    }
  }
}
