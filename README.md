# AudioAlchemist 🎵➡️📝

> 将音频"炼成"文字的魔法工具

AudioAlchemist 是一个基于 Web 的音频转录应用，用户可以上传音频文件，系统使用 WhisperX 进行高精度转录，并提供多种格式的文本结果下载。

## ✨ 特性

- 🎯 **高精度转录**: 基于 WhisperX 的先进语音识别技术
- 🚀 **异步处理**: Celery + Redis 实现高效的后台任务处理
- 📱 **现代界面**: Vue.js 构建的响应式 Web 界面
- 📄 **多格式导出**: 支持 TXT、SRT 等多种格式下载
- 🔍 **实时监控**: 完整的日志记录和任务状态跟踪
- 🐳 **容器化部署**: Docker Compose 一键部署

## 🛠️ 技术栈

- **后端**: FastAPI + Python 3.11
- **前端**: Vue.js + TypeScript
- **异步任务**: Celery + Redis
- **转录引擎**: WhisperX
- **数据库**: PostgreSQL / SQLite
- **部署**: Docker Compose

## 🚀 快速开始

### 本地开发环境（推荐）

按照技术执行计划书的要求，我们采用 **"本地开发 → 本地测试 → 功能验证 → Docker化 → 部署测试"** 的工作流。

1. **环境准备**
   ```bash
   git clone <repository-url>
   cd AudioAlchemist

   # 创建 conda 环境
   conda env create -f environment.yml
   conda activate audioalchemist
   ```

2. **启动背景服务**
   ```bash
   # Windows
   powershell -ExecutionPolicy Bypass -File scripts/start-local-dev.ps1

   # Linux/macOS
   ./scripts/start-dev.sh
   ```

3. **启动应用服务**
   ```bash
   # 启动 FastAPI (终端1)
   conda activate audioalchemist
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # 启动 Celery Worker (终端2)
   conda activate audioalchemist
   cd backend
   celery -A app.core.celery_app worker --loglevel=info
   ```

4. **运行测试**
   ```bash
   cd backend
   pytest
   ```

### 生产环境部署

```bash
# 复制环境配置
cp .env.local .env
# 编辑 .env 文件，配置生产环境参数

# 启动所有服务
# Windows
powershell -ExecutionPolicy Bypass -File scripts/start-prod.ps1

# Linux/macOS
./scripts/start-prod.sh
```

## 🌐 访问应用

启动成功后，访问以下地址：

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/

## 🧪 测试

### 本地测试

在本地conda环境中运行测试：

```bash
cd backend
pytest -v
```

运行特定测试类别：

```bash
# API测试
pytest app/tests/test_main.py -v

# 带覆盖率的测试
pytest --cov=app --cov-report=term-missing

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html
```

### 端到端测试

运行完整的E2E测试脚本：

```bash
python scripts/test_transcriber_cli.py
```

该脚本将：
1. 检查API健康状态
2. 创建测试音频文件
3. 上传并转录音频
4. 轮询完成状态
5. 测试下载功能

## 📊 日志解读

### Structlog结构化日志

AudioAlchemist使用Structlog进行结构化、上下文化的日志记录。所有日志都包含相关上下文，如任务ID和文件路径。

#### 开发环境
开发环境中，日志格式化为易读的彩色输出：

```log
2024-07-02 12:34:56 [info] Starting transcription task [task_id=abc123] [file_path=/uploads/audio.wav]
```

#### 生产环境
生产环境中，日志以JSON格式输出，便于解析：

```json
{"timestamp": "2024-07-02T12:34:56Z", "level": "info", "event": "Starting transcription task", "task_id": "abc123", "file_path": "/uploads/audio.wav"}
```

### 关键日志事件

- **文件上传**: `Receiving audio file`, `Audio file saved`
- **任务创建**: `Celery task sent`
- **转录过程**: `Loading WhisperX model`, `Starting transcription`, `Transcription completed`
- **下载事件**: `Generated TXT content for download`, `Generated SRT content for download`

## 🏗️ 架构概览

```
Frontend (Vue.js) → FastAPI → Celery → WhisperX
                      ↓
                 PostgreSQL ← Redis
```

## 📚 文档

- [本地开发环境搭建指南](docs/implementation/本地开发环境搭建指南.md)
- [技术执行计划书](docs/project/AudioAlchemist%20-%20技术执行计划书%20v1.0.md)
- [里程碑任务清单](docs/project/)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

[MIT License](LICENSE)