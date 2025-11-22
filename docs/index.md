# KlipNote 文档中心

> **项目概述:** KlipNote 是一款基于 GPU 加速的 AI 字幕转录工具，支持多模型转录和后处理增强。

---

## 📖 核心文档

### 产品与规划
- **[PRD - 产品需求文档](./prd.md)** - 产品愿景、功能需求、非功能需求
- **[Epics - 功能史诗分解](./epics.md)** - Epic 1-4 详细故事分解
- **[Backlog - 产品积压](./backlog.md)** - 未来功能规划

### 技术架构
- **[Architecture - 系统架构](./architecture.md)** - 整体技术架构设计
- **[Architecture Decisions](./architecture-decisions/index.md)** - 架构决策记录 (ADR)
- **[Developer Guide - 开发者指南](./developer-guide.md)** - 开发环境配置、代码规范、测试指南
- **[API Reference](./api-reference.md)** - 后端接口与示例

### 质量保证
- **[Quality Validation - 质量验证](./quality-validation.md)** - 质量指标与验证框架

---

## 🏃 Sprint 工件

### 当前进度
- **[Sprint Status - 冲刺状态](./sprint-artifacts/sprint-status.yaml)** - Epic 和 Story 实时状态追踪
  - ✅ Epic 1: Foundation & Core Transcription - **完成**
  - ✅ Epic 2: MVP Enhancement - **完成**
  - ✅ Epic 3: Optimizer Architecture - **完成**
  - 🔄 Epic 4: Multi-Model Enhancement - **进行中**

### 技术规格
- **[Tech Spec - Epic 1](./sprint-artifacts/tech-spec-epic-1.md)** - 基础转录工作流技术规格
- **[Tech Spec - Epic 2](./sprint-artifacts/tech-spec-epic-2.md)** - MVP 完善技术规格
- **[Tech Spec - Epic 3](./sprint-artifacts/tech-spec-epic-3.md)** - 优化器架构技术规格
- **[Tech Spec - Epic 4](./sprint-artifacts/tech-spec-epic-4.md)** - 多模型增强技术规格

### 用户故事
- **[Stories Index - 故事索引](./sprint-artifacts/stories/index.md)** - 所有用户故事按 Epic 分类索引

---

## 🔄 项目历程

### 回顾与反思
- **[Retrospectives - 回顾文档](./retrospectives/)** - Epic 完成后的经验总结
  - [Epic 1 回顾](./retrospectives/epic-1-retro-2025-11-07.md)

### 改进与规划
- **[Improvement - 改进文档](./improvement/)** - 项目状态分析与解决方案设计
  - [项目状态与差距分析 (2025-11-22)](./improvement/project-status-and-gaps-2025-11-22.md)
  - [解决方案设计 (2025-11-22)](./improvement/solution-design-2025-11-22.md)

### 初始文档
- **[Initial - 初始文档](./initial/)** - 项目启动时的头脑风暴和产品简报
  - [BMM 头脑风暴会议](./initial/bmm-brainstorming-session-2025-11-02.md)
  - [BMM 产品简报](./initial/bmm-product-brief-KlipNote-2025-11-03.md)

---

## 📦 部署文档

- **[Multi-Worker Deployment Guide](./deployment/multi-worker-deployment-guide.md)** - 多 Worker 部署指南
- **[Prerequisites Check Script](./deployment/check-prerequisites.sh)** - 前置条件检查脚本

---

## 📂 归档文档

- **[Archive - 归档](./archive/)** - 历史验证报告、研究文档、过期的变更提案

---

## 🔗 快速导航

### 我是新开发者，应该从哪里开始？
1. 阅读 [PRD](./PRD.md) 了解产品愿景
2. 查看 [Architecture](./architecture.md) 理解技术架构
3. 参考 [Developer Guide](./developer-guide.md) 配置开发环境
4. 查看 [Sprint Status](./sprint-artifacts/sprint-status.yaml) 了解当前进度

### 我想了解某个具体功能的实现？
1. 在 [Stories Index](./sprint-artifacts/stories/index.md) 找到对应的用户故事
2. 阅读故事的验收标准和技术细节
3. 查看对应 Epic 的 Tech Spec 了解架构决策

### 我想了解为什么做某个技术决策？
1. 查看 [Architecture Decisions](./architecture-decisions/index.md)
2. 阅读相关 ADR 文档了解决策背景、选项和结果

---

**最后更新:** 2025-11-22
**文档维护者:** Link
**BMad 工作流:** 本文档由 BMad Method 自动生成和维护
