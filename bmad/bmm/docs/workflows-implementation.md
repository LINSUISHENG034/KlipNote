# BMM Implementation Workflows (Phase 4)

**Reading Time:** ~20 minutes

## Overview

Phase 4 (Implementation) workflows manage the iterative sprint-based development cycle. This phase uses a **story-centric workflow** where each story moves through a defined lifecycle from creation to completion.

**Key principle:** One story at a time, move it through the entire lifecycle before starting the next.

## Quick Reference

| Workflow              | Agent     | Duration       | Purpose                              |
| --------------------- | --------- | -------------- | ------------------------------------ |
| **sprint-planning**   | SM        | 30-60 min      | Initialize sprint tracking file      |
| **epic-tech-context** | Architect | 15-30 min/epic | Epic-specific technical guidance     |
| **create-story**      | SM        | 10-20 min      | Create next story from epics         |
| **story-context**     | PM        | 10-15 min      | Assemble dynamic story context       |
| **dev-story**         | DEV       | 2-8 hours      | Implement story with tests           |
| **code-review**       | DEV       | 30-60 min      | Senior dev review of completed story |
| **correct-course**    | SM        | 30-90 min      | Handle mid-sprint changes            |
| **retrospective**     | SM        | 60-90 min      | Post-epic review and lessons         |
| **workflow-status**   | All       | 2-5 min        | Check "what should I do now?"        |
| **document-project**  | Analyst   | 1-3 hours      | Document brownfield projects         |

---

## Understanding the Implementation Phase

### Story Lifecycle

Every story moves through this lifecycle:

```
1. TODO (Not Started)
   ↓ [sprint-planning creates status file]

2. IN PROGRESS (Being Implemented)
   ↓ [create-story generates story file]
   ↓ [story-context assembles context]
   ↓ [dev-story implements with tests]

3. READY FOR REVIEW (Implementation Complete)
   ↓ [code-review validates quality]

4. DONE (Accepted)
   ↓ [story-done marks complete]
   ↓ [Repeat for next story]
```

### Sprint-Based Development Model

**Sprint Structure:**

- **Sprint 0 (Planning)**: Phases 1-3 complete
- **Sprint 1**: Epic 1 stories (P0/P1)
- **Sprint 2**: Epic 2 stories (P0/P1)
- **Sprint 3**: Epic 3+ stories (P0/P1)
- **Sprint N**: P2/P3 stories, polish

**Typical Sprint Timeline:**

- Week 1-2: Epic 1 implementation
- Week 3-4: Epic 2 implementation
- Week 5-6: Epic 3 implementation
- Week 7+: Refinement, P2/P3, polish

### Multi-Agent Workflow

Phase 4 involves coordination between agents:

| Agent         | Primary Workflows                                            | Role                        |
| ------------- | ------------------------------------------------------------ | --------------------------- |
| **SM**        | sprint-planning, create-story, correct-course, retrospective | Orchestration, tracking     |
| **Architect** | epic-tech-context                                            | Technical guidance per epic |
| **PM**        | story-context                                                | Context assembly            |
| **DEV**       | dev-story, code-review                                       | Implementation, quality     |
| **Analyst**   | document-project                                             | Documentation (brownfield)  |

---

## sprint-planning

### Purpose

Generate and manage the sprint status tracking file for Phase 4 implementation, extracting all epics and stories from epic files and tracking their status through the development lifecycle.

**Agent:** SM (Scrum Master)
**Phase:** 4 (Implementation)
**Required:** Yes (first step of Phase 4)
**Typical Duration:** 30-60 minutes

### When to Use

Run **once at the start of Phase 4** after solutioning-gate-check passes (or after PRD for Level 0-2).

**Trigger Points:**

- solutioning-gate-check PASS (Level 3-4)
- PRD complete (Level 2)
- tech-spec complete (Level 0-1)

### Purpose of Sprint Planning

**Creates:**

- Sprint status tracking file (`sprint-status.yaml`)
- Story queue (ordered by priority and dependencies)
- Epic-level tracking
- Sprint assignments

**Enables:**

- workflow-status to answer "what's next?"
- Progress tracking throughout implementation
- Dependency management
- Velocity measurement

### Process Overview

**Phase 1: Context Loading (Step 1)**

- Load epics.md
- Load individual epic files
- Load architecture.md (if exists)
- Extract all stories

**Phase 2: Story Extraction (Steps 2-3)**

- Parse stories from epic files
- Extract acceptance criteria
- Identify priorities (P0/P1/P2/P3)
- Extract dependencies

**Phase 3: Sprint Assignment (Steps 4-5)**

- Group stories by epic
- Sequence by priority and dependencies
- Assign to sprints (Sprint 1, 2, 3, etc.)
- Calculate sprint capacity estimates

**Phase 4: Status File Creation (Step 6)**

- Generate sprint-status.yaml
- Initialize all stories as TODO
- Document sprint plan
- Save to output folder

### Inputs

Required:

- epics.md
- Epic files (epic-1-_.md, epic-2-_.md, etc.)

Optional:

- architecture.md (for technical dependencies)
- Team velocity data (for sprint sizing)

### Outputs

**Primary Output:** `sprint-status.yaml`

**File Structure:**

