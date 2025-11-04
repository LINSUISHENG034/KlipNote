# BMM Testing & QA Workflows (Testarch)

**Reading Time:** ~18 minutes

## Overview

Testarch workflows provide comprehensive testing infrastructure and quality assurance. Unlike Phases 1-4 which are sequential, **testing workflows run in parallel** with implementation and can be invoked as needed throughout the project lifecycle.

**Key principle:** Testing is not a phase—it's a continuous practice integrated into every story.

## Quick Reference

| Workflow            | Duration          | When to Run            | Purpose                                |
| ------------------- | ----------------- | ---------------------- | -------------------------------------- |
| **framework**       | 1-2 hours         | Once (setup)           | Scaffold test infrastructure           |
| **test-design**     | 2-4 hours         | Before implementation  | Risk assessment and test planning      |
| **atdd**            | 30-90 min/story   | Per story (before dev) | Generate failing acceptance tests      |
| **automate**        | 1-3 hours/feature | After dev-story        | Expand regression suite                |
| **ci**              | 1-2 hours         | Once (after framework) | CI/CD pipeline with burn-in            |
| **trace** (Phase 1) | 15-30 min         | After tests written    | Traceability matrix                    |
| **trace** (Phase 2) | 15-30 min         | Before release         | Quality gate decision                  |
| **nfr-assess**      | 1-2 hours         | Before release         | Non-functional requirements validation |
| **test-review**     | 30-60 min         | After test creation    | Test quality validation                |

---

## Understanding Testarch

### TEA Agent (Test Architect)

All testarch workflows are executed by the **TEA agent** - your dedicated test architect and quality assurance specialist.

**TEA's Responsibilities:**

- Design test strategies
- Generate test code
- Validate test quality
- Ensure coverage
- Make quality gate decisions

**TEA's Knowledge Base:**

- 22+ knowledge fragments (tea-index.csv)
- Best practices for Playwright, Cypress, Jest, Vitest
- Test patterns: fixtures, factories, network-first, burn-in
- Quality standards: determinism, isolation, no flakiness

### Testing Integration with Implementation

**Parallel Execution Model:**

```
Implementation (Phase 4)          Testing (Continuous)
─────────────────────            ───────────────────
framework (once)          →      Test infrastructure ready
test-design (per epic)    →      Risk assessment complete
create-story              →      atdd (generate failing tests)
dev-story                 →      Tests now pass
                          →      automate (expand coverage)
code-review               →      test-review (validate quality)
                          →      trace (check coverage)
sprint complete           →      nfr-assess (validate NFRs)
                          →      trace Phase 2 (quality gate)
```

### Testarch vs Traditional QA

| Aspect          | Traditional QA     | Testarch                  |
| --------------- | ------------------ | ------------------------- |
| **When**        | After development  | Throughout development    |
| **Who**         | QA team            | TEA agent + DEV agent     |
| **Tests**       | Manual → Automated | Generated → Validated     |
| **Coverage**    | Variable           | Systematic (P0-P3)        |
| **Integration** | Separate process   | Built into workflows      |
| **Knowledge**   | Tribal             | Codified (knowledge base) |

---

## framework

### Purpose

Scaffold production-ready test infrastructure including framework configuration, directory structure, fixtures, factories, and helper utilities.

**Agent:** TEA (Test Architect)
**When to Run:** Once at project start (before implementation)
**Duration:** 1-2 hours
**Required:** Yes (for all projects with tests)

### When to Use

Run **before writing any tests** to establish test infrastructure.

**Trigger Points:**

- After Phase 3 (Solutioning) completes
- Before first dev-story workflow
- When starting a new project

**Skip if:**

- Tests already exist (brownfield with good test setup)
- Prototype/POC without tests

### What Framework Provides

**1. Framework Configuration**

- playwright.config.ts (or cypress.config.ts, jest.config.js)
- Environment-based configuration
- Browser/device targeting
- Parallel execution setup
- Reporter configuration

**2. Directory Structure**

```
/tests
  /e2e              - End-to-end tests
  /api              - API/integration tests
  /component        - Component tests
  /unit             - Unit tests
  /support
    /fixtures       - Test fixtures (setup/teardown)
    /factories      - Data factories (test data generation)
    /helpers        - Utility functions
  /reports          - Test reports
  README.md         - Test documentation
```

**3. Base Fixtures**

- Authentication fixtures
- Database fixtures (if applicable)
- API client fixtures
- Common test utilities

**4. Data Factories**

- User factory (with faker.js)
- Common entity factories
- Factory utilities

**5. Helper Utilities**

- Wait utilities
- Retry utilities
- API helpers
- Database helpers

### Process Overview

**Phase 1: Framework Selection (Steps 1-2)**

- Detect project type (web app, API, mobile, desktop)
- Recommend framework (Playwright, Cypress, Jest, Vitest, etc.)
- Confirm with user

**Phase 2: Configuration (Steps 3-5)**

- Generate framework config file
- Configure environments (local, CI, staging, prod)
- Set up parallel execution
- Configure reporters

