-----

### � 1. 关键风险：缺失的 `ffmpeg` 核心依赖

这是最关键的一个疏漏，它将导致所有转录任务失败。

  * **问题所在：**
    Task 1 的 `requirements.txt` 中包含了 `python-ffmpeg`。这是一个 `ffmpeg` 命令的 Python *包装器*（wrapper），但它**并不安装 `ffmpeg` 二进制程序本身**。

  * **风险分析：**
    `WhisperX`（以及底层的 `torchaudio`）在加载音视频文件时，会通过命令行调用 `ffmpeg` 程序。如果 `Dockerfile` 构建的镜像中没有安装 `ffmpeg`，那么在 Story 1.3 中，当 Celery worker 尝试处理第一个文件时，会立即因“`ffmpeg: command not found`”而失败。

  * **可行的建议：**
    在 **Task 1** 的 **`Dockerfile` 子任务**中，明确添加 `ffmpeg` 的安装步骤。

    **修改 `Dockerfile` 子任务为：**

    ```dockerfile
    # (基于一个 nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04 这样的基础镜像)
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        ffmpeg \
        && apt-get clean && \
        rm -rf /var/lib/apt/lists/*

    # ... (后续的 pip install 步骤)
    ```

-----

### � 2. 技术陷阱：PyTorch 与 CUDA 版本的强绑定

这个问题会导致 GPU 无法被 `torch` 识别，使 GPU 配置失效。

  * **问题所在：**
    Task 1 的 `requirements.txt` 中指定了 `torch==2.x`。同时，Task 5 的 `README` 和 Task 1 的 `Dockerfile` 都指向了 "CUDA 11.8+"。

  * **风险分析：**
    PyTorch (`torch`) 对 CUDA 版本**极度敏感**。如果只在 `requirements.txt` 中写入 `torch`，`pip` 几乎一定会下载一个 CPU-only 版本，或者是一个为*最新* CUDA (如 12.1) 编译的版本。
    无论哪种情况，它都无法与您 Docker 镜像中的 CUDA 11.8 驱动程序匹配，导致 `torch.cuda.is_available()` 返回 `false`。

  * **可行的建议：**
    **从 `requirements.txt` 中移除 `torch` 和 `torchaudio`**。
    转而在 **Task 1** 的 **`Dockerfile` 子任务**中，使用 PyTorch 官方指定的 `index-url` 来安装与 CUDA 11.8 匹配的特定版本。

    **修改 `Dockerfile` 子任务为：**

    ```dockerfile
    # (在安装 ffmpeg 之后)

    # 显式安装与 CUDA 11.8 绑定的 PyTorch 版本
    RUN pip install torch==2.1.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118

    # 从 requirements.txt 安装其余的依赖
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    ```

    *(注意：`requirements.txt` 中应*删除\* `torch` 和 `torchaudio`，以避免冲突。)\*

-----

### ⚙️ 3. 架构优化：Docker Compose 启动顺序

这是一个常见的启动时（Startup）竞态条件问题。

  * **问题所在：**
    Task 1 的 `docker-compose.yaml` 定义了 `web`, `worker`, `redis` 服务。

  * **风险分析：**
    `web` (FastAPI) 和 `worker` (Celery) 服务都依赖 `redis` 服务。如果它们在 `redis` 准备好接受连接*之前*启动，它们会因连接失败而崩溃，并可能进入重启循环，导致开发环境启动非常不稳定。

  * **可行的建议：**
    在 **Task 1** 的 **`docker-compose.yaml` 子任务**中，为 `web` 和 `worker` 服务添加 `depends_on` 和 `healthcheck`。

    **修改 `docker-compose.yaml` 子任务为：**

    ```yaml
    services:
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
        # 添加健康检查，确保 Redis 真正准备好了
        healthcheck:
          test: ["CMD", "redis-cli", "ping"]
          interval: 1s
          timeout: 3s
          retries: 30

      web:
        build: .
        # ...
        # 添加依赖，等待 redis 健康检查通过
        depends_on:
          redis:
            condition: service_healthy

      worker:
        build: .
        # ...
        # 添加依赖，等待 redis 健康检查通过
        depends_on:
          redis:
            condition: service_healthy
    ```

-----

### � 4. 细节完善：`.env.example` 的显式创建

这是一个小细节，但能完善配置流程。

  * **问题所在：**
    “Dev Notes”部分的“Source Tree”提到了 `.env.example`，Task 4 的 `.gitignore` 也提到了 `.env`，但 Task 1 的*任务列表*中没有明确创建这个文件。
  * **风险分析：**
    `app/config.py` 的 Pydantic 设置会依赖环境变量。如果没有一个 `.env.example` 模板，新开发者（或AI代理）不知道需要设置哪些变量。
  * **可行的建议：**
    在 **Task 1** 中添加一个明确的子任务：
      * `[ ] 创建 .env.example 文件，包含 CELERY_BROKER_URL, CELERY_RESULT_BACKEND, WHISPER_MODEL 等占位符。`