```yaml
metadata:
  project_name: 'E-Commerce Platform'
  total_epics: 3
  total_stories: 24
  current_sprint: 1
  sprint_start_date: '2025-11-02'

sprints:
  sprint_1:
    name: 'Epic 1: Authentication'
    start_date: '2025-11-02'
    end_date: '2025-11-15'
    capacity_points: 40
    stories:
      - id: '1.1'
        title: 'User can register with email'
        status: 'TODO'
        priority: 'P0'
        epic: 1
        estimated_hours: 8
        assigned_to: null
        dependencies: []
      - id: '1.2'
        title: 'User can login with email'
        status: 'TODO'
        priority: 'P0'
        epic: 1
        estimated_hours: 6
        assigned_to: null
        dependencies: ['1.1']

  sprint_2:
    name: 'Epic 2: Product Catalog'
    # ...

story_queue:
  - '1.1' # No dependencies, P0
  - '1.2' # Depends on 1.1, P0
  - '1.3' # Depends on 1.2, P0
  # ...

epics:
  - id: 1
    name: 'Authentication'
    total_stories: 8
    completed_stories: 0
    status: 'IN_PROGRESS'
  - id: 2
    name: 'Product Catalog'
    total_stories: 10
    completed_stories: 0
    status: 'TODO'
  - id: 3
    name: 'Shopping Cart'
    total_stories: 6
    completed_stories: 0
    status: 'TODO'
```

### Example Scenario

**Input:** 3 epics with 24 total stories

**Output:**

- **Sprint 1**: Epic 1 (8 stories, 2 weeks)
- **Sprint 2**: Epic 2 (10 stories, 2 weeks)
- **Sprint 3**: Epic 3 (6 stories, 1 week)

**Story Queue:**

1. Story 1.1 (P0, no deps) → Start here
2. Story 1.2 (P0, deps: 1.1)
3. Story 1.3 (P0, deps: 1.2)
4. Story 2.1 (P0, no deps) → Can parallelize with 1.x
   ...

### Related Workflows

- **solutioning-gate-check** (Phase 3) - Must PASS before sprint-planning
- **workflow-status** - Uses sprint-status.yaml to answer "what's next?"
- **create-story** - Uses story_queue to determine next story

---

## epic-tech-context

### Purpose

Generate epic-specific technical context document that provides implementation guidance, patterns, and technical decisions for a single epic. Bridges architecture and story implementation.

**Agent:** Architect
**Phase:** 4 (Implementation)
**Required:** Optional (recommended for Level 3-4)
**Typical Duration:** 15-30 minutes per epic

### When to Use

Run **once per epic** before starting epic stories.

**Trigger Points:**

- Before implementing first story of an epic
- When starting a new epic in a sprint
- When architecture guidance is needed

**Skip if:**

- Level 0-1 (no epics)
- Level 2 (simple epics, architecture is straightforward)

### Purpose of Epic Tech Context

**Provides:**

- Epic-specific technical guidance
- Code patterns and examples
- Integration points
- Testing strategy for epic
- Epic-level architectural decisions

**Prevents:**

- Re-reading entire architecture.md for each story
- Inconsistent implementations within epic
- Missing epic-level integration patterns

### Process Overview

**Phase 1: Context Loading (Step 1)**

- Load architecture.md
- Load epic file (epic-X-\*.md)
- Load sprint-status.yaml
- Identify epic stories

**Phase 2: Technical Extraction (Steps 2-4)**

- Extract relevant architecture sections for epic
- Identify epic-specific ADRs
- Determine code patterns
- Identify integration points

**Phase 3: Implementation Guidance (Steps 5-7)**

- Define directory structure for epic
- Specify testing approach
- Provide code examples
- Document epic-level constants/config

**Phase 4: Documentation (Step 8)**

- Generate epic-tech-context.md
- Save to output folder
- Update sprint-status.yaml with context path

### Inputs

Required:

- architecture.md
- epic-X-\*.md (specific epic file)
- sprint-status.yaml

### Outputs

**Primary Output:** `epic-{N}-tech-context.md`

**Document Structure:**

1. Epic Overview
2. Relevant Architecture Decisions
   - ADRs applicable to this epic
   - Technology selections
3. Directory Structure
   - Files to create/modify
   - Module organization
4. Code Patterns
   - Epic-specific patterns
   - Code examples
5. Integration Points
   - APIs to create/consume
   - Database interactions
   - Third-party services
6. Testing Strategy
   - Test levels for epic (E2E, API, Unit)
   - Test fixtures needed
   - Mock strategies
7. Configuration
   - Environment variables
   - Feature flags
   - Constants

### Example: Epic 1 Tech Context (Authentication)

```markdown
# Epic 1 Tech Context: Authentication

## Architecture Decisions

**ADR-001: Use NextAuth.js**

- All stories in this epic use NextAuth.js
- Database adapter: PostgreSQL (via Prisma)
- Session strategy: Database sessions (not JWT)

**ADR-003: Password Security**

- Use bcrypt with 12 rounds
- Minimum password length: 8 characters
- Require: uppercase, lowercase, number

## Directory Structure
```

/pages/api/auth/
[...nextauth].ts # Story 1.1
register.ts # Story 1.2
verify-email.ts # Story 1.3

/lib/auth/
validation.ts # Story 1.2
email-service.ts # Story 1.3

/prisma/schema.prisma
User model # Story 1.1
Session model # Story 1.1

````

## Code Patterns

