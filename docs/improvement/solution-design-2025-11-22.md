# Solution Design: KlipNote Improvement Plan (2025-11-22)

**文档日期：** 2025-11-22
**关联文档：** `docs/improvement/project-status-and-gaps-2025-11-22.md`
**状态：** 提案 (Proposed)

---

## 1. 总体策略

针对 [project-status-and-gaps-2025-11-22.md] 中识别的三个核心问题，本方案采用 **"API First + HTTP CLI"** 的策略进行解决。

1.  **API层改造**：优先改造 `/upload` 端点，使其支持通过参数动态注入 Enhancement 配置。这是解决所有问题的基础。
2.  **CLI工具重构**：放弃直接导入 Python 模块的 "Thick Client" 模式，转向基于 HTTP 的 "Thin Client" 模式。CLI 工具将只负责发送 HTTP 请求，不再依赖本地 PyTorch 环境。
3.  **统一模型管理**：利用改造后的 API 和 CLI，通过标准的 HTTP 接口统一管理和测试不同模型（Belle2/WhisperX），利用现有的 Celery 路由机制屏蔽环境差异。

---

## 2. 详细解决方案

### 目标 1：Enhancement 功能 API 化

**问题描述：** 目前 Enhancement 配置完全依赖服务端环境变量，无法针对单个请求进行调整。

**解决方案：**
在 `/upload` 端点新增 `enhancement_config` 参数，允许客户端通过 JSON 格式传递完整的配置覆盖。

#### 2.1 API 变更设计 (`backend/app/main.py`)

修改 `POST /upload` 接口，增加一个 Form Field：

-   **参数名**：`enhancement_config`
-   **类型**：JSON String (in `multipart/form-data`)
-   **默认值**：`null` (使用服务端环境变量默认配置)
-   **示例结构**：
    ```json
    {
      "pipeline": "vad,refine,split",
      "vad": {
        "engine": "silero",
        "min_silence_duration": 0.5
      },
      "split": {
        "max_duration": 15.0
      }
    }
    ```

#### 2.2 后端逻辑变更

1.  **Task Signature 更新** (`backend/app/tasks/transcription.py`)：
    -   更新 `transcribe_audio` 任务签名，接受 `enhancement_config: Dict` 参数。
    -   在调用 `transcription_service.transcribe` 时传入该配置。

2.  **Factory 增强** (`backend/app/ai_services/enhancement/factory.py`)：
    -   修改 `create_pipeline` 函数，使其接受 `config_dict`。
    -   在实例化 `VADManager`, `SegmentSplitter` 等组件时，优先使用 `config_dict` 中的参数，环境变量作为 Fallback。

**理由：**
-   **向后兼容**：不改变现有参数结构，不传此参数则行为不变。
-   **灵活性**：JSON 结构可以轻松扩展支持未来的新组件参数，无需频繁修改 API 签名。

---

### 目标 2：通用 HTTP-based CLI 工具

**问题描述：** 现有 CLI 工具依赖特定虚拟环境，无法跨环境测试，且无法测试完整的 API Workflow。

**解决方案：**
开发一个新的 CLI 工具 `backend/app/cli/klip_client.py`，基于 `httpx` 或 `requests` 与运行中的 API 服务交互。

#### 2.1 CLI 功能设计

该工具将是一个纯 Python 脚本（无重依赖，不需要 PyTorch），可以在任何安装了 `requests` 的环境中运行。

**支持命令：**

1.  **`upload`**: 上传文件并启动转录。
    ```bash
    python klip_client.py upload audio.mp3 --model belle2 --enhance '{"pipeline":"vad"}'
    ```
2.  **`status`**: 轮询任务状态直到完成。
    ```bash
    python klip_client.py status <job_id> --watch
    ```
3.  **`result`**: 获取并打印结果。
    ```bash
    python klip_client.py result <job_id>
    ```
4.  **`test-flow`**: 自动化测试流程（Upload -> Wait -> Result -> Export）。
    ```bash
    python klip_client.py test-flow audio.mp3 --model auto --language zh
    ```

**理由：**
-   **环境解耦**：彻底解决了 Belle2 (`.venv`) 和 WhisperX (`.venv-whisperx`) 的环境冲突问题。CLI 只需要能访问 HTTP 端口即可。
-   **真实性验证**：测试的是实际运行的 Docker 容器和 Celery Worker，验证结果更接近生产环境。

---

### 目标 3：统一模型管理与验证

**问题描述：** 模型分散在不同环境，难以统一对比测试。

**解决方案：**
利用上述的 **HTTP CLI** 作为统一入口，配合简单的测试脚本或 CI 流程来进行模型验证。

#### 3.1 验证流程设计

不再需要在本地分别激活不同的 venv 来运行测试，而是通过 CLI 向 API 发起请求，由 API 的 `model_router` 负责分发到正确的 Worker 容器。

**对比测试场景：**

1.  **准备测试集**：`tests/standard/` 目录（已存在，包含三种不同的音频文件，分别代表不同的场景）。
2.  **运行对比脚本**：编写一个简单的 Shell 或 Python 脚本，循环调用 CLI：
    ```python
    # 伪代码
    for file in test_files:
        # Run Belle2
        cli.run("test-flow", file, model="belle2", output="result_belle2.json")
        # Run WhisperX
        cli.run("test-flow", file, model="whisperx", output="result_whisperx.json")
    ```
3.  **生成报告**：解析输出的 JSON，计算 CER/WER（可以使用现有的 `jiwer` 库，这部分可以在本地统一环境运行，因为它不需要 PyTorch，只需要文本处理）。

**理由：**
-   **利用现有架构**：KlipNote 已经有了基于 Celery Queue 的完善路由机制 (`model_router.py`)，CLI 应该利用它而不是绕过它。
-   **简化运维**：开发者只需要维护一套 API 服务，不需要在本地维护多个复杂的 Python 环境来进行日常测试。

---

## 3. 实施路线图 (Roadmap)

建议按以下顺序执行：

1.  **Step 1: API 改造 (预计 1-2 小时)**
    -   修改 `main.py` 添加 `enhancement_config` 参数。
    -   修改 `transcription.py` 传递配置。
    -   修改 `factory.py` 支持配置注入。

2.  **Step 2: 开发 HTTP CLI (预计 2-3 小时)**
    -   创建 `klip_client.py`。
    -   实现 Upload, Status, Result 等基础命令。
    -   实现 `test-flow` 自动化命令。

3.  **Step 3: 验证与文档 (预计 1 小时)**
    -   使用新 CLI 验证 Belle2 和 WhisperX 的工作流。
    -   更新项目 README。

---

## 4. 专家建议总结

针对您提出的核心问题：

1.  **API设计**：推荐使用 **JSON String** 形式的单一参数 `enhancement_config`，而不是展开所有参数。这样保持了 API 的整洁，且对未来 Enhancement 组件的增删具有极高的适应性。
2.  **优先级**：**API > CLI**。API 是核心能力，CLI 是基于 API 的工具。先有了 API 的支持，CLI 的开发就水到渠成。
3.  **架构演进**：不需要重构 Service 层的大型架构。目前的 Factory 模式非常适合进行配置注入的改造，只需要修改 Factory 的实例化逻辑即可，风险很低。
