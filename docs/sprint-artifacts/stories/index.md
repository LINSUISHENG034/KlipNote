# User Stories Index

> **导航:** [← 返回文档中心](../../index.md) | [查看 Sprint 状态](../sprint-status.yaml)

本文档按 Epic 组织所有用户故事，提供快速导航和状态查看。

---

## 📊 Epic 概览

| Epic | 标题 | 状态 | 故事数量 | 完成度 |
|------|------|------|---------|--------|
| Epic 1 | Foundation & Core Transcription Workflow | ✅ 完成 | 8 | 8/8 |
| Epic 2 | MVP Enhancement | ✅ 完成 | 7 | 7/7 |
| Epic 3 | Optimizer Architecture | ✅ 完成 | 4 | 4/4 (3 取消, 1 移至 Epic 4) |
| Epic 4 | Multi-Model Enhancement | 🔄 进行中 | 9 | 7/9 |

---

## Epic 1: Foundation & Core Transcription Workflow

**目标:** 建立 KlipNote 技术基础，实现完整的后端 API 架构（FastAPI + Celery + WhisperX）、基础前端界面和端到端上传 → 转录 → 显示工作流。

**状态:** ✅ 完成

### Stories

| ID | 标题 | 状态 | 文件 |
|----|------|------|------|
| 1-1 | Project Scaffolding and Development Environment | ✅ Done | [📄 Story](./1-1-project-scaffolding-and-development-environment.md) |
| 1-2 | Backend API Upload Endpoint | ✅ Done | [📄 Story](./1-2-backend-api-upload-endpoint.md) |
| 1-3 | Celery Task Queue and WhisperX Integration | ✅ Done | [📄 Story](./1-3-celery-task-queue-and-whisperx-integration.md) |
| 1-4 | Status and Result API Endpoints | ✅ Done | [📄 Story](./1-4-status-and-result-api-endpoints.md) |
| 1-5 | Frontend Upload Interface | ✅ Done | [📄 Story](./1-5-frontend-upload-interface.md) |
| 1-6 | Frontend Progress Monitoring | ✅ Done | [📄 Story](./1-6-frontend-progress-monitoring.md) |
| 1-7 | Frontend Transcription Display | ✅ Done | [📄 Story](./1-7-frontend-transcription-display.md) |
| 1-8 | UI Refactoring with Stitch Design System | ✅ Done | [📄 Story](./1-8-ui-refactoring-with-stitch-design-system.md) |

**回顾:** [Epic 1 Retrospective](../../retrospectives/epic-1-retro-2025-11-07.md)

---

## Epic 2: MVP Enhancement

**目标:** 在 Epic 1 基础上完善 MVP 功能，包括媒体播放、时间戳导航、字幕编辑和导出功能。

**状态:** ✅ 完成

### Stories

| ID | 标题 | 状态 | 文件 |
|----|------|------|------|
| 2-1 | Media Playback API Endpoint | ✅ Done | [📄 Story](./2-1-media-playback-api-endpoint.md) |
| 2-2 | Frontend Media Player Integration | ✅ Done | [📄 Story](./2-2-frontend-media-player-integration.md) |
| 2-3 | Click-to-Timestamp Navigation | ✅ Done | [📄 Story](./2-3-click-to-timestamp-navigation.md) |
| 2-4 | Inline Subtitle Editing | ✅ Done | [📄 Story](./2-4-inline-subtitle-editing.md) |
| 2-5 | Export API Endpoint with Data Flywheel | ✅ Done | [📄 Story](./2-5-export-api-endpoint-with-data-flywheel.md) |
| 2-6 | Frontend Export Functionality | ✅ Done | [📄 Story](./2-6-frontend-export-functionality.md) |
| 2-7 | MVP Release Checklist and Final Validation | ✅ Done | [📄 Story](./2-7-mvp-release-checklist-and-final-validation.md) |

---

## Epic 3: Optimizer Architecture

**目标:** 实现可插拔的优化器架构，集成 BELLE-2 和 WhisperX，进行 A/B 对比验证。

**状态:** ✅ 完成

### Stories