**User Registration (Story 1.2):**
```typescript
// /lib/auth/validation.ts
export const validatePassword = (password: string) => {
  const minLength = 8;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);

  if (password.length < minLength) {
    throw new Error('Password too short');
  }
  // ...
};
````

## Integration Points

**Database:**

- Create User table with Prisma migration (Story 1.1)
- Create Session table with Prisma migration (Story 1.1)

**Third-Party Services:**

- SendGrid for email verification (Story 1.3)
  - API Key: SENDGRID_API_KEY env variable
  - From email: no-reply@example.com

## Testing Strategy

**E2E Tests:**

- Story 1.1: Full registration flow
- Story 1.2: Login flow
- Story 1.3: Email verification flow

**API Tests:**

- All /api/auth/\* endpoints
- Error cases: duplicate email, invalid password

**Unit Tests:**

- validation.ts functions
- email-service.ts functions

**Test Fixtures:**

- Create `tests/fixtures/auth.fixture.ts`
- Provide: createTestUser(), loginTestUser(), cleanupTestUser()

## Configuration

**Environment Variables:**

```
DATABASE_URL=postgresql://...
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<generate-random-string>
SENDGRID_API_KEY=SG.xxx
```

**Constants:**

```typescript
// /lib/auth/constants.ts
export const PASSWORD_MIN_LENGTH = 8;
export const BCRYPT_ROUNDS = 12;
export const EMAIL_VERIFICATION_EXPIRY_HOURS = 24;
```

````

### Related Workflows
- **architecture** (Phase 3) - Source of technical guidance
- **story-context** - Uses epic-tech-context as input
- **dev-story** - References epic-tech-context during implementation

---

## create-story

### Purpose
Create the next user story markdown from epics/PRD and architecture, using a standard template and saving to the stories folder.

**Agent:** SM (Scrum Master)
**Phase:** 4 (Implementation)
**Required:** Yes (for each story)
**Typical Duration:** 10-20 minutes per story

### When to Use
Run **before implementing each story** to generate story file.

**Trigger Points:**
- Before starting work on a new story
- When story_queue identifies next story
- After completing previous story

### Process Overview

**Phase 1: Story Selection (Step 1)**
- Load sprint-status.yaml
- Read story_queue
- Select next story (first in queue with dependencies met)

**Phase 2: Story Extraction (Steps 2-3)**
- Load epic file for selected story
- Extract story details
- Extract acceptance criteria
- Extract dependencies

**Phase 3: Context Gathering (Steps 4-5)**
- Load PRD/GDD for product context
- Load architecture for technical context
- Load epic-tech-context (if exists)

**Phase 4: Story File Creation (Step 6)**
- Generate story markdown using template
- Include acceptance criteria
- Include technical notes
- Save to stories/ folder

**Phase 5: Status Update (Step 7)**
- Update sprint-status.yaml
- Move story from TODO → IN PROGRESS
- Update workflow-status.md

### Inputs
Required:
- sprint-status.yaml (story queue)
- epic-X-*.md (for story details)
- PRD.md or GDD.md

Optional:
- architecture.md
- epic-tech-context.md

### Outputs

**Primary Output:** `story-{epic}.{num}-{title}.md`

**Story File Structure:**
```markdown
# Story {Epic}.{Num}: {Title}

**Epic:** {Epic Name}
**Priority:** P0/P1/P2/P3
**Status:** IN PROGRESS
**Estimated Hours:** {Hours}
**Dependencies:** {Story IDs or "None"}

## User Story

As a {user type},
I want to {action},
So that {benefit}.

## Acceptance Criteria

- [ ] AC-1: {Criterion}
- [ ] AC-2: {Criterion}
- [ ] AC-3: {Criterion}

## Technical Notes

{From architecture/epic-tech-context}

## Implementation Checklist

- [ ] Read story-context.xml for dynamic context
- [ ] Implement feature code
- [ ] Write tests (unit, integration, E2E as needed)
- [ ] Update documentation
- [ ] Run tests locally
- [ ] Verify acceptance criteria
- [ ] Mark story as READY FOR REVIEW

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] No regressions in existing features
````

### Example: Story 1.2 - User Can Login

```markdown
# Story 1.2: User Can Login with Email

**Epic:** Epic 1 - Authentication
**Priority:** P0
**Status:** IN PROGRESS
**Estimated Hours:** 6
**Dependencies:** Story 1.1 (User Registration)

## User Story

As a registered user,
I want to login with my email and password,
So that I can access my account.

## Acceptance Criteria

- [ ] AC-1: User can enter email and password on login page
- [ ] AC-2: Valid credentials redirect to dashboard
- [ ] AC-3: Invalid credentials show error message
- [ ] AC-4: Error message does not reveal if email exists (security)
- [ ] AC-5: Login creates session that persists across page refreshes

## Technical Notes

**From Architecture (ADR-001):**

- Use NextAuth.js with database session strategy
- Session stored in PostgreSQL via Prisma

**From Epic Tech Context:**

- Implement /pages/api/auth/[...nextauth].ts
- Use bcrypt.compare() for password validation
- Return generic error for security (don't reveal "email not found" vs "wrong password")

## Implementation Checklist

- [ ] Read story-context.xml
- [ ] Create /pages/login.tsx
- [ ] Configure NextAuth.js credentials provider
- [ ] Implement password comparison logic
- [ ] Write E2E test: Valid login → Dashboard
- [ ] Write E2E test: Invalid login → Error
- [ ] Write API test: POST /api/auth/callback/credentials
- [ ] Verify AC-1 through AC-5
- [ ] Mark READY FOR REVIEW

## Definition of Done

- [ ] Login page exists and is styled
- [ ] Valid credentials authenticate successfully
- [ ] Invalid credentials show error
- [ ] Session persists across page loads
- [ ] Tests pass (2 E2E, 3 API)
- [ ] Code reviewed
```

### Related Workflows

- **sprint-planning** - Creates story_queue
- **story-context** - Run after create-story
- **dev-story** - Implements the story

---

## story-context

### Purpose

Assemble dynamic story context XML by pulling latest documentation and existing code/library artifacts relevant to a drafted story.

**Agent:** PM (Project Manager)
**Phase:** 4 (Implementation)
**Required:** Yes (before implementing story)
**Typical Duration:** 10-15 minutes per story