**Phase 3: Directory Structure (Step 6)**

- Create test directories
- Generate README with test guidelines

**Phase 4: Fixtures and Factories (Steps 7-9)**

- Generate base fixtures
- Generate data factories
- Create helper utilities

**Phase 5: Validation (Step 10)**

- Generate sample test
- Run sample test to verify setup
- Document test execution commands

### Inputs

Required:

- Project type (web, API, mobile, desktop)
- Framework preference (optional, will recommend)

Optional:

- Existing package.json
- Technology stack (React, Vue, Node, etc.)

### Outputs

**Primary Outputs:**

1. **Framework Configuration File**
   - `playwright.config.ts` (Playwright)
   - `cypress.config.ts` (Cypress)
   - `jest.config.js` (Jest)
   - `vitest.config.ts` (Vitest)

2. **Directory Structure** (all directories created)

3. **Base Fixtures** (`/tests/support/fixtures/`)
   - `auth.fixture.ts` - Authentication fixture
   - `base.fixture.ts` - Base fixture utilities

4. **Data Factories** (`/tests/support/factories/`)
   - `user.factory.ts` - User data factory
   - `factory-utils.ts` - Factory utilities

5. **Helpers** (`/tests/support/helpers/`)
   - `wait.ts` - Wait utilities
   - `retry.ts` - Retry utilities

6. **Documentation**
   - `/tests/README.md` - Test execution guide

7. **Sample Test**
   - `/tests/e2e/sample.spec.ts` - Verify setup works