| ID | 标题 | 状态 | 文件 |
|----|------|------|------|
| 3-1 | BELLE-2 Integration | ✅ Done | [📄 Story](./3-1-belle2-integration.md) |
| 3-2a | Pluggable Optimizer Architecture | ✅ Done | [📄 Story](./3-2a-pluggable-optimizer-architecture.md) |
| 3-2b | WhisperX Integration Validation | ✅ Done | [📄 Story](./3-2b-whisperx-integration-validation.md) |
| 3-2c | BELLE-2 vs WhisperX Model Comparison | ✅ Done | [📄 Story](./3-2c-belle2-vs-whisperx-model-comparison.md) |
| 3-3 | Heuristic VAD Preprocessing | ❌ Cancelled | - |
| 3-4 | Heuristic Timestamp Refinement | ❌ Cancelled | - |
| 3-5 | Heuristic Segment Splitting | ❌ Cancelled | - |
| 3-6 | Quality Validation Framework | ↗️ Moved to Epic 4 | - |

**注释:** Stories 3-3, 3-4, 3-5 被取消，由 Epic 4 的模型无关增强组件替代。Story 3-6 移至 Epic 4 成为 Story 4-6。

---

## Epic 4: Multi-Model Enhancement

**目标:** 构建多模型生产架构和模型无关的后处理增强管道，支持 BELLE-2 和 WhisperX 的独立容器化部署。

**状态:** 🔄 进行中 (7/9 完成)

### Stories

| ID | 标题 | 状态 | 文件 |
|----|------|------|------|
| 4-1 | Multi-Model Production Architecture | ✅ Done | [📄 Story](./4-1-multi-model-production-architecture.md) |
| 4-1b | Frontend Model Selection | ✅ Done | [📄 Story](./4-1b-frontend-model-selection.md) |
| 4-2 | Model-Agnostic VAD Preprocessing & Enhanced Metadata Schema | ✅ Done | [📄 Story](./4-2-model-agnostic-vad-preprocessing.md) |
| 4-3 | Model-Agnostic Timestamp Refinement Component | ✅ Done | [📄 Story](./4-3-model-agnostic-timestamp-refinement.md) |
| 4-4 | Model-Agnostic Segment Splitting Component | ✅ Done | [📄 Story](./4-4-model-agnostic-segment-splitting.md) |
| 4-5 | Enhancement Pipeline Composition | ✅ Done | [📄 Story](./4-5-enhancement-pipeline-composition.md) |
| 4-6 | Multi-Model Quality Validation Framework | ✅ Done | [📄 Story](./4-6-multi-model-quality-validation.md) |
| 4-7 | Enhancement API Layer | 🔍 Review | [📄 Story](./4-7-enhancement-api-layer.md) |
| 4-8 | HTTP CLI Tool Development | 📋 Todo | - |
| 4-9 | Model Testing and Documentation | 📋 Todo | - |

**当前工作:** Story 4-7 正在代码审查中。

---

## 🔍 按状态查看

### ✅ 已完成 (26 stories)
- Epic 1: 全部 8 个故事
- Epic 2: 全部 7 个故事
- Epic 3: 4 个故事 (3-1, 3-2a, 3-2b, 3-2c)
- Epic 4: 7 个故事 (4-1, 4-1b, 4-2, 4-3, 4-4, 4-5, 4-6)

### 🔍 审查中 (1 story)
- Epic 4: Story 4-7 (Enhancement API Layer)

### 📋 待办 (2 stories)
- Epic 4: Story 4-8, 4-9

### ❌ 已取消 (3 stories)
- Epic 3: Stories 3-3, 3-4, 3-5 (被 Epic 4 的模型无关组件替代)

---

## 📝 文件命名约定

每个故事包含两个文件：
- `{epic}-{story}-{slug}.md` - 用户故事文档（验收标准、技术细节）
- `{epic}-{story}-{slug}.context.xml` - 故事上下文（仅在 ready-for-dev 状态创建）

---

**最后更新:** 2025-11-22
**当前 Sprint:** Epic 4 - Multi-Model Enhancement
**下一步:** 完成 Story 4-7 审查，启动 Story 4-8
