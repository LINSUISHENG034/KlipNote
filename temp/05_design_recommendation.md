
以下是一名专业软件工程师，为三份项目文档（PRD.md, epics.md, architecture.md），提供的建议：

---

### � 1. 最高优先级：解决“数据丢失”的NFR冲突

这是我发现的唯一一个在文档间存在的核心冲突，也是最有可能导致用户严重不满的风险点。

* **问题所在：**
    * **PRD (NFR-003):** "Browser-based state shall prevent data loss during normal operation." (浏览器状态应在正常操作期间防止数据丢失。)
    * **PRD (Out of Scope):** "localStorage edit recovery and crash protection." (localStorage 编辑恢复和崩溃保护被列为“范围之外”。)
    * **Architecture (Pattern):** 整个“Click-to-Timestamp”模式依赖 Pinia store (`transcription.ts`) 来管理状态。

* **风险分析：**
    Pinia store 中的数据**仅存在于内存中**。如果用户不小心刷新了浏览器标签页（`F5`或`Cmd+R`），或者浏览器崩溃，他们花费数分钟甚至数小时校对和编辑的所有字幕都将**立即丢失**。

    这直接违反了 NFR-003 的“防止数据丢失”要求。将 `localStorage` 恢复列为“范围之外”与此NFR背道而驰。对于一个以编辑为核心功能的工具，刷新即丢失数据是不可接受的。

* **可行的建议：**
    您**必须**在 Epic 2 中实现一个轻量级的持久化层。`localStorage` 是最简单、最符合您“无后端会话”设计理念的选择。

    1.  **修改 Story 2.4 (Inline Subtitle Editing):** 将 AC7 从“Edits persist in browser memory”修改为“Edits persist in browser localStorage”。
    2.  **修改 Architecture:** 在 Pinia store (`transcription.ts`) 中，使用 `watch` 侦听 `segments` 数组的变化，并将其（节流地）自动保存到 `localStorage` 中。
    3.  **添加 Story 1.7 / 2.2 的 AC:** 在加载结果页面时，应用应检查 `localStorage` 中是否存在与 `job_id` 匹配的已编辑 `segments`。如果存在，则加载这些编辑过的数据，而不是从 `/result/{job_id}` API 加载的原始数据。

    **理由：** 这是一个最小的改动（可能只需额外2-3小时的开发），但它能100%解决NFR-003的冲突，并将用户体验从“极其脆弱”提升到“足够健壮”。

---

### � 2. 架构与技术风险（“隐藏的陷阱”）

这些是您的架构设计中可能在实施时导致意外复杂性或阻塞的点。

#### A. 2GB 大文件上传的实现
* **问题所在：** Story 1.2 的 AC6 提到“Handles files up to 2GB size”。
* **风险分析：**
    标准的 FastAPI `UploadFile` 会将文件流式传输到内存或临时文件。但对于2GB这样的体积，它极有可能耗尽容器的内存导致崩溃，或者填满服务器的临时磁盘空间。
* **可行的建议：**
    您不能依赖 FastAPI 的默认 `UploadFile` 处理。您必须实现**分块流式上传 (Chunked Streaming Upload)**。
    1.  **前端 (Story 1.5):** 需要使用如 `tus.io` 客户端库或手动使用 `File.slice()` 来将大文件分割成小块（例如 5MB）。
    2.  **后端 (Story 1.2):** API `/upload` 端点需要重构，以接收这些分块，并将它们按顺序附加到服务器存储上的最终文件中（例如 `/uploads/{job_id}/original.mp4.part`）。
    3.  这也会改变您的工作流：您需要一个额外的 API 调用来“完成”上传，此时后端才将作业提交给 Celery。

#### B. 进度条的“真实性”
* **问题所在：** Story 1.3 (AC4) 要求 Celery 任务更新进度 (0%, 25%, 50%...)。`architecture.md` 定义了存储结构，但没有定义*如何*生成这个百分比。
* **风险分析：**
    WhisperX (以及大多数深度学习模型) 是一个“黑盒”。它不提供“我已完成 45%”的实时回调。您只能知道它“已开始”和“已完成”。一个假的、不动的进度条和完全没有进度条一样糟糕。