### When to Use

Run **after create-story** and **before dev-story** for each story.

**Trigger Points:**

- Immediately after create-story generates story file
- Before DEV agent starts implementation

### Purpose of Story Context

**Problem Without Context:**

- DEV agent re-reads entire PRD, architecture, epic files (100+ pages)
- Slow context loading
- Irrelevant information clutters thinking

**Solution With Context:**

- PM assembles **only relevant** context for this story
- DEV agent receives focused, story-specific information
- Fast, targeted implementation

### Process Overview

**Phase 1: Story Loading (Step 1)**

- Load story file (story-{epic}.{num}-{title}.md)
- Extract story ID, epic, dependencies
- Extract acceptance criteria

**Phase 2: Documentation Context (Steps 2-4)**

- Load relevant PRD/GDD sections
- Load relevant architecture sections
- Load epic-tech-context (if exists)
- Load dependent story files

**Phase 3: Code Context (Steps 5-6)**

- Identify existing code files related to story
- Load relevant library code (models, services, utils)
- Load related test files

**Phase 4: Context Assembly (Step 7)**

- Generate story-context.xml
- Organize context by type (docs, code, tests)
- Include only relevant sections
- Save to output folder

### Inputs

Required:

- story-{epic}.{num}-{title}.md

Optional (loaded as needed):

- PRD.md or GDD.md
- architecture.md
- epic-tech-context.md
- Existing codebase files

### Outputs

**Primary Output:** `story-{epic}.{num}-context.xml`

**XML Structure:**

```xml
<story-context>
  <story id="1.2" epic="1" title="User Can Login">
    <acceptance-criteria>
      <criterion id="AC-1">User can enter email and password on login page</criterion>
      <criterion id="AC-2">Valid credentials redirect to dashboard</criterion>
      <!-- ... -->
    </acceptance-criteria>
  </story>

  <product-context>
    <section source="PRD.md" name="Authentication Requirements">
      <!-- Relevant PRD excerpt -->
    </section>
  </product-context>

  <architecture-context>
    <adr id="ADR-001" title="Use NextAuth.js">
      <!-- Full ADR content -->
    </adr>
    <section source="architecture.md" name="Authentication Architecture">
      <!-- Relevant architecture excerpt -->
    </section>
  </architecture-context>

  <epic-context>
    <section source="epic-1-tech-context.md">
      <!-- Epic-specific technical guidance -->
    </section>
  </epic-context>

  <code-context>
    <file path="/prisma/schema.prisma">
      <!-- Existing User model -->
    </file>
    <file path="/lib/auth/validation.ts">
      <!-- Existing validation functions -->
    </file>
  </code-context>

  <dependency-context>
    <story id="1.1" title="User Can Register">
      <!-- Story 1.1 summary for context -->
    </story>
  </dependency-context>
</story-context>
```

### Example: Story 1.2 Context Assembly

**Story 1.2: User Can Login**

**Context Assembled:**

1. **Product Context** (from PRD):
   - Authentication requirements section (2 pages)
   - User personas: Primary user is buyer

2. **Architecture Context** (from architecture.md):
   - ADR-001: Use NextAuth.js (full ADR)
   - Authentication Architecture section (1 page)

3. **Epic Context** (from epic-1-tech-context.md):
   - Code patterns for login
   - Integration points (NextAuth.js config)
   - Testing strategy

4. **Code Context** (existing files):
   - `/prisma/schema.prisma` - User and Session models
   - `/lib/auth/validation.ts` - Password validation (from Story 1.1)
   - `/pages/api/auth/[...nextauth].ts` - Auth config (created in Story 1.1)

5. **Dependency Context** (Story 1.1):
   - Summary: User registration creates User in DB
   - Dependency: User table must exist

**Result:** DEV agent receives 8-10 pages of **focused** context instead of 100+ pages of full documentation.

### Related Workflows

- **create-story** - Creates story file that story-context uses
- **dev-story** - Consumes story-context.xml

---

## dev-story

### Purpose

Execute a story by implementing tasks/subtasks, writing tests, validating, and updating the story file per acceptance criteria.

**Agent:** DEV (Developer)
**Phase:** 4 (Implementation)
**Required:** Yes (for each story)
**Typical Duration:** 2-8 hours per story (varies by complexity)

### When to Use

Run **after story-context** to implement the story.

**Trigger Points:**

- After story-context.xml is generated
- When story status is IN PROGRESS
- For each story in story_queue

### Process Overview

**Phase 1: Context Loading (Step 1)**

- Load story file
- Load story-context.xml
- Review acceptance criteria
- Review technical notes

**Phase 2: Implementation Planning (Steps 2-3)**

- Break story into tasks
- Identify files to create/modify
- Plan test strategy
- Estimate implementation approach

**Phase 3: Implementation (Steps 4-6)**

- Write code to satisfy acceptance criteria
- Follow architecture decisions
- Apply code patterns from epic-tech-context
- Write tests (unit, integration, E2E as needed)

**Phase 4: Validation (Steps 7-8)**

- Run tests locally
- Verify all acceptance criteria met
- Check for regressions
- Ensure code quality

**Phase 5: Documentation (Step 9)**

- Update story file (check off AC items)
- Document any deviations
- Mark story as READY FOR REVIEW
- Update sprint-status.yaml

### Inputs

Required:

- story-{epic}.{num}-{title}.md
- story-{epic}.{num}-context.xml

### Outputs

- Implementation code (multiple files)
- Test files
- Updated story file (AC checked off)
- Updated sprint-status.yaml (status: READY FOR REVIEW)

### Example: Implementing Story 1.2 (Login)

