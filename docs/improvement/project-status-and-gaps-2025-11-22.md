# KlipNote 项目现状与问题客观描述

**文档目的：** 为专家咨询提供清晰的项目现状和待解决问题
**日期：** 2025-11-22
**项目阶段：** MVP完成（Epic 1-4 Done），进入后MVP打磨阶段

---

## 1. 项目背景

**KlipNote** 是一个音频转录服务，提供Web界面和API端点。当前已完成MVP开发（Epic 1-4），实现了基本的上传→转录→展示→导出workflow。

**技术栈：**
- 后端：FastAPI + Celery + Redis
- 转录模型：Belle2（中文优化）+ WhisperX（多语言）
- 部署：Docker Compose，Belle2和WhisperX在不同环境（`.venv` vs `.venv-whisperx`），原因是PyTorch版本冲突

---

## 2. 已实现的能力（Epic 1-4）

### 2.1 转录基座模型（Epic 3-4）

**Belle2：**
- 位置：`backend/app/ai_services/belle2_service.py`
- 环境：`backend/.venv`
- 特点：中文转录优化

**WhisperX：**
- 位置：`backend/app/ai_services/whisperx_service.py`
- 环境：`backend/.venv-whisperx`（独立环境，PyTorch版本不兼容Belle2）
- 特点：多语言支持，GPU加速

**模型路由：**
- 代码位置：`backend/app/ai_services/model_router.py`
- 支持：auto（自动选择）、belle2、whisperx
- 路由逻辑：通过Celery queue区分不同模型worker

### 2.2 Enhancement增强组件（Epic 4）

**已开发的组件：**

| 组件 | 文件位置 | 功能 |
|------|---------|------|
| VADManager | `backend/app/ai_services/enhancement/vad_manager.py` | 语音活动检测，过滤静音段 |
| TimestampRefiner | `backend/app/ai_services/enhancement/timestamp_refiner.py` | 优化字级时间戳边界 |
| SegmentSplitter | `backend/app/ai_services/enhancement/segment_splitter.py` | 长段落分割（按标点/时长/字符数） |

**Pipeline编排：**
- Factory：`backend/app/ai_services/enhancement/factory.py`
- Pipeline：`backend/app/ai_services/enhancement/pipeline.py`
- 支持组件链式组合（如"vad,refine,split"）

**配置系统（环境变量）：**

**全局开关：**
```python
ENABLE_ENHANCEMENTS = True/False  # 总开关
ENHANCEMENT_PIPELINE = "vad,refine,split"  # 组件配置
```

**VAD引擎配置：**
```python
VAD_ENGINE = "auto/silero/webrtc"
VAD_SILERO_THRESHOLD = 0.5
VAD_SILERO_MIN_SILENCE_MS = 700
VAD_WEBRTC_AGGRESSIVENESS = 2
VAD_WEBRTC_MIN_SPEECH_MS = 300
VAD_WEBRTC_MAX_SILENCE_MS = 500
VAD_MIN_SILENCE_DURATION = 1.0
```

**Segment Splitter配置：**
```python
SEGMENT_SPLITTER_MAX_DURATION = 7.0  # 最大段落时长（秒）
SEGMENT_SPLITTER_MAX_CHARS = 200     # 最大字符数
SEGMENT_SPLITTER_CHAR_DURATION_SEC = 0.4  # 字符时长估算
```

**其他配置：**
```python
OPTIMIZER_ENGINE = "auto/whisperx/heuristic"
ENABLE_OPTIMIZATION = True/False
SEGMENT_SPLITTER_ENABLED = True/False
INCLUDE_ENHANCED_METADATA = True/False
```

### 2.3 现有CLI工具

**已存在的CLI工具（质量验证专用）：**

**`backend/app/cli/compare_models.py`**
- 功能：比较Belle2 vs WhisperX转录质量
- 使用方式：直接导入转录服务类（`Belle2Service`, `WhisperXService`）
- 输入：音频文件corpus + 可选参考转录
- 输出：CER/WER、质量metrics对比报告

**`backend/app/cli/validate_quality.py`**
- 功能：单模型质量验证
- 使用方式：直接导入转录服务类
- 输入：音频文件 + 模型名 + pipeline配置
- 输出：详细质量metrics（包含enhancement指标）