### Example Output: Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    ['html', { outputFolder: 'tests/reports' }],
    ['json', { outputFile: 'tests/reports/results.json' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
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
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Related Workflows

- **ci** - Configure CI/CD using framework config
- **test-design** - Plan test coverage using framework
- **atdd** - Generate tests using framework

---

## test-design

### Purpose

Plan comprehensive test coverage strategy with risk assessment (probability × impact scoring), priority classification (P0-P3), and resource estimation.

**Agent:** TEA (Test Architect)
**When to Run:** Before implementation (per epic or per project)
**Duration:** 2-4 hours
**Required:** Recommended for Level 3-4, Optional for Level 2

### When to Use

Run **before implementing tests** to plan coverage strategy.

**Trigger Points:**

- After PRD/GDD creation (project-wide planning)
- Before each epic (epic-specific planning)
- When assessing test coverage needs

**Skip if:**

- Level 0-1 (simple changes, test strategy obvious)
- Continuing existing project with established strategy

### Risk Assessment Framework

**Risk Score = Probability × Impact**

**Probability (1-3):**

- 1 (Unlikely): <10% chance
- 2 (Possible): 10-50% chance
- 3 (Likely): >50% chance

**Impact (1-3):**

- 1 (Minor): Cosmetic, workaround exists
- 2 (Degraded): Feature impaired
- 3 (Critical): System failure, no workaround

**Risk Scores:**

- **6-9 (High)**: Immediate attention, P0 tests required
- **3-4 (Medium)**: Plan mitigation, P1-P2 tests
- **1-2 (Low)**: Monitor, P3 tests optional

### Priority Classification (P0-P3)

| Priority | Run Frequency | Coverage Requirement | Characteristics                          |
| -------- | ------------- | -------------------- | ---------------------------------------- |
| **P0**   | Every commit  | 100%                 | Critical paths, security, data integrity |
| **P1**   | PR to main    | 90%                  | Important features, common workflows     |
| **P2**   | Nightly       | 80%                  | Edge cases, secondary features           |
| **P3**   | On-demand     | No requirement       | Nice-to-have, exploratory                |

### Process Overview

**Phase 1: Context Loading (Steps 1-2)**

- Load PRD/GDD
- Load architecture
- Load story files

**Phase 2: Risk Assessment (Steps 3-5)**

- Identify risk categories (TECH, SEC, PERF, DATA, BUS, OPS)
- Score risks (probability × impact)
- Flag high-risk items (≥6)

**Phase 3: Coverage Planning (Steps 6-8)**

- Map requirements to test levels (E2E/API/Component/Unit)
- Assign priorities (P0/P1/P2/P3)
- Avoid duplicate coverage

**Phase 4: Resource Estimation (Steps 9-10)**

- Estimate hours per priority
- Calculate total effort
- Define execution order

**Phase 5: Documentation (Step 11)**

- Generate test-design document
- Create coverage matrix
- Define quality gates

### Inputs

Required:

- PRD.md or GDD.md
- Epic files (for epic-specific design)

Optional:

- architecture.md
- Historical bug data
- Security audit results

### Outputs

**Primary Output:** `test-design-epic-{N}.md` or `test-design-project.md`

**Document Structure:**

1. **Risk Assessment Matrix**
   - Risk ID, category, description
   - Probability × Impact = Score
   - High-priority risks flagged

2. **Coverage Matrix**
   - Requirement → Test Level mapping
   - Priority assignment (P0-P3)
   - Test count estimates

3. **Execution Order**
   - Smoke tests (P0 subset, <5 min)
   - P0 tests (critical paths, <10 min)
   - P1 tests (important features, <30 min)
   - P2/P3 tests (full regression, <60 min)

4. **Resource Estimates**
   - Hours per priority level
   - Total effort in days

5. **Quality Gate Criteria**
   - P0 pass rate: 100%
   - P1 pass rate: ≥95%
   - Coverage targets

### Example: Test Design for Authentication Epic

**Risk Assessment:**

- R-001 (SEC): Password bypass, P=2 × I=3 = **6 (HIGH)** → P0 tests required
- R-002 (SEC): Session hijacking, P=2 × I=3 = **6 (HIGH)** → P0 tests required
- R-003 (PERF): Login slow, P=2 × I=2 = 4 (MEDIUM) → P1 tests

**Coverage Plan:**

| Requirement         | Test Level | Priority | Test Count |
| ------------------- | ---------- | -------- | ---------- |
| User registration   | E2E        | P0       | 1          |
| Password validation | Unit       | P0       | 5          |
| Login flow          | E2E        | P0       | 1          |
| Session creation    | API        | P0       | 2          |
| Password reset      | E2E        | P1       | 1          |
| Email verification  | E2E        | P1       | 1          |
| Remember me         | E2E        | P2       | 1          |

**Total:** 12 tests (P0: 9, P1: 2, P2: 1)

**Effort Estimate:**

- P0: 9 tests × 2h = 18 hours
- P1: 2 tests × 1h = 2 hours
- P2: 1 test × 0.5h = 0.5 hours
- **Total: 20.5 hours (~3 days)**

### Related Workflows

- **atdd** - Generate P0 tests from design
- **automate** - Generate P1/P2 tests from design
- **trace** - Validate coverage against design

---

## atdd (Acceptance Test-Driven Development)

### Purpose

Generate failing acceptance tests from story acceptance criteria before implementation. Creates deterministic, production-quality tests using BDD patterns and knowledge base best practices.

**Agent:** TEA (Test Architect)
**When to Run:** Before dev-story (per story)
**Duration:** 30-90 minutes per story
**Required:** Recommended for P0/P1 stories

### When to Use

Run **before implementing a story** to create failing tests first.

**Trigger Points:**

- After create-story workflow
- Before dev-story workflow
- For P0/P1 stories (required)
- For P2/P3 stories (optional)

**Workflow Sequence:**

```
create-story → atdd (failing tests) → dev-story (make tests pass) → code-review
```

### Test-Driven Development Approach

**Red-Green-Refactor Cycle:**

1. **Red**: Write failing test (atdd workflow)
2. **Green**: Make test pass (dev-story workflow)
3. **Refactor**: Improve code (dev-story workflow)

**Benefits:**

- Tests define behavior first
- Implementation guided by tests
- Higher confidence in correctness
- Better test quality (not retrofitted)

### Process Overview

**Phase 1: Story Loading (Steps 1-2)**

- Load story file
- Load story-context.xml
- Extract acceptance criteria

**Phase 2: Test Planning (Steps 3-4)**

- Map AC to test levels (E2E, API, Component, Unit)
- Identify test scenarios (happy path, sad path, edge cases)
- Plan test fixtures and data

**Phase 3: Test Generation (Steps 5-8)**

- Generate E2E tests (critical user journeys)
- Generate API tests (business logic validation)
- Generate Component tests (UI behavior)
- Generate Unit tests (pure logic)

**Phase 4: Quality Validation (Steps 9-10)**

- Apply knowledge base patterns
- Ensure Given-When-Then structure
- Use data-testid selectors
- Network-first patterns
- No hard waits or flaky patterns

**Phase 5: Execution (Step 11)**

- Run tests (should fail - RED)
- Verify tests fail for right reasons
- Document expected behavior

### Test Generation Modes

**1. AI Generation (Default)**

- TEA generates tests using knowledge base
- Fast, consistent, high quality
- Best for standard patterns

**2. Recording Mode (MCP-Enhanced)**

- Interactive browser recording
- TEA records user actions
- Best for complex UI flows
- Requires Playwright MCP server

**Selection Logic:**

- Simple CRUD, standard forms → AI generation
- Complex wizards, drag-drop → Recording mode
- API-only → AI generation (no UI to record)

### Inputs

Required:

- story-{epic}.{num}-{title}.md
- story-{epic}.{num}-context.xml

Optional:

- test-design-epic-{N}.md (risk/priority context)
- Playwright MCP (for recording mode)

### Outputs

**Test Files Created:**

- `/tests/e2e/{story-id}-{feature}.spec.ts` (E2E tests)
- `/tests/api/{story-id}-{feature}.api.spec.ts` (API tests)
- `/tests/component/{ComponentName}.test.tsx` (Component tests)
- `/tests/unit/{module}.test.ts` (Unit tests)

**Supporting Files:**

- `/tests/support/fixtures/{feature}.fixture.ts` (if needed)
- `/tests/support/factories/{entity}.factory.ts` (if needed)

**Test Structure (Example E2E):**

```typescript
// tests/e2e/1.2-login.spec.ts
import { test, expect } from '@playwright/test';
import { authenticatedUser } from '../support/fixtures/auth.fixture';

test.describe('1.2-E2E-001: User Login Flow', () => {
  test('[P0] should login with valid credentials and redirect to dashboard', async ({ page }) => {
    // GIVEN: User is on login page
    await page.goto('/login');

    // WHEN: User submits valid credentials
    await page.fill('[data-testid="email-input"]', 'user@example.com');
    await page.fill('[data-testid="password-input"]', 'ValidPassword123!');
    await page.click('[data-testid="login-button"]');

    // THEN: User is redirected to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('[P1] should show error message for invalid credentials', async ({ page }) => {
    // GIVEN: User is on login page
    await page.goto('/login');

    // WHEN: User submits invalid credentials
    await page.fill('[data-testid="email-input"]', 'user@example.com');
    await page.fill('[data-testid="password-input"]', 'WrongPassword');
    await page.click('[data-testid="login-button"]');

    // THEN: Error message is displayed
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
    await expect(page).toHaveURL('/login'); // Still on login page
  });
});
```

### Quality Standards Enforced

**All generated tests must:**

- ✅ Use Given-When-Then format
- ✅ Have priority tags ([P0], [P1], [P2], [P3])
- ✅ Use data-testid selectors (not CSS classes)
- ✅ No hard waits (page.waitForTimeout)
- ✅ Network-first pattern (route intercept before navigate)
- ✅ Self-cleaning (fixtures with auto-cleanup)
- ✅ Deterministic (no conditionals, try-catch)
- ✅ Test IDs: {STORY_ID}-{LEVEL}-{SEQ} (e.g., 1.2-E2E-001)

### Related Workflows

- **test-design** - Provides test planning context
- **dev-story** - Makes failing tests pass
- **test-review** - Validates test quality
- **automate** - Expands beyond ATDD tests

---

## automate

### Purpose

Expand test automation coverage by generating comprehensive test suites at appropriate levels (E2E, API, Component, Unit) with supporting infrastructure. Works seamlessly WITH or WITHOUT BMad artifacts.

**Agent:** TEA (Test Architect)
**When to Run:** After dev-story (per story or feature)
**Duration:** 1-3 hours per feature
**Required:** Recommended for comprehensive coverage

### Dual-Mode Operation

**1. BMad-Integrated Mode** (story available):

- Uses story acceptance criteria
- Aligns with test-design priorities
- Expands ATDD tests with edge cases
- **Story enhances coverage but NOT required**

**2. Standalone Mode** (no story):

- Analyzes source code independently
- Identifies coverage gaps automatically
- Works with any project (BMad or non-BMad)
- "Work out of thin air"

**3. Auto-Discover Mode** (no targets):

- Scans codebase for features needing tests
- Prioritizes features with no coverage
- Generates comprehensive test plan

### When to Use

**BMad-Integrated:**

- After dev-story completes
- To expand beyond ATDD tests
- For P1/P2 edge cases and regression

**Standalone:**

- Brownfield project with missing tests
- Non-BMad projects
- Point TEA at any codebase/feature

**Auto-Discover:**

- No specific targets
- Want comprehensive coverage audit
- Identify coverage gaps

### Process Overview

**Phase 1: Mode Detection (Step 1)**

- Check if story file exists
- Check if target feature specified
- Auto-detect mode (BMad/Standalone/Auto-discover)

**Phase 2: Context Loading (Steps 2-3)**

- BMad mode: Load story, tech-spec, test-design
- Standalone: Load source code, existing tests
- Auto-discover: Scan codebase for features

**Phase 3: Gap Analysis (Steps 4-5)**

- Identify coverage gaps (missing tests)
- Prioritize by risk (P0-P3)
- Avoid duplicate coverage

**Phase 4: Test Generation (Steps 6-10)**

- Generate E2E tests (critical paths only)
- Generate API tests (business logic variations)
- Generate Component tests (UI edge cases)
- Generate Unit tests (pure logic edge cases)
- Generate fixtures and factories

**Phase 5: Validation & Healing (Steps 11-13)**

- Run generated tests (if auto_validate enabled)
- Heal failures (if auto_heal_failures enabled)
- Mark unfixable as test.fixme()

### Test Healing Capabilities (NEW)

**Automatic Test Healing:**
When tests fail after generation, TEA can automatically heal them.

**Configuration:** `config.tea_use_mcp_enhancements` (default: true)

- If true + MCP available → MCP-assisted healing
- If true + MCP unavailable → Pattern-based healing
- If false → No healing, document failures

**Pattern-Based Healing** (always available):

1. Parse error messages from test output
2. Match patterns against known failures
3. Apply fixes from healing knowledge fragments:
   - `test-healing-patterns.md` - Common failures
   - `selector-resilience.md` - Selector fixes
   - `timing-debugging.md` - Race condition fixes
4. Re-run tests (max 3 iterations)
5. Mark unfixable as `test.fixme()`

**MCP-Enhanced Healing** (when Playwright MCP available):

- **Interactive debugging** before pattern fixes
- **Visual context** with browser snapshots
- **Live DOM inspection** to find correct selectors
- **Console analysis** for JS errors
- **Network inspection** for API failures

**Example Healing:**

```typescript
// ❌ Original (failing): CSS class selector
await page.locator('.submit-btn').click();

// ✅ Healed: data-testid selector
await page.getByTestId('submit-button').click();
```

### Recording Mode (MCP-Enhanced)

**Complex UI interactions** can be recorded instead of AI-generated.

**When Recording Mode Activates:**

- Complex scenarios: drag-drop, wizards, multi-page flows
- Visual workflows: modals, animations
- Fallback: AI generation (automatic, silent)

**Recording Workflow:**

1. Use `browser_*` tools to interact with UI
2. Capture interactions as test steps
3. Add verifications with `browser_verify_*`
4. Generate test file from recording
5. Enhance with knowledge base patterns

### Inputs

**BMad-Integrated Mode:**

- story file (optional, enhances coverage)
- tech-spec (optional)
- test-design (optional)

**Standalone Mode:**

- target_feature: Feature name or directory (e.g., "user-authentication" or "src/auth/")
- target_files: Specific files (comma-separated)

**Both Modes:**

- Framework config (playwright.config.ts)
- Existing tests (for gap analysis)
- Knowledge base fragments

### Outputs

**Test Files Created:**

- E2E tests: `/tests/e2e/{feature}.spec.ts`
- API tests: `/tests/api/{feature}.api.spec.ts`
- Component tests: `/tests/component/{ComponentName}.test.tsx`
- Unit tests: `/tests/unit/{module}.test.ts`

**Supporting Infrastructure:**

- Fixtures: `/tests/support/fixtures/{feature}.fixture.ts`
- Factories: `/tests/support/factories/{entity}.factory.ts`
- Helpers: `/tests/support/helpers/{utility}.ts`

**Documentation:**

- **automation-summary.md**: Comprehensive report with:
  - Execution mode (BMad/Standalone/Auto-discover)
  - Feature analysis (coverage gaps)
  - Tests created (counts, paths, priorities)
  - Infrastructure created
  - Healing report (if enabled)
  - Next steps

### Example: Standalone Mode

**Input:**

```bash
bmad tea *automate --target-feature "src/auth/"
```

**Output:**

```markdown
# Automation Summary - src/auth/

**Mode:** Standalone (no story)
**Date:** 2025-11-02

## Feature Analysis

**Source Files Analyzed:**

- src/auth/login.ts
- src/auth/session.ts
- src/auth/validation.ts

**Existing Coverage:** 0 tests found

**Coverage Gaps:**

- ❌ No E2E tests for login flow
- ❌ No API tests for /auth/login endpoint
- ❌ No unit tests for validateEmail()

## Tests Created

### E2E Tests (2 tests, P0-P1)

- tests/e2e/user-authentication.spec.ts (87 lines)
  - [P0] Login with valid credentials → Dashboard
  - [P1] Invalid credentials → Error message

### API Tests (3 tests, P1-P2)

- tests/api/auth.api.spec.ts (102 lines)
  - [P1] POST /auth/login - valid → 200 + token
  - [P1] POST /auth/login - invalid → 401
  - [P2] POST /auth/login - missing fields → 400

### Unit Tests (4 tests, P2)

- tests/unit/validation.test.ts (45 lines)
  - [P2] validateEmail - valid formats
  - [P2] validateEmail - invalid formats
  - [P2] validatePassword - strength rules
  - [P2] validatePassword - edge cases

## Infrastructure Created

- Fixtures: tests/support/fixtures/auth.fixture.ts
- Factories: tests/support/factories/user.factory.ts

## Coverage Analysis

**Total:** 9 tests (P0: 1, P1: 4, P2: 4)
**Levels:** E2E: 2, API: 3, Unit: 4

✅ Critical paths covered (E2E + API)
✅ Error cases covered (API)
✅ Edge cases covered (Unit)

## Recommendations

1. **High Priority (P0-P1):**
   - Add E2E test for password reset flow
   - Add API tests for token refresh endpoint

2. **Medium Priority (P2):**
   - Add unit tests for session timeout logic
```

### Related Workflows

- **atdd** - atdd creates P0 tests, automate expands with P1/P2
- **test-design** - Provides priority context
- **trace** - Validates coverage
- **test-review** - Validates quality

---

## ci (CI/CD Pipeline)

### Purpose

Scaffold production-ready CI/CD quality pipeline with test execution, burn-in loops for flaky test detection, parallel sharding, and artifact collection.

**Agent:** TEA (Test Architect)
**When to Run:** Once (after framework setup)
**Duration:** 1-2 hours
**Required:** Recommended for all projects

### When to Use

Run **after framework workflow** to enable continuous integration.

**Trigger Points:**

- After framework setup complete
- Before first sprint
- When ready to enable CI/CD

### Key Features

**1. Burn-In Loop** (flaky test detection):

- Runs tests 10 times consecutively
- Catches non-deterministic failures
- Prevents flaky tests from reaching main

**2. Parallel Sharding** (4 shards):

- 75% time reduction (40 min → 10 min per shard)
- Configurable shard count
- Faster feedback on PRs

**3. Smart Caching**:

- Node modules + browser binaries cached
- 2-5 min savings per run
- Automatic invalidation on dependency changes

**4. Selective Testing**:

- Run only tests affected by code changes
- 50-80% time reduction for focused PRs
- Full suite still runs on main branch

**5. Failure-Only Artifacts**:

- Upload traces/screenshots/videos only on failure
- 90% storage cost reduction
- 30-day retention default

### Process Overview

**Phase 1: Platform Detection (Steps 1-2)**

- Auto-detect CI platform (GitHub Actions, GitLab CI, Circle CI)
- Confirm with user

**Phase 2: Pipeline Configuration (Steps 3-6)**

- Generate CI config file
- Configure parallel sharding (4 jobs)
- Configure burn-in loop (10 iterations)
- Configure caching (dependencies + browsers)
- Configure artifact collection (failure-only)

**Phase 3: Helper Scripts (Steps 7-9)**

- Generate test-changed.sh (selective testing)
- Generate ci-local.sh (local CI mirror)
- Generate burn-in.sh (standalone burn-in)

**Phase 4: Documentation (Step 10)**

- Generate ci.md (pipeline guide)
- Generate ci-secrets-checklist.md (required secrets)

### Inputs

Required:

- Framework config (playwright.config.ts, etc.)
- package.json

Optional:

- .git/config (for platform auto-detection)
- .nvmrc (Node version)

### Outputs

**1. CI Configuration File:**

- `.github/workflows/test.yml` (GitHub Actions)
- `.gitlab-ci.yml` (GitLab CI)

**2. Helper Scripts:**

- `scripts/test-changed.sh`
- `scripts/ci-local.sh`
- `scripts/burn-in.sh`

**3. Documentation:**

- `docs/ci.md`
- `docs/ci-secrets-checklist.md`

### Example: GitHub Actions Pipeline

```yaml
# .github/workflows/test.yml
name: Test

on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e -- --shard=${{ matrix.shard }}/4
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: test-results-${{ matrix.shard }}
          path: test-results/
          retention-days: 30

  burn-in:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - name: Burn-in loop
        run: |
          for i in {1..10}; do
            echo "🔥 Burn-in iteration $i/10"
            npm run test:e2e || exit 1
          done
```

**Performance Targets:**

- Lint: <2 minutes
- Test (per shard): <10 minutes
- Burn-in: <30 minutes
- **Total: <45 minutes** (20× faster than sequential)

### Related Workflows

- **framework** - Must run before ci
- **trace** (Phase 2) - Uses CI results for gate decision

---

## trace (Traceability & Quality Gate)

### Purpose

**Two-phase workflow:** (1) Generate requirements-to-tests traceability matrix, then (2) Make deterministic quality gate decision for deployment readiness.

**Agent:** TEA (Test Architect)
**When to Run:**

- **Phase 1**: After tests written (per story/epic)
- **Phase 2**: Before release (quality gate)
  **Duration:**
- **Phase 1**: 15-30 minutes
- **Phase 2**: 15-30 minutes

### Phase 1: Requirements Traceability

**Purpose:** Map acceptance criteria to tests, identify coverage gaps.

**Process:**

1. Load story file (acceptance criteria)
2. Auto-discover tests related to story
3. Map AC to test cases
4. Classify coverage (FULL, PARTIAL, NONE)
5. Generate traceability matrix

**Output:** `traceability-matrix.md`

**Example:**

```markdown
# Traceability Matrix - Story 1.2

## Coverage Summary

| Priority | Total | FULL | Coverage % | Status  |
| -------- | ----- | ---- | ---------- | ------- |
| P0       | 3     | 3    | 100%       | ✅ PASS |
| P1       | 2     | 2    | 100%       | ✅ PASS |

## Detailed Mapping

### AC-1: User can login with valid credentials

**Tests:**

- 1.2-E2E-001: Login happy path ✅
- 1.2-API-001: POST /auth/login valid creds ✅

**Coverage:** FULL ✅

### AC-2: Invalid credentials show error

**Tests:**

- 1.2-E2E-002: Login with invalid password ✅
- 1.2-API-002: POST /auth/login invalid creds ✅

**Coverage:** FULL ✅

## Gap Analysis

**Critical Gaps:** None ✅
**High Priority Gaps:** None ✅
**Medium Priority Gaps:** None ✅
```

### Phase 2: Quality Gate Decision

**Purpose:** Make PASS/CONCERNS/FAIL/WAIVED decision for deployment.

**Process:**

1. Load traceability results (Phase 1)
2. Load test execution results (CI/CD reports)
3. Load NFR assessment (if exists)
4. Apply deterministic decision rules
5. Generate gate decision document

**Decision Rules:**

**PASS** ✅ (All criteria met):

- P0 coverage = 100%
- P1 coverage ≥ 90%
- P0 pass rate = 100%
- P1 pass rate ≥ 95%
- Security issues = 0
- Critical NFRs met

**CONCERNS** ⚠️ (P0 met, P1 degraded):

- P0 coverage = 100%
- P1 coverage 80-89%
- P1 pass rate 90-94%
- No security issues

**FAIL** ❌ (P0 criteria failed):

- P0 coverage <100%
- P0 pass rate <100%
- Security issues >0
- Critical NFRs failed

**WAIVED** 🔓 (FAIL + business approval):

- FAIL status + VP/CTO approval
- Business justification documented
- Remediation plan with timeline
- **Never waive: security, data corruption**

**Output:** `gate-decision-story-{X}.{X}.md`

**Example:**

```markdown
# Quality Gate Decision: Story 1.2

**Decision:** ✅ PASS
**Date:** 2025-11-02

## Evidence

- P0 Coverage: 100% ✅ (3/3 AC covered)
- P1 Coverage: 100% ✅ (2/2 AC covered)
- P0 Pass Rate: 100% ✅ (5/5 tests passing)
- P1 Pass Rate: 100% ✅ (4/4 tests passing)
- Overall Pass Rate: 100% ✅ (9/9 tests passing)
- Security Issues: 0 ✅

## Next Steps

1. Deploy to staging
2. Monitor for 24 hours
3. Deploy to production
```

### Related Workflows

- **test-design** - Defines P0-P3 priorities
- **atdd** / **automate** - Generate tests that trace validates
- **nfr-assess** - Provides NFR validation for gate

---

## nfr-assess (Non-Functional Requirements)

### Purpose

Assess non-functional requirements (performance, security, reliability, maintainability) against defined thresholds using evidence-based validation.

**Agent:** TEA (Test Architect)
**When to Run:** Before release (after implementation)
**Duration:** 1-2 hours
**Required:** Recommended for releases

### When to Use

Run **before quality gate decision** to validate NFRs.

**Trigger Points:**

- Before release
- Before major deployment
- After performance/security testing

### NFR Categories

**Performance:**

- Response time (p95: 500ms)
- Throughput (100 RPS)
- CPU usage (<70%)
- Memory usage (<80%)

**Security:**

- Security score (≥85/100)
- Critical vulnerabilities (0)
- High vulnerabilities (<3)
- MFA enabled

**Reliability:**

- Uptime (≥99.9%)
- Error rate (<0.1%)
- MTTR (<15 min)
- CI burn-in (100 runs)

**Maintainability:**

- Test coverage (≥80%)
- Code quality (≥85/100)
- Technical debt (<5%)
- Documentation (≥90%)

### Process Overview

**Phase 1: Load Context (Steps 1-2)**

- Load tech-spec/PRD for NFR requirements
- Load test results, metrics, logs

**Phase 2: Assess NFRs (Steps 3-6)**

- Performance assessment (against thresholds)
- Security assessment
- Reliability assessment
- Maintainability assessment

**Phase 3: Evidence Validation (Steps 7-8)**

- Validate evidence exists and is fresh
- Apply deterministic PASS/CONCERNS/FAIL rules

**Phase 4: Reporting (Step 9)**

- Generate NFR assessment report
- Identify quick wins
- Provide recommendations

### Assessment Rules

**PASS** ✅: Evidence exists AND meets/exceeds threshold
**CONCERNS** ⚠️: Threshold unknown OR evidence missing/incomplete OR close to threshold
**FAIL** ❌: Evidence exists BUT does NOT meet threshold

### Example Output

```markdown
# NFR Assessment - Story 1.2

**Overall Status:** PASS ✅

## Performance Assessment

- Response Time p95: PASS ✅ (320ms < 500ms)
- Throughput: PASS ✅ (250 RPS > 100 RPS)

**Evidence:** Load test results (2025-11-02)

## Security Assessment

- Authentication: PASS ✅ (MFA enforced)
- Data Protection: PASS ✅ (AES-256 + TLS 1.3)

**Evidence:** Security audit (2025-11-02)

## Reliability Assessment

- Uptime: PASS ✅ (99.95% > 99.9%)
- Error Rate: PASS ✅ (0.05% < 0.1%)
- CI Burn-in: PASS ✅ (100 consecutive runs, 0 failures)

**Evidence:** Monitoring data (last 7 days), CI logs

## Maintainability Assessment

- Test Coverage: PASS ✅ (87% > 80%)
- Code Quality: PASS ✅ (92/100 > 85/100)

**Evidence:** Coverage report, SonarQube scan

Gate Status: PASS ✅ - All NFRs met
```

### Related Workflows

- **trace** (Phase 2) - Uses NFR assessment in gate decision

---

## test-review

### Purpose

Perform comprehensive quality validation of test code using TEA's knowledge base, detecting flaky patterns, validating structure, and providing actionable feedback.

**Agent:** TEA (Test Architect)
**When to Run:** After test creation (per test file or suite)
**Duration:** 30-60 minutes
**Required:** Recommended for critical tests

### When to Use

Run **after test creation** to validate quality.

**Trigger Points:**

- After atdd workflow
- After automate workflow
- After developer writes tests
- Before code-review workflow
- Periodic quality audits

### Quality Scoring (0-100)

**Score Calculation:**

```
Starting Score: 100

Deductions:
- Critical (P0): -10 points each
- High (P1): -5 points each
- Medium (P2): -2 points each
- Low (P3): -1 point each

Bonus (max +30):
+ Excellent BDD structure: +5
+ Comprehensive fixtures: +5
+ Data factories: +5
+ Network-first pattern: +5
+ Perfect isolation: +5
+ All test IDs present: +5
```

**Quality Grades:**

- **90-100 (A+)**: Excellent - Production-ready
- **80-89 (A)**: Good - Minor improvements
- **70-79 (B)**: Acceptable - Some issues
- **60-69 (C)**: Needs Improvement
- **<60 (F)**: Critical Issues

### Quality Criteria Checked

1. **BDD Format** (Given-When-Then)
2. **Test IDs** ({STORY_ID}-{LEVEL}-{SEQ})
3. **Priority Markers** (P0/P1/P2/P3)
4. **No Hard Waits** (page.waitForTimeout)
5. **Determinism** (no conditionals/try-catch)
6. **Isolation** (tests clean up, no shared state)
7. **Fixture Patterns** (pure function → fixture → mergeTests)
8. **Data Factories** (faker.js, no hardcoded data)
9. **Network-First Pattern** (route before navigate)
10. **Explicit Assertions**
11. **Test Length** (≤300 lines)
12. **Test Duration** (≤1.5 min)
13. **Flakiness Patterns** (tight timeouts, race conditions)

### Example Output

```markdown
# Test Quality Review: login.spec.ts

**Quality Score:** 92/100 (A+ - Excellent)
**Recommendation:** Approve - Production Ready

## Executive Summary

Excellent test quality with comprehensive coverage and best practices.

**Strengths:**
✅ Clear Given-When-Then structure
✅ All test IDs present (1.2-E2E-001, 1.2-E2E-002)
✅ Network-first pattern used consistently
✅ Perfect test isolation with cleanup
✅ Data factories for test data

**Minor Issues:**
⚠️ One test slightly verbose (245 lines) - consider helper function

**Recommendation:** Approve without changes.
```

### Related Workflows

- **atdd** - Review after ATDD generation
- **automate** - Review after automation expansion
- **code-review** - Test quality feeds into overall review

---

## Testing Workflow Integration

### With Implementation Workflows

```
Phase 4: Implementation          Testarch (Parallel)
──────────────────────          ───────────────────

                        → framework (once at start)
                        → test-design (per epic)

create-story            → atdd (P0/P1 failing tests)
story-context
dev-story               → Tests pass (RED → GREEN)
                        → automate (expand P1/P2 coverage)
code-review             → test-review (validate quality)
story-done
                        → trace Phase 1 (coverage check)

Epic complete           → retrospective
                        → nfr-assess (NFRs)
                        → trace Phase 2 (quality gate)
```

### Recommended Testing Strategy

**Level 0-1 Projects:**

- framework (optional)
- atdd (optional, if tests needed)
- Skip test-design, automate

**Level 2 Projects:**

- framework (required)
- test-design (optional)
- atdd (P0 stories)
- automate (optional)
- trace Phase 1 (optional)

**Level 3-4 Projects:**

- framework (required)
- test-design (required)
- atdd (all P0/P1 stories)
- automate (comprehensive coverage)
- ci (required)
- trace Phase 1 (required)
- nfr-assess (before release)
- trace Phase 2 (quality gate)
- test-review (critical tests)

---

## Best Practices

### 1. Test Early, Test Often

Run **atdd before dev-story** for P0/P1 stories. Write failing tests first.

### 2. Use Test Design for Complex Projects

Don't skip test-design for Level 3-4. Risk assessment prevents gaps.

### 3. Trust the Burn-In Loop

Flaky tests are poison. Always run burn-in in CI to catch them.

### 4. Review Test Quality

Don't assume generated tests are perfect. Run test-review for critical tests.

### 5. Make Quality Gates Explicit

Use trace Phase 2 for release decisions. Document gate criteria.

### 6. Heal Failures Automatically

Enable auto-healing for faster iteration. Pattern-based healing works without MCP.

---

## Summary

Testarch workflows provide comprehensive testing infrastructure:

| Workflow            | Frequency         | Critical For            |
| ------------------- | ----------------- | ----------------------- |
| **framework**       | Once              | All projects with tests |
| **test-design**     | Per epic/project  | Level 3-4 planning      |
| **atdd**            | Per story (P0/P1) | Test-driven development |
| **automate**        | Per feature       | Comprehensive coverage  |
| **ci**              | Once              | Continuous integration  |
| **trace** (Phase 1) | Per story/epic    | Coverage validation     |
| **trace** (Phase 2) | Before release    | Quality gate            |
| **nfr-assess**      | Before release    | NFR validation          |
| **test-review**     | As needed         | Test quality            |

**Key Takeaway:** Testing is not a phase—it's a continuous practice integrated throughout implementation. Use testarch workflows to ensure comprehensive, high-quality test coverage.