**Phase 1: Planning**
Tasks identified:

1. Create /pages/login.tsx (UI)
2. Configure NextAuth credentials provider
3. Implement password verification logic
4. Write E2E test: Valid login
5. Write E2E test: Invalid login
6. Write API test: /api/auth/callback/credentials

**Phase 2: Implementation**
Files created/modified:

- `/pages/login.tsx` (new)
- `/pages/api/auth/[...nextauth].ts` (modified - add credentials provider)
- `/lib/auth/password.ts` (new - password verification)
- `/tests/e2e/auth-login.spec.ts` (new)
- `/tests/api/auth-api.spec.ts` (modified - add login tests)

**Phase 3: Testing**

```bash
npm run test:e2e
npm run test:api
npm run test:unit
```

All tests pass ✅

**Phase 4: Verification**

- [x] AC-1: Login page exists with email/password inputs
- [x] AC-2: Valid credentials → Dashboard
- [x] AC-3: Invalid credentials → Error message
- [x] AC-4: Error message generic (security)
- [x] AC-5: Session persists across page refreshes

**Phase 5: Documentation**
Update story file:

```markdown
## Acceptance Criteria

- [x] AC-1: User can enter email and password on login page
- [x] AC-2: Valid credentials redirect to dashboard
- [x] AC-3: Invalid credentials show error message
- [x] AC-4: Error message does not reveal if email exists (security)
- [x] AC-5: Login creates session that persists across page refreshes

## Implementation Summary

Files Created:

- /pages/login.tsx
- /lib/auth/password.ts
- /tests/e2e/auth-login.spec.ts

Files Modified:

- /pages/api/auth/[...nextauth].ts
- /tests/api/auth-api.spec.ts

Tests Added:

- 2 E2E tests (valid/invalid login)
- 3 API tests (credentials endpoint)

**Status:** READY FOR REVIEW
```

### Related Workflows

- **story-context** - Provides focused context
- **code-review** - Next step after implementation
- **correct-course** - If changes needed mid-story

---

## code-review

### Purpose

Perform a Senior Developer code review on a completed story flagged Ready for Review, leveraging story-context, epic tech-spec, repo docs, MCP servers for latest best-practices, and web search as fallback.

**Agent:** DEV (Senior Developer persona)
**Phase:** 4 (Implementation)
**Required:** Recommended (especially for P0/P1 stories)
**Typical Duration:** 30-60 minutes per story

### When to Use

Run **after dev-story** when story status is READY FOR REVIEW.

**Trigger Points:**

- Story status: READY FOR REVIEW
- Before marking story as DONE
- For P0/P1 stories (required)
- For P2/P3 stories (optional but recommended)

### Process Overview

**Phase 1: Context Loading (Step 1)**

- Load story file
- Load story-context.xml
- Load implementation files
- Load test files

**Phase 2: Review Criteria (Steps 2-5)**

- **Acceptance Criteria**: All AC met?
- **Architecture Alignment**: Follows architecture decisions?
- **Code Quality**: Readable, maintainable, follows conventions?
- **Test Coverage**: Sufficient tests, tests passing?
- **Best Practices**: Uses latest framework patterns?

**Phase 3: Knowledge Loading (Steps 6-7)**

- Load repository documentation (CONTRIBUTING.md, CODE_STYLE.md)
- Use MCP servers for framework best practices (if available)
- Web search for latest patterns (fallback)

**Phase 4: Review Execution (Steps 8-10)**

- Review each file changed
- Identify issues (critical, high, medium, low)
- Suggest improvements
- Verify tests

**Phase 5: Review Report (Step 11)**

- Generate code-review.md
- Append to story file
- Update sprint-status.yaml

### Review Criteria

**Acceptance Criteria Validation:**

- [ ] All AC items checked off in story file
- [ ] AC validated through tests
- [ ] AC validated manually (if needed)

**Architecture Alignment:**

- [ ] Follows ADRs
- [ ] Uses specified technology choices
- [ ] Follows directory structure conventions
- [ ] Follows code patterns from epic-tech-context

**Code Quality:**

- [ ] Readable and maintainable
- [ ] Follows repository conventions
- [ ] No code smells (long functions, god classes, etc.)
- [ ] Appropriate error handling
- [ ] Security best practices followed

**Test Coverage:**

- [ ] Tests exist for all AC
- [ ] Tests pass locally
- [ ] Edge cases covered
- [ ] Tests follow framework best practices
- [ ] No flaky tests

**Best Practices:**

- [ ] Uses latest framework patterns
- [ ] Avoids deprecated APIs
- [ ] Performance considerations addressed
- [ ] Accessibility requirements met (if applicable)

### Inputs

Required:

- story-{epic}.{num}-{title}.md (with READY FOR REVIEW status)
- story-{epic}.{num}-context.xml
- Implementation files (code)
- Test files

Optional:

- Repository documentation (CONTRIBUTING.md, CODE_STYLE.md)
- MCP servers for best practices
- Web search for latest patterns

### Outputs

**Primary Output:** Code review appended to story file

**Review Structure:**

````markdown
---

## Code Review - {Date}

**Reviewer:** DEV (Senior Developer)
**Status:** APPROVED / REQUEST CHANGES / APPROVED WITH COMMENTS

### Summary

{Overall assessment}

### Acceptance Criteria Validation

- [x] AC-1: Validated ✅
- [x] AC-2: Validated ✅
- [x] AC-3: Validated ✅
- [x] AC-4: Validated ✅
- [x] AC-5: Validated ✅

### Architecture Alignment

✅ Follows ADR-001 (NextAuth.js)
✅ Uses database session strategy
✅ Follows epic-tech-context patterns