* **可行的建议：**
    将进度更新从“百分比”更改为“**基于阶段的更新**”。这更诚实，也更容易实现。
    1.  **修改 Story 1.3 / 1.6：**
    2.  在 Celery 任务中，按顺序更新 Redis 中的 `message` 字段：
        * `{"status": "processing", "progress": 10, "message": "任务已排队..."}`
        * `{"status": "processing", "progress": 20, "message": "正在加载 AI 模型..."}` (模型加载可能需要一些时间)
        * `{"status": "processing", "progress": 40, "message": "正在转录音频..."}` (这是最长的步骤)
        * `{"status": "processing", "progress": 80, "message": "正在对齐时间戳..."}`
        * `{"status": "completed", "progress": 100, "message": "处理完成！"}`
    3.  前端 `ProgressView.vue` (Story 1.6) 应**显示这个 `message` 文本**，并将 `progress` 百分比用于进度条。这提供了丰富的上下文，即使用户看到进度条在“正在转录音频...”阶段停留了20分钟，他们也会理解。

#### C. WhisperX 依赖项的冲突
* **问题所在：** 文档在如何引入 `WhisperX` 上存在矛盾。
    * `epics.md` (Story 1.1 AC3): "Dependencies installed: ... WhisperX" (暗示 `pip install whisperx`)
    * `architecture.md` (Project Structure): `ai_services/whisperx/` (Git submodule)
    * `architecture.md` (Requirements.txt): "whisperx" (又暗示 `pip install`)
* **风险分析：**
    开发人员在执行 Story 1.1 时会感到困惑。`git submodule` 策略（在架构正文中详细描述）是**更优越的选择**，因为它锁定了版本并允许您跟踪上游变化。
* **可行的建议：**
    1.  **全局统一：** 明确决定使用 `git submodule`。
    2.  **修改 Story 1.1:** 将 AC3 的 `WhisperX` 移除。添加一个新的 AC："WhisperX git submodule initialized at `ai_services/whisperx`."
    3.  **修改 `requirements.txt`:** 移除 `whisperx`。您可能需要添加 `WhisperX` 的*依赖项*（如 `faster-whisper`, `torch`），但不是 `whisperx` 包本身。

---

### � 3. 需求与故事的微调

#### A. 澄清“2小时” vs “2GB”
* **问题所在：**
    * **PRD (NFR-004):** "...handle files up to 2 hours duration."
    * **Epics (Story 1.2):** "...Handles files up to 2GB size."
* **风险分析：**
    这两个限制并不等同。一个2小时的 `MP4` 视频根据比特率的不同，可能从 500MB 到 10GB 不等。一个2小时的 `WAV` 音频大约是 1.5GB。一个2小时的 `MP3` 可能只有 100MB。
* **可行的建议：**
    您需要明确哪个是真正的限制。
    * **如果是 GPU 显存限制：** 那么“时长”是更相关的指标 (NFR-004)。
    * **如果是服务器存储限制：** 那么“文件大小”是更相关的指标 (Story 1.2)。
    我猜测“时长”是 WhisperX 的主要考量。如果是这样，您应该**移除2GB的文件大小限制**（或大幅提高它），但在上传时**检查媒体文件的时长**（可以使用 `ffprobe`），如果超过2小时则拒绝。

#### B. Story 2.7 (E2E 测试) 的规模
* **问题所在：** `epics.md` 中提到故事应该是“AI-agent sized (2-4 hour focused session)”。但 Story 2.7 (End-to-End Integration Testing) 的 AC 极其庞大（跨浏览器测试、性能验证、错误处理验证...）。
* **风险分析：**
    这是一个“陷阱”故事。它不是一个2-4小时的任务，它是一个持续的QA（质量保障）阶段。
* **可行的建议：**
    将 Story 2.7 **重命名为“Story 2.7: MVP 候选版交付与验收”**。将其 ACs 视为一个**发布清单 (Release Checklist)**，而不是一个单一的开发故事。这能更准确地管理期望。

---

### 总结

您的项目规划已经非常接近完美。上述建议旨在修补几个关键的“接缝”，防止它们在实施过程中裂开。

**最高优先级的行动项：**

1.  **立即解决 NFR-003 冲突：** 使用 `localStorage` 来防止因刷新导致的数据丢失。
2.  **重新评估 Story 1.2：** 确认您需要一个“分块流式上传”策略来处理 2GB 文件，并相应调整故事。
3.  **调整 Story 1.3：** 将进度更新从“百分比”改为“基于阶段的消息”，以匹配 WhisperX 的黑盒特性。
