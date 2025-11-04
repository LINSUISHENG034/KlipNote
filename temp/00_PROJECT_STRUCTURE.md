# KlipNote 项目结构 (Direct Transcribe 模块)

本项目已清理，仅保留与 `direct_transcribe.py` 模块相关的核心代码。

## 核心文件

### 主脚本
- `direct_transcribe.py` - WhisperX 流式转录测试脚本

### Backend 核心模块

#### AI 服务 (`backend/ai_services/`)
- `model_manager.py` - AI模型管理器，负责模型加载和缓存
- `providers/base.py` - 转录服务接口定义
- `providers/streaming_whisperx_provider.py` - WhisperX 流式转录实现
- `whisperx/` - 自定义 WhisperX 源代码

#### 应用核心 (`backend/app/`)
- `core/config.py` - 应用配置管理
- `core/enums.py` - 枚举定义
- `core/logging_config.py` - 日志配置
- `schemas/transcription.py` - 转录配置和响应schema
- `utils/audio_utils.py` - 音频处理工具

## 配置文件
- `.env` - 环境配置
- `.env.local` - 本地环境配置
- `pyproject.toml` - Python 项目配置
- `uv.lock` - UV 包管理器锁定文件
- `environment.yml` - Conda 环境配置

## 其他目录
- `.git/` - Git 版本控制
- `.venv/` - Python 虚拟环境
- `models/` - AI 模型缓存
- `backend/models/` - 模型缓存（备用）
- `logs/` - 应用日志

## 已删除的模块
以下模块已被删除，因为与 direct_transcribe.py 无关：
- frontend/ - 前端代码
- legacy/ - 遗留代码
- docs/ - 文档
- config/ - 配置目录
- scripts/ - 脚本工具
- tests/ - 测试代码
- backend/api/ - REST API端点
- backend/models/ - 数据库模型
- backend/repository/ - 数据仓储层
- backend/services/ - 其他服务
- backend/celery_worker/ - Celery 任务队列
- backend/alembic/ - 数据库迁移

## 使用方法

运行转录测试：
```bash
python direct_transcribe.py
```

## 依赖关系

direct_transcribe.py 依赖链：
```
direct_transcribe.py
  └─ backend.ai_services.providers.streaming_whisperx_provider
      ├─ backend.ai_services.providers.base
      ├─ backend.ai_services.model_manager
      │   ├─ backend.app.core.config
      │   │   └─ backend.app.core.logging_config
      │   └─ backend.app.core.enums
      ├─ backend.app.schemas.transcription
      │   ├─ backend.app.core.config
      │   └─ backend.app.core.enums
      └─ backend.app.utils.audio_utils
```