### Code Quality Issues

**Critical Issues (Must Fix):**
None

**High Priority (Should Fix Before Merge):**

1. /lib/auth/password.ts:15 - Use constant for bcrypt rounds instead of magic number

   ```typescript
   // Current:
   const hash = await bcrypt.hash(password, 12);

   // Suggested:
   import { BCRYPT_ROUNDS } from './constants';
   const hash = await bcrypt.hash(password, BCRYPT_ROUNDS);
   ```
````

**Medium Priority (Address in Follow-up):**

1. /pages/login.tsx:42 - Consider extracting form validation to custom hook
2. Add JSDoc comments to public functions in /lib/auth/password.ts

**Low Priority (Nice to Have):**

1. Consider using react-hook-form for login form (reduces boilerplate)

### Test Coverage

✅ E2E tests cover happy and sad paths
✅ API tests cover error cases
⚠️ Consider adding unit test for password validation edge cases

### Best Practices

✅ Uses latest Next.js 14 patterns
✅ Follows React best practices
✅ Accessibility: Form has labels and error messages

### Recommendation

**APPROVED WITH COMMENTS** - Address high priority issue #1, then merge.

Medium/low priority items can be addressed in future stories.

````

### Review Outcomes

**APPROVED** ✅
- All criteria met
- No critical/high issues
- Story can be marked DONE
- **Action**: Run story-done workflow

**APPROVED WITH COMMENTS** ✅⚠️
- Minor issues noted
- Suggestions for improvement
- Story can be marked DONE
- **Action**: Address comments in follow-up (optional)

**REQUEST CHANGES** ❌
- Critical or high-priority issues found
- Changes required before merge
- Story remains READY FOR REVIEW
- **Action**: Fix issues, re-request review

### Related Workflows
- **dev-story** - Implementation that's being reviewed
- **story-done** - Next step if approved
- **correct-course** - If significant changes needed

---

## correct-course

### Purpose
Navigate significant changes during sprint execution by analyzing impact, proposing solutions, and routing for implementation.

**Agent:** SM (Scrum Master)
**Phase:** 4 (Implementation)
**Required:** As needed
**Typical Duration:** 30-90 minutes

### When to Use
Run when **significant changes** occur mid-sprint:

**Trigger Scenarios:**
- New requirements discovered during implementation
- Architecture decision needs revision
- Story dependencies change
- External factors impact sprint (API changes, platform updates)
- Critical bug discovered requiring immediate attention

**Don't Use For:**
- Minor clarifications → Clarify in story file
- Small scope adjustments → Adjust AC in story
- Typical development blockers → Resolve within team

### Process Overview

**Phase 1: Change Analysis (Steps 1-3)**
- Identify change type (requirements, technical, external)
- Assess impact (stories, epics, architecture)
- Determine urgency (blocking, high, medium, low)

**Phase 2: Impact Assessment (Steps 4-6)**
- Stories affected
- Epics affected
- Architecture changes needed
- Timeline impact

**Phase 3: Solution Proposal (Steps 7-9)**
- **Option A**: Adjust scope (remove stories, defer features)
- **Option B**: Adjust architecture (revise decisions)
- **Option C**: Adjust timeline (extend sprint)
- **Option D**: Combination approach

**Phase 4: Decision and Routing (Steps 10-12)**
- Consult stakeholders (if needed)
- Select solution
- Route to appropriate workflow:
  - Requirements change → Update PRD → Re-run create-story
  - Architecture change → Update architecture → Re-run epic-tech-context
  - Story change → Update story file → Continue dev-story
- Update sprint-status.yaml

### Change Types

**Requirements Change:**
- New AC discovered
- AC invalidated by new information
- Feature scope expansion/reduction

**Technical Change:**
- Architecture decision no longer viable
- Technology choice needs revision
- Integration approach changed

**External Change:**
- Third-party API changed
- Platform update breaks implementation
- Regulatory requirement introduced

### Inputs
Required:
- Description of change
- Current story/epic affected
- Current sprint-status.yaml

### Outputs
- Change impact analysis document
- Updated documentation (PRD/architecture/stories)
- Updated sprint-status.yaml
- Routing recommendations

### Example: API Change Mid-Sprint

**Change:** SendGrid deprecated email API, requires migration to new API

**Impact Analysis:**
- **Stories Affected**: Story 1.3 (Email Verification) - IN PROGRESS
- **Epics Affected**: Epic 1 (Authentication)
- **Architecture Impact**: ADR-004 (Email Service) needs revision
- **Timeline Impact**: +1 day (API migration work)

**Solution Options:**

**Option A:** Continue with deprecated API, plan migration for later
- **Pros**: No sprint disruption
- **Cons**: Technical debt, API sunset in 6 months

**Option B:** Migrate to new API now
- **Pros**: No technical debt, future-proof
- **Cons**: +1 day to sprint

**Option C:** Defer email verification to next sprint
- **Pros**: No disruption to current sprint
- **Cons**: Story 1.3 incomplete, Epic 1 not done

**Decision:** Option B (Migrate now)

**Actions:**
1. Update architecture.md (ADR-004: Use SendGrid v4 API)
2. Update epic-1-tech-context.md (new email patterns)
3. Update Story 1.3 acceptance criteria (new API endpoints)
4. Continue dev-story with new approach
5. Extend sprint by 1 day

### Related Workflows
- **architecture** - May need updates
- **create-story** - May need to create new stories
- **sprint-planning** - May need to re-prioritize
- **retrospective** - Document learnings

---

## retrospective

### Purpose
Run after epic completion to review overall success, extract lessons learned, and explore if new information emerged that might impact the next epic.

