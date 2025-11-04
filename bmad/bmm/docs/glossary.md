# BMM Glossary

Comprehensive terminology reference for the BMad Method Module.

---

## Navigation

- [Core Concepts](#core-concepts)
- [Scale & Complexity](#scale--complexity)
- [Planning Documents](#planning-documents)
- [Workflow & Phases](#workflow--phases)
- [Agents & Roles](#agents--roles)
- [Status & Tracking](#status--tracking)
- [Project Types](#project-types)
- [Implementation Terms](#implementation-terms)

---

## Core Concepts

### BMM (BMad Method Module)

Core orchestration system for AI-driven agile development, providing comprehensive lifecycle management through specialized agents and workflows.

### BMad Method

The complete methodology for AI-assisted software development, encompassing planning, architecture, implementation, and quality assurance workflows that adapt to project complexity.

### Scale-Adaptive System

BMad Method's intelligent workflow orchestration that automatically adjusts planning depth, documentation requirements, and implementation processes based on project size and complexity (Levels 0-4).

### Agent

A specialized AI persona with specific expertise (PM, Architect, SM, DEV, TEA) that guides users through workflows and creates deliverables. Agents have defined capabilities, communication styles, and workflow access.

### Workflow

A multi-step guided process that orchestrates AI agent activities to produce specific deliverables. Workflows are interactive and adapt to user context.

---

## Scale & Complexity

### Level 0 (Single Atomic Change)

Single-story projects like bug fixes, typos, or small patches. Uses tech-spec only, no architecture needed. Estimated completion: hours.

### Level 1 (Small Feature)

Projects with 1-10 stories, typically 2-3 related changes. Examples: OAuth login, search feature, user profile page. Uses tech-spec with epic breakdown.

### Level 2 (Medium Project)

Projects with 5-15 stories across multiple epics. Examples: admin dashboard, customer portal, reporting system. Uses PRD + optional architecture.

### Level 3 (Complex Integration)

Projects with 12-40 stories involving subsystems and integrations. Examples: e-commerce platform, SaaS product, multi-module system. Requires PRD + comprehensive architecture.

### Level 4 (Enterprise Scale)

Projects with 40+ stories across products. Examples: multi-tenant systems, product ecosystems, platform expansions. Requires full methodology with strategic planning.

### Complexity Level

The scale rating (0-4) assigned to a project based on story count, integration requirements, team size, and architectural complexity.

---

## Planning Documents

### Tech-Spec (Technical Specification)

**Level 0-1 only.** Comprehensive technical plan created upfront that serves as the primary planning document for small changes or features. Contains problem statement, solution approach, file-level changes, stack detection (brownfield), testing strategy, and developer resources.

### Epic-Tech-Spec (Epic Technical Specification)

**Level 2-4 only.** Detailed technical planning document created during implementation (just-in-time) for each epic. Supplements PRD + Architecture with epic-specific implementation details, code-level design decisions, and integration points.

**Key Difference:** Tech-spec (Level 0-1) is created upfront and is the only planning doc. Epic-tech-spec (Level 2-4) is created per epic during implementation and supplements PRD + Architecture.

### PRD (Product Requirements Document)

**Level 2-4.** Product-level planning document containing vision, goals, feature requirements, epic breakdown, success criteria, and UX considerations. Replaces tech-spec for larger projects that need product planning.

### Architecture Document

**Level 2-4.** System-wide design document defining structure, components, interactions, data models, integration patterns, security, performance, and deployment. Optional for Level 2, required for Level 3-4.

**Scale-Adaptive:** Architecture complexity scales with level - Level 2 is lightweight, Level 4 is enterprise-grade.

### Epics

High-level feature groupings that contain multiple related stories. Typically span 5-15 stories each and represent cohesive functionality (e.g., "User Authentication Epic").

### Product Brief

Optional strategic planning document created in Phase 1 (Analysis) that captures product vision, market context, user needs, and high-level requirements before detailed planning.

### GDD (Game Design Document)

Game development equivalent of PRD, created by Game Designer agent for game projects.

---

## Workflow & Phases

### Phase 0: Documentation (Prerequisite)

**Conditional phase for brownfield projects.** Creates comprehensive codebase documentation before planning. Only required if existing documentation is insufficient for AI agents.

### Phase 1: Analysis (Optional)

Discovery and research phase including brainstorming, research workflows, and product brief creation. Optional for small projects (Level 0-1), recommended for Level 2, required for Level 3-4.

### Phase 2: Planning (Required)

**Always required.** Creates formal requirements and work breakdown. Routes to tech-spec (Level 0-1) or PRD (Level 2-4) based on detected complexity level.

### Phase 3: Solutioning (Conditional)

Architecture design phase. Optional for Level 2, required for Level 3-4. Includes architecture creation, validation, and gate checks.

### Phase 4: Implementation (Required)

Sprint-based development through story-by-story iteration. Uses sprint-planning, epic-tech-context, create-story, story-context, dev-story, code-review, and retrospective workflows.

### Quick Spec Flow

Fast-track workflow system for Level 0-1 projects that goes straight from idea to tech-spec to implementation, bypassing heavy planning. Designed for bug fixes, small features, and rapid prototyping.

### Just-In-Time Design

Pattern where epic-tech-specs are created during implementation (Phase 4) right before working on each epic, rather than all upfront. Enables learning and adaptation.

### Context Injection

Dynamic technical guidance generated for each story via epic-tech-context and story-context workflows, providing exact expertise when needed without upfront over-planning.

---

## Agents & Roles

### PM (Product Manager)

Agent responsible for creating PRDs, tech-specs, and managing product requirements. Primary agent for Phase 2 planning.

### Analyst (Business Analyst)

Agent that initializes workflows, conducts research, creates product briefs, and tracks progress. Often the entry point for new projects.

### Architect

Agent that designs system architecture, creates architecture documents, performs technical reviews, and validates designs. Primary agent for Phase 3.

### SM (Scrum Master)

Agent that manages sprints, creates stories, generates contexts, and coordinates implementation. Primary orchestrator for Phase 4.

### DEV (Developer)

Agent that implements stories, writes code, runs tests, and performs code reviews. Primary implementer in Phase 4.

### TEA (Test Architect)

Agent responsible for test strategy, quality gates, NFR assessment, and comprehensive quality assurance. Integrates throughout all phases.

### Paige (Documentation Guide)

Agent specialized in creating and maintaining high-quality technical documentation. Expert in documentation standards, information architecture, and professional technical writing.

### UX Designer

Agent that creates UX design documents, interaction patterns, and visual specifications for UI-heavy projects.

### Game Designer

Specialized agent for game development projects. Creates game design documents (GDD) and game-specific workflows.

### BMad Master

Meta-level orchestrator agent from BMad Core. Facilitates party mode, lists available tasks and workflows, and provides high-level guidance across all modules.

### Party Mode

Multi-agent collaboration feature where all installed agents (19+ from BMM, CIS, BMB, custom modules) discuss challenges together in real-time. BMad Master orchestrates, selecting 2-3 relevant agents per message for natural cross-talk and debate. Best for strategic decisions, creative brainstorming, cross-functional alignment, and complex problem-solving. See [Party Mode Guide](./party-mode.md).

---

## Status & Tracking

### bmm-workflow-status.md

**Phases 0-3.** Tracking file that shows current phase, completed workflows, progress, and next recommended actions. Created by workflow-init, updated automatically.

### sprint-status.yaml

**Phase 4 only.** Single source of truth for implementation tracking. Contains all epics, stories, and retrospectives with current status for each. Created by sprint-planning, updated by agents.

### Story Status Progression

```
backlog → drafted → ready-for-dev → in-progress → review → done
```

- **backlog** - Story exists in epic but not yet drafted
- **drafted** - Story file created by SM via create-story
- **ready-for-dev** - Story has context, ready for DEV via story-context
- **in-progress** - DEV is implementing via dev-story
- **review** - Implementation complete, awaiting code-review
- **done** - Completed with DoD met

### Epic Status Progression

```
backlog → contexted
```

- **backlog** - Epic exists in planning docs but no context yet
- **contexted** - Epic has technical context via epic-tech-context

### Retrospective

Workflow run after completing each epic to capture learnings, identify improvements, and feed insights into next epic planning. Critical for continuous improvement.

---

## Project Types

### Greenfield

New project starting from scratch with no existing codebase. Freedom to establish patterns, choose stack, and design from clean slate.

### Brownfield

Existing project with established codebase, patterns, and constraints. Requires understanding existing architecture, respecting established conventions, and planning integration with current systems.

**Critical:** Brownfield projects should run document-project workflow BEFORE planning to ensure AI agents have adequate context about existing code.

### document-project Workflow

**Brownfield prerequisite.** Analyzes and documents existing codebase, creating comprehensive documentation including project overview, architecture analysis, source tree, API contracts, and data models. Three scan levels: quick, deep, exhaustive.

---

## Implementation Terms

### Story

Single unit of implementable work with clear acceptance criteria, typically 2-8 hours of development effort. Stories are grouped into epics and tracked in sprint-status.yaml.

### Story File

Markdown file containing story details: description, acceptance criteria, technical notes, dependencies, implementation guidance, and testing requirements.

### Story Context

Technical guidance document created via story-context workflow that provides implementation-specific context, references existing patterns, suggests approaches, and injects expertise for the specific story.

### Epic Context

Technical planning document created via epic-tech-context workflow before drafting stories within an epic. Provides epic-level technical direction, architecture notes, and implementation strategy.

### Sprint Planning

Workflow that initializes Phase 4 implementation by creating sprint-status.yaml, extracting all epics/stories from planning docs, and setting up tracking infrastructure.

### Gate Check

Validation workflow (solutioning-gate-check) run before Phase 4 to ensure PRD, architecture, and UX documents are cohesive with no gaps or contradictions. Required for Level 3-4.

### DoD (Definition of Done)

Criteria that must be met before marking a story as done. Typically includes: implementation complete, tests written and passing, code reviewed, documentation updated, and acceptance criteria validated.

### Shard / Sharding

**For runtime LLM optimization only (NOT human docs).** Splitting large planning documents (PRD, epics, architecture) into smaller section-based files to improve workflow efficiency. Phase 1-3 workflows load entire sharded documents transparently. Phase 4 workflows selectively load only needed sections for massive token savings.

---

## Additional Terms

### Workflow Status

Universal entry point workflow that checks for existing status file, displays current phase/progress, and recommends next action based on project state.

### Workflow Init

Initialization workflow that creates bmm-workflow-status.md, detects greenfield vs brownfield, determines complexity level, and sets up appropriate workflow path.

### Level Detection

Automatic analysis by workflow-init that uses keyword analysis, story count estimation, and complexity indicators to suggest appropriate level (0-4). User can override suggested level.

### Correct Course

Workflow run during Phase 4 when significant changes or issues arise. Analyzes impact, proposes solutions, and routes to appropriate remediation workflows.

### Migration Strategy

Plan for handling changes to existing data, schemas, APIs, or patterns during brownfield development. Critical for ensuring backward compatibility and smooth rollout.

### Feature Flags

Implementation technique for brownfield projects that allows gradual rollout of new functionality, easy rollback, and A/B testing. Recommended for Level 2+ brownfield changes.

### Integration Points

Specific locations where new code connects with existing systems. Must be documented explicitly in brownfield tech-specs and architectures.

### Convention Detection

Quick Spec Flow feature that automatically detects existing code style, naming conventions, patterns, and frameworks from brownfield codebases, then asks user to confirm before proceeding.

---

## Related Documentation

- [Quick Start Guide](./quick-start.md) - Learn BMM basics
- [Scale Adaptive System](./scale-adaptive-system.md) - Deep dive on levels and complexity
- [Brownfield Guide](./brownfield-guide.md) - Working with existing codebases
- [Quick Spec Flow](./quick-spec-flow.md) - Fast-track for Level 0-1
- [FAQ](./faq.md) - Common questions
- [Troubleshooting](./troubleshooting.md) - Problem resolution
