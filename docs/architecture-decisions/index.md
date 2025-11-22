# Architecture Decision Records (ADR)

> **导航:** [← 返回文档中心](../index.md) | [查看架构文档](../architecture.md)

本目录记录 KlipNote 项目中的重要架构和技术决策。每个 ADR 文档说明决策的背景、考虑的选项、最终选择及其理由。

---

## 📋 ADR 日志

| ADR | 标题 | 状态 | 日期 | 相关 Epic |
|-----|------|------|------|-----------|
| [ADR-004](./ADR-004-multi-model-architecture.md) | Multi-Model Production Architecture | ✅ Approved | 2025-11-15 | Epic 4 |

---

## 🎯 关于 ADR

### 什么是 ADR？

Architecture Decision Records (架构决策记录) 是轻量级文档，用于记录项目中的重要技术决策。每个 ADR 描述：

- **背景 (Context):** 需要做出决策的情况和问题
- **决策 (Decision):** 最终选择的方案
- **理由 (Rationale):** 为什么选择这个方案
- **后果 (Consequences):** 这个决策带来的影响（正面和负面）
- **替代方案 (Alternatives):** 考虑过但未采用的其他选项

### 何时创建 ADR？

在以下情况下应该创建 ADR：

- 🏗️ 选择关键的架构模式或技术栈
- 🔀 重大的架构重构或方向调整
- ⚖️ 在多个有效方案间做出权衡决策
- 🔒 设定影响未来开发的技术约束
- 📚 需要向团队或未来的自己解释"为什么这样做"

### ADR 标准格式

```markdown
# ADR-XXX: [简短标题]

**Date**: YYYY-MM-DD
**Status**: [Proposed | Approved | Deprecated | Superseded]
**Deciders**: [决策参与者]
**Epic**: [相关 Epic]

---

## Context

[描述需要做决策的背景和问题]

## Decision

[最终决策的描述]

## Rationale

[为什么选择这个方案]

## Consequences

### Positive
- [正面影响 1]
- [正面影响 2]

### Negative
- [负面影响/权衡 1]
- [负面影响/权衡 2]

## Alternatives Considered

### Option A
[描述和评估]

### Option B
[描述和评估]

## Implementation Notes

[实施细节、参考文档等]
```

---

## 📚 现有 ADR 摘要

### ADR-004: Multi-Model Production Architecture

**关键决策:** 使用 Docker 容器化方案分离 BELLE-2 和 WhisperX 模型环境，解决 PyTorch 版本冲突问题。

**背景:** Epic 3 验证了两个模型各有优势但无法共存于同一 Python 环境：
- BELLE-2 需要 CUDA 11.8 / PyTorch <2.6
- WhisperX 需要 CUDA 12.x / PyTorch ≥2.6（安全合规要求）

**方案:**
- 每个模型独立 Docker 容器
- 共享 GPU 资源通过 Docker GPU runtime
- FastAPI 主服务通过 HTTP 调用容器化模型

**影响:**
- ✅ 解决依赖冲突，支持多模型并行
- ✅ 隔离环境，提高稳定性
- ⚠️ 增加部署复杂度和资源开销

**相关文档:** [Epic 4 Tech Spec](../sprint-artifacts/tech-spec-epic-4.md)

---

## 🔢 ADR 编号规则

- ADR 按创建顺序编号（ADR-001, ADR-002, ...）
- 已废弃的 ADR 保留编号和文件，状态标记为 "Deprecated"
- 被替代的 ADR 在文档中链接到新的 ADR

---

## 📝 创建新 ADR

1. 确定 ADR 编号（下一个可用编号）
2. 复制上面的标准格式创建新文件 `ADR-XXX-short-title.md`
3. 填写所有章节，确保清晰说明决策背景和理由
4. 将新 ADR 添加到本索引文件的日志表格中
5. 在相关文档（Epic Tech Spec、Architecture 等）中引用 ADR

---

**最后更新:** 2025-11-22
**ADR 数量:** 1
**下一个 ADR 编号:** ADR-005