**Agent:** SM (Scrum Master)
**Phase:** 4 (Implementation)
**Required:** Recommended (after each epic)
**Typical Duration:** 60-90 minutes

### When to Use
Run **after completing an epic** (all stories DONE).

**Trigger Points:**
- Epic status: DONE
- All epic stories completed
- Before starting next epic
- Before final release (after all epics)

### Process Overview

**Phase 1: Data Gathering (Steps 1-3)**
- Load sprint-status.yaml
- Load completed story files
- Load code-review feedback
- Gather metrics (velocity, story cycle time)

**Phase 2: Review Execution (Steps 4-7)**
- **What Went Well**: Successes and wins
- **What Didn't Go Well**: Challenges and issues
- **Lessons Learned**: Actionable insights
- **Process Improvements**: Changes for next epic

**Phase 3: Technical Insights (Steps 8-10)**
- Architecture decisions review
- Technology choices validation
- Code quality assessment
- Test coverage and quality

**Phase 4: Planning Insights (Steps 11-13)**
- Estimation accuracy
- Requirements clarity
- Dependency management
- Scope changes

**Phase 5: Action Items (Step 14)**
- Process changes for next epic
- Architecture updates needed
- Documentation improvements
- Training or knowledge gaps

### Inputs
Required:
- sprint-status.yaml (epic completion data)
- Completed story files
- code-review feedback

Optional:
- Team velocity data
- CI/CD metrics
- Bug reports

### Outputs

**Primary Output:** `retrospective-epic-{N}-{date}.md`

**Document Structure:**
1. Epic Summary
   - Stories completed
   - Time taken
   - Velocity achieved
2. What Went Well
3. What Didn't Go Well
4. Lessons Learned
5. Technical Insights
6. Planning Insights
7. Action Items for Next Epic
8. Process Improvements

### Example: Epic 1 Retrospective

```markdown
# Retrospective: Epic 1 - Authentication

**Date:** 2025-11-15
**Duration:** 2 weeks (planned), 2.5 weeks (actual)
**Stories Completed:** 8/8
**Velocity:** 48 points (target: 60 points)

## What Went Well

✅ **Architecture decisions solid**
- NextAuth.js choice worked well
- Database sessions simpler than JWT

✅ **Test coverage excellent**
- All stories have E2E + API tests
- No critical bugs in production

✅ **Team collaboration strong**
- Code reviews thorough
- Knowledge sharing effective

## What Didn't Go Well

❌ **Estimation inaccurate**
- Stories took 20% longer than estimated
- Story 1.3 (Email Verification) took 2 days instead of 1

❌ **Third-party integration surprise**
- SendGrid API deprecation discovered mid-sprint
- Required correct-course workflow

❌ **Testing setup overhead**
- Test fixtures took longer than expected to set up
- Should have created fixtures earlier

## Lessons Learned

💡 **Buffer time for integrations**
- Add 25% buffer to stories with third-party APIs
- Research API stability before committing

💡 **Test fixtures upfront**
- Create test fixtures in first story of epic
- Reuse across all stories

💡 **Architecture review cadence**
- Mid-epic architecture check-in would have caught issues earlier

## Technical Insights

**Architecture:**
- ADR-001 (NextAuth.js) validated ✅
- ADR-004 (SendGrid) needed revision (v3 → v4)

**Code Quality:**
- Average code-review score: 8.5/10
- No critical issues
- 3 high-priority issues (all addressed)

**Test Coverage:**
- E2E: 95% of critical paths
- API: 100% of endpoints
- Unit: 85% of business logic

## Planning Insights

**Estimation Accuracy:**
- Estimated: 60 points
- Actual: 72 points
- Variance: +20%
- **Adjustment**: Use 1.2× multiplier for next epic

**Requirements Clarity:**
- PRD was clear ✅
- Architecture was thorough ✅
- Story AC needed refinement in 2 stories

**Dependency Management:**
- Story dependencies well-sequenced
- No blocking issues

## Action Items for Epic 2

1. **Create test fixtures first** (Story 2.1)
   - Owner: DEV
   - Timeline: First story of Epic 2

2. **Add 25% buffer to integration stories**
   - Owner: SM
   - Apply in epic-2 estimates

3. **Mid-epic architecture check-in**
   - Owner: Architect
   - Schedule after 50% epic completion

4. **Research third-party API stability**
   - Owner: DEV
   - Before starting stories with external APIs

## Process Improvements

**For Next Epic:**
- ✅ Run architecture review mid-epic
- ✅ Create test fixtures in first story
- ✅ Add buffer time to estimates
- ✅ Document third-party API versions in architecture

**For Future Projects:**
- Document API stability research process
- Create reusable test fixture templates
````

### Related Workflows

- **sprint-planning** - Next epic planning
- **architecture** - May need updates from insights
- **create-story** - Apply lessons to story creation

---

## Utility Workflows

### workflow-status

**Purpose:** Check "what should I do now?" for any agent.

**Agent:** All
**Duration:** 2-5 minutes
**When to Use:** Anytime you're unsure of next step

**How It Works:**

1. Loads sprint-status.yaml
2. Determines current phase
3. Identifies next workflow to run
4. Provides clear recommendation

**Example Output:**

```
Current Phase: 4 (Implementation)
Current Epic: Epic 1 (Authentication)
Current Sprint: Sprint 1

Next Story: Story 1.3 (Email Verification)
Status: TODO
Dependencies: Story 1.2 (DONE) ✅

**Recommendation:** Run `create-story` to generate Story 1.3