**特点：**
- 这两个CLI工具**直接导入Python模块**，不通过HTTP API
- 需要在正确的虚拟环境中运行（`.venv` for Belle2, `.venv-whisperx` for WhisperX）
- 主要用于离线质量测试，非日常开发调试

---

## 3. 当前API端点现状

### 3.1 已有的FastAPI端点（7个）

| 端点 | 方法 | 参数 | 功能 |
|------|------|------|------|
| `/` | GET | 无 | API根信息 |
| `/health` | GET | 无 | 健康检查 |
| `/upload` | POST | `file`, `model`, `language` | 上传文件启动转录 |
| `/status/{job_id}` | GET | `job_id` | 查询任务状态 |
| `/result/{job_id}` | GET | `job_id` | 获取转录结果 |
| `/media/{job_id}` | GET | `job_id` | 访问原始媒体文件 |
| `/export/{job_id}` | POST | `job_id`, `format` | 导出转录（SRT/TXT） |

### 3.2 `/upload`端点参数详情

**当前支持的参数（Form Data）：**
- `file` (required)：上传的音频/视频文件
- `model` (optional)：belle2 | whisperx | auto（默认：环境变量`DEFAULT_TRANSCRIPTION_MODEL`）
- `language` (optional)：语言提示，如"zh", "en"（用于auto模式路由）

**当前不支持的参数：**
- ❌ Enhancement pipeline配置
- ❌ VAD引擎选择
- ❌ VAD参数调整
- ❌ Segment Splitter参数调整
- ❌ 任何其他enhancement相关参数

**实际行为：**
- Enhancement配置完全由**服务端.env环境变量**决定
- 用户/前端**无法**通过API控制enhancement行为
- 修改enhancement配置需要重启服务或修改环境变量

---

## 4. 识别的问题和Gap

### 4.1 问题1：Enhancement功能无法通过API调用

**现状：**
- Epic 4已开发完整的Enhancement组件和配置系统
- 但所有配置仅通过服务端环境变量控制（`.env`文件）
- API层未暴露任何enhancement参数

**影响：**
- 前端用户无法选择或调整enhancement行为
- 开发者无法通过API快速测试不同enhancement组合
- 所有enhancement调试必须通过修改.env + 重启服务

**数据流断层：**
```
[前端/CLI] → [/upload API] → [Celery Task] → [TranscriptionService]
                    ↑                              ↑
                  缺少                          有完整的
              enhancement                    enhancement
                参数                          配置能力
```

### 4.2 问题2：缺乏通用的HTTP-based CLI工具

**现状：**
- 存在两个质量验证CLI工具（`compare_models.py`, `validate_quality.py`）
- 这些工具直接导入Python模块，不通过API
- 需要在特定虚拟环境运行（Belle2用`.venv`，WhisperX用`.venv-whisperx`）

**缺少的能力：**
- 没有通用的CLI工具来测试FastAPI的7个端点
- 无法通过命令行快速验证完整workflow（upload → status → result → export）
- 开发调试依赖手动curl命令或Postman

**对比：**
| 需求场景 | 现有工具 | Gap |
|---------|---------|-----|
| 质量验证（CER/WER对比） | ✅ `compare_models.py` | 满足 |
| 质量验证（单模型metrics） | ✅ `validate_quality.py` | 满足 |
| API端点测试（upload/status/result/export） | ❌ 无 | **缺失** |
| Enhancement参数快速测试 | ❌ 无（需修改.env） | **缺失** |
| 多模型日常开发调试 | ❌ 无 | **缺失** |

### 4.3 问题3：转录基座模型管理分散

**现状：**
- Belle2和WhisperX分别实现在独立的Service类中
- 两个模型在不同的虚拟环境运行（PyTorch版本冲突）
- 模型路由通过Celery queue机制实现

**管理上的复杂性：**
1. **环境隔离**：
   - Belle2：`backend/.venv`
   - WhisperX：`backend/.venv-whisperx`
   - 运行不同模型需要切换虚拟环境

2. **测试复杂度**：
   - 验证Belle2效果：需在`.venv`中运行或通过API
   - 验证WhisperX效果：需在`.venv-whisperx`中运行或通过API
   - 对比测试：需要分别在两个环境运行，或依赖`compare_models.py`工具

3. **配置分散**：
   - 模型选择：API的`model`参数 + 环境变量`DEFAULT_TRANSCRIPTION_MODEL`
   - Enhancement配置：环境变量（15+个）
   - 优化器配置：环境变量`OPTIMIZER_ENGINE`
   - 没有统一的配置入口或测试界面

**未解决的问题：**
- 如何高效地对比不同模型+不同enhancement组合的效果？
- 如何在不重启服务的情况下测试各种配置组合？
- 如何为未来可能新增的模型（如Whisper v4）预留扩展空间？

---

## 5. 你的目标需求

基于以上现状，你提出了三个明确的目标：

### 目标1：为增强功能开发API端点便于调用
**需要解决：**
- API层暴露enhancement配置参数（pipeline, VAD设置, Splitter设置等）
- 前端/CLI可以per-request方式控制enhancement行为
- 保持向后兼容（默认行为不变）

### 目标2：利用CLI工具对真实媒体文件进行转录，便于验证不同模型的转录效果以及各个增强组件的效果
**需要解决：**
- 开发通用的CLI工具覆盖所有FastAPI端点
- CLI可以快速测试不同模型（belle2/whisperx/auto）
- CLI可以快速测试不同enhancement组合（vad/refine/split）
- 避免或处理Belle2/WhisperX环境冲突问题

### 目标3：转录基座模型的统一管理，便于对各种模型的转录效果进行验证
**需要解决：**
- 建立统一的模型测试/对比机制
- 简化跨环境模型验证流程
- 可能需要考虑模型抽象层或统一接口
- 为新模型接入预留架构空间

---

## 6. 技术约束和限制

### 6.1 环境约束
- Belle2和WhisperX必须在不同虚拟环境运行（PyTorch版本冲突）
- 当前部署使用Docker Compose，两个独立worker服务

### 6.2 架构约束
- FastAPI作为Web API层
- Celery处理异步转录任务
- Redis用于任务队列和状态存储
- 前后端分离架构（Vue前端 + FastAPI后端）

### 6.3 已有投资
- Enhancement组件已完整开发并测试
- 环境变量配置系统已建立
- 质量验证CLI工具已存在并正常工作
- 前端和API的基本workflow已稳定运行

---

## 7. 需要专家指导的核心问题

**策略问题：**
1. API设计：如何暴露enhancement参数？全部暴露还是简化为presets？
2. 优先级：应该先完善API层，还是先开发CLI工具？还是并行？
3. 架构演进：是否需要重构Service层以支持更灵活的per-request配置？

**技术问题：**
1. CLI环境处理：如何优雅地处理Belle2/WhisperX的环境隔离？HTTP client还是直接导入？
2. 模型管理：是否需要建立模型抽象层统一管理不同转录引擎？
3. 测试策略：如何系统化地验证model × enhancement的组合效果？

**工程问题：**
1. 变更范围：这些需求是否应该作为一个Story，还是拆分为多个Story？
2. 时间估算：完整实现这三个目标预计需要多长时间？
3. 风险控制：如何保证新增功能不影响现有稳定的workflow？

---

## 8. 相关文件参考

**API端点：**
- `backend/app/main.py:63` - `/upload`端点定义

**转录服务：**
- `backend/app/ai_services/belle2_service.py`
- `backend/app/ai_services/whisperx_service.py`
- `backend/app/ai_services/model_router.py`

**Enhancement组件：**
- `backend/app/ai_services/enhancement/factory.py` - Pipeline工厂
- `backend/app/ai_services/enhancement/pipeline.py` - Pipeline编排
- `backend/app/ai_services/enhancement/vad_manager.py`
- `backend/app/ai_services/enhancement/timestamp_refiner.py`
- `backend/app/ai_services/enhancement/segment_splitter.py`

**配置：**
- `backend/app/config.py:114-121` - Enhancement相关环境变量

**现有CLI工具：**
- `backend/app/cli/compare_models.py`
- `backend/app/cli/validate_quality.py`

**已生成的变更提案（待更新）：**
- `docs/sprint-change-proposal-2025-11-22.md`

---

**文档状态：** 已完成客观描述，待咨询专家指导