After create-story:
1. Run story-context
2. Run dev-story
3. Run code-review
4. Run story-done
```

See: [workflow-status README](../workflows/workflow-status/README.md)

---

### document-project

**Purpose:** Analyze and document brownfield projects by scanning codebase, architecture, and patterns.

**Agent:** Analyst
**Duration:** 1-3 hours
**When to Use:** Brownfield projects without documentation

**How It Works:**

1. Scans codebase structure
2. Identifies architecture patterns
3. Documents technology stack
4. Creates reference documentation
5. Generates PRD-like document from existing code

**Output:** `project-documentation-{date}.md`

**When to Run:**

- Before starting work on legacy project
- When inheriting undocumented codebase
- Creating onboarding documentation

See: [document-project README](../workflows/document-project/README.md)

---

## Story Lifecycle Visualization

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: IMPLEMENTATION (Iterative Story Lifecycle)        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐
│ Sprint Planning │  → Creates sprint-status.yaml
└────────┬────────┘     Defines story queue
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ▼                                          │
┌─────────────────────┐                            │
│ Epic Tech Context   │  → Optional per epic       │
│ (Once per epic)     │     Provides technical     │
└─────────────────────┘     guidance              │
         │                                          │
         ▼                                          │
┌─────────────────────────────────────────────────┤
│ FOR EACH STORY IN QUEUE:                        │
├─────────────────────────────────────────────────┤
         │                                          │
         ▼                                          │
┌─────────────────┐                                │
│ Create Story    │  → Generates story file        │
│ (TODO → IN PROGRESS)                            │
└────────┬────────┘                                │
         │                                          │
         ▼                                          │
┌─────────────────┐                                │
│ Story Context   │  → Assembles focused context   │
└────────┬────────┘                                │
         │                                          │
         ▼                                          │
┌─────────────────┐                                │
│ Dev Story       │  → Implements + tests           │
│ (IN PROGRESS)   │                                │
└────────┬────────┘                                │
         │                                          │
         ▼                                          │
┌─────────────────┐                                │
│ Code Review     │  → Senior dev review            │
│ (IN PROGRESS →  │                                │
│  READY FOR REVIEW)                               │
└────────┬────────┘                                │
         │                                          │
    ┌────┴────┐                                    │
    │ Result? │                                    │
    └────┬────┘                                    │
         │                                          │
    ┌────┼────────────────────┐                   │
    │    │                    │                   │
    ▼    ▼                    ▼                   │
APPROVED  APPROVED           REQUEST              │
          WITH COMMENTS      CHANGES              │
    │         │                   │                │
    └─────────┴───────────────────┘               │
              │                                    │
              ▼                                    │
    ┌─────────────────┐                           │
    │ Story Done      │  → READY FOR REVIEW → DONE│
    └────────┬────────┘                           │
             │                                     │
             ├─────────────────────────────────────┘
             │ More stories?
             │
             ▼
    ┌────────────────┐
    │ Epic Complete? │
    └────────┬───────┘
             │
        ┌────┼────┐
        │         │
       Yes       No
        │         └──> Continue to next story
        │
        ▼
┌─────────────────┐
│ Retrospective   │  → Review epic, lessons learned
└─────────────────┘
        │
        ▼
    All epics done?
        │
       Yes → PROJECT COMPLETE
```

---

## Best Practices for Phase 4

### 1. One Story at a Time

**Focus on completing stories fully** before starting new ones. Don't parallelize stories unless you have multiple developers.

### 2. Always Run story-context

Don't skip context assembly. DEV agent performs better with focused, relevant context.

### 3. Write Tests First (ATDD)

For P0/P1 stories, write failing tests first (acceptance test-driven development), then implement to make them pass.

### 4. Code Review P0/P1 Stories

Always review critical stories. P2/P3 can be optional reviews.

### 5. Run Retrospectives

Don't skip retrospectives. They provide valuable insights that improve velocity in subsequent epics.

### 6. Use workflow-status

When unsure what to do next, run workflow-status. It will guide you.

### 7. Document Deviations

If you deviate from architecture or PRD, document why in story file.

---

## Common Anti-Patterns

### ❌ Starting Multiple Stories Simultaneously

"Let's parallelize 5 stories to go faster."
→ **Result**: Context switching, incomplete stories, harder to track

### ❌ Skipping story-context

"The DEV agent can just read the full PRD."
→ **Result**: Slow context loading, irrelevant info, slower implementation

### ❌ No Code Reviews

"Code reviews slow us down, skip them."
→ **Result**: Technical debt, inconsistent quality, bugs in production

### ❌ Skipping Retrospectives

"We're too busy shipping, no time for retros."
→ **Result**: Repeat mistakes, no process improvement, lower velocity

### ✅ Correct Approach

- Focus on one story at a time
- Always assemble story context
- Review P0/P1 stories
- Run retrospectives after epics
- Use workflow-status for guidance

---

## Summary

Phase 4 Implementation follows a **story-centric workflow**:

| Workflow              | Purpose             | Frequency         |
| --------------------- | ------------------- | ----------------- |
| **sprint-planning**   | Initialize tracking | Once at start     |
| **epic-tech-context** | Technical guidance  | Once per epic     |
| **create-story**      | Generate story file | Per story         |
| **story-context**     | Assemble context    | Per story         |
| **dev-story**         | Implement story     | Per story         |
| **code-review**       | Review quality      | Per story (P0/P1) |
| **correct-course**    | Handle changes      | As needed         |
| **retrospective**     | Learn and improve   | After each epic   |

**Key Takeaway:** Implementation is iterative and incremental. Move one story through its full lifecycle before starting the next. Use retrospectives to continuously improve.

**Next:** Testing & QA (testarch workflows) run in parallel with implementation.

See: [workflows-testing.md](./workflows-testing.md)
