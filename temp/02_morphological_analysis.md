  ---
  架构组合矩阵分析

  你的选择映射：

  | 维度    | 选择               | 复杂度    | 理由        |
  |-------|------------------|--------|-----------|
  | 编辑持久化 | localStorage (B) | 低 ⭐    | 简单实现，意外保护 |
  | 通信机制  | SSE (C)          | 中 ⭐⭐   | 长时间转录场景最优 |
  | 状态管理  | 多组件拆分 (D)        | 中 ⭐⭐   | 考虑扩展性     |
  | 媒体处理  | Range请求 (B)      | 低-中 ⭐⭐ | 适配不确定大小   |
  | 导出    | 服务端渲染 (A)        | 低 ⭐    | 已确定       |

  ---
  组合协同效应分析

  ✅ 强协同组合 (1+1>2)

  1. localStorage + SSE 的完美配合
  - SSE推送进度 → localStorage实时保存转录中间结果
  - 场景： 用户在转录90%时意外关闭浏览器，重新打开页面：
    - ✅ localStorage恢复到90%状态
    - ✅ 重新建立SSE连接，继续接收最后10%
  - 实现要点： SSE每次推送部分结果时，同步写入localStorage

  2. 多组件拆分 + localStorage 的优雅配合
  - Composable模式天然支持localStorage持久化
  - 建议架构：
  // useSubtitles.js - Composable
  export function useSubtitles(jobId) {
    const subtitles = ref(loadFromLocalStorage(jobId) || [])

    watch(subtitles, () => {
      saveToLocalStorage(jobId, subtitles.value)
    }, { deep: true })

    return { subtitles, ... }
  }
  - 好处： 持久化逻辑与业务逻辑分离，多个组件共享同一数据源

  3. Range请求 + 不确定媒体大小
  - Range请求对小文件和大文件都友好
  - 浏览器原生<video>标签自动处理Range请求
  - 无需额外开发： HTML5 video/audio自动处理

  ---
  ⚠️ 需要注意的组合点

  1. localStorage + 多用户场景的隐患
  - 问题： 如果用户在不同浏览器/设备打开同一个job_id？
  - localStorage是浏览器本地的，不同设备不同步
  - 解决方案：
    - 选项1：localStorage存储时加上设备标识，允许多设备各自编辑
    - 选项2：检测冲突（服务端记录最后导出版本，localStorage检查版本号）
    - 推荐： 选项1更简单，符合"单用户编辑"的设计

  2. SSE + 浏览器兼容性
  - SSE支持： 现代浏览器全支持（除了IE，但IE已退役）
  - 移动端： iOS Safari、Android Chrome都完全支持
  - 降级策略： 如果SSE连接失败，自动fallback到轮询
  if (typeof EventSource !== 'undefined') {
    // 使用SSE
  } else {
    // 降级到轮询
  }

  ---
  推荐架构组合方案

  🎯 最优组合：混合持久化 + SSE + Composable模式

  ┌─────────────────────────────────────────────────┐
  │  前端架构（Vue 3）                                │
  ├─────────────────────────────────────────────────┤
  │  组件层：                                         │
  │    ├─ EditorView.vue (编辑器主页面)              │
  │    ├─ MediaPlayer.vue (媒体播放器组件)           │
  │    ├─ SubtitleEditor.vue (字幕编辑器组件)        │
  │    └─ ExportPanel.vue (导出面板组件)             │
  │                                                  │
  │  Composables层：                                 │
  │    ├─ useSubtitles(jobId)                       │
  │    │   ├─ localStorage持久化                    │
  │    │   ├─ 编辑操作（增删改）                     │
  │    │   └─ 时间戳跳转逻辑                         │
  │    ├─ useMediaPlayer()                          │
  │    │   └─ 播放控制 + seek功能                   │
  │    └─ useSSEProgress(jobId)                     │
  │        └─ SSE连接 + fallback轮询               │
  └─────────────────────────────────────────────────┘
                        ↕ HTTP/SSE
  ┌─────────────────────────────────────────────────┐
  │  后端架构（FastAPI + Celery）                     │
  ├─────────────────────────────────────────────────┤
  │  API层：                                         │
  │    POST   /upload          → job_id             │
  │    GET    /progress/{id}   → SSE stream         │
  │    GET    /result/{id}     → JSON (text+时间戳) │
  │    GET    /media/{id}      → Range支持的流       │
  │    POST   /export/{id}     → 接收编辑版+返回文件 │
  │                                                  │
  │  任务队列：Celery                                 │
  │    └─ transcribe_task(file, job_id)            │
  │        └─ 定期发布进度到Redis（供SSE读取）       │
  │                                                  │
  │  存储：                                           │
  │    ├─ 媒体文件（原始）                           │
  │    ├─ 转录结果（原始JSON）                       │
  │    └─ 导出版本（编辑后JSON + SRT/TXT）          │
  └─────────────────────────────────────────────────┘

  ---
  关键实现细节

  1. localStorage策略（解决意外关闭问题）

  // 存储键设计
  const STORAGE_KEY = `klipnote_edits_${jobId}_${deviceId}`

  // 自动保存：编辑时防抖保存
  watch(subtitles,
    debounce(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        jobId,
        timestamp: Date.now(),
        subtitles: subtitles.value
      }))
    }, 1000),
    { deep: true }
  )

  // 页面加载时恢复
  onMounted(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      // 显示提示："检测到未完成的编辑，是否恢复？"
      if (confirm('检测到未完成的编辑，是否恢复？')) {
        subtitles.value = data.subtitles
      }
    }
  })

  // 导出成功后清理
  function onExportSuccess() {
    localStorage.removeItem(STORAGE_KEY)
  }

  优势：
  - ✅ 意外关闭浏览器 → 数据不丢失
  - ✅ 刷新页面 → 可以恢复编辑
  - ✅ 导出后自动清理 → 不占用存储空间
  - ✅ 设备隔离 → 多设备不冲突

  ---
  2. SSE进度推送（处理长时间转录）

  服务端（FastAPI）:
  @app.get("/progress/{job_id}")
  async def stream_progress(job_id: str):
      async def event_generator():
          while True:
              # 从Redis读取任务进度
              progress = redis.get(f"progress:{job_id}")
              if progress:
                  data = json.loads(progress)
                  yield f"data: {json.dumps(data)}\n\n"

                  if data['status'] == 'completed':
                      break
              await asyncio.sleep(1)

      return StreamingResponse(
          event_generator(),
          media_type="text/event-stream"
      )

  客户端（Vue Composable）:
  export function useSSEProgress(jobId) {
    const progress = ref(0)
    const status = ref('pending')
    const result = ref(null)

    function connect() {
      const eventSource = new EventSource(`/progress/${jobId}`)

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        progress.value = data.progress
        status.value = data.status

        if (data.status === 'completed') {
          result.value = data.result
          eventSource.close()
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        // Fallback到轮询
        startPolling()
      }
    }

    return { progress, status, result, connect }
  }

  ---
  3. 媒体Range请求支持（适配不确定大小）

  服务端（FastAPI）:
  from fastapi.responses import FileResponse
  from starlette.background import BackgroundTask

  @app.get("/media/{job_id}")
  async def stream_media(job_id: str, request: Request):
      file_path = get_media_path(job_id)

      # FastAPI自动处理Range请求
      return FileResponse(
          file_path,
          media_type="video/mp4",  # 或audio/mpeg
          headers={
              "Accept-Ranges": "bytes",
              "Cache-Control": "public, max-age=3600"
          }
      )

  客户端（Vue组件）:
  <template>
    <video
      ref="videoRef"
      :src="`/media/${jobId}`"
      @timeupdate="onTimeUpdate"
      controls
    />
  </template>

  <script setup>
  // 浏览器自动处理Range请求，无需手动实现
  // 拖动进度条、快进快退都自动优化加载
  </script>

  好处：
  - ✅ 小文件（几分钟音频）→ 快速加载全部
  - ✅ 大文件（小时级视频）→ 按需加载，拖动流畅
  - ✅ 无需额外开发 → 浏览器原生支持

  ---
  额外发现的组合优势

  4. localStorage + 数据飞轮的增强

  记得你的"数据飞轮"洞察吗？localStorage可以增强它：

  // 当用户导出时
  function exportEdits() {
    const edits = calculateEditDelta(originalSubtitles, editedSubtitles)

    // 发送到服务端（不仅用于导出，还用于训练数据）
    await fetch(`/export/${jobId}`, {
      method: 'POST',
      body: JSON.stringify({
        original: originalSubtitles,
        edited: editedSubtitles,
        edits: edits,  // 具体修改了什么
        edit_time: totalEditTime,  // 用户花了多长时间编辑
        edit_count: edits.length   // 改了多少处
      })
    })

    // 清理localStorage
    localStorage.removeItem(STORAGE_KEY)
  }

  数据价值：
  - 服务端收到：原始转录 + 人工修正 + 编辑行为数据
  - 可以分析：哪些词容易错？哪些场景需要更多编辑？
  - 意外收获： 编辑时间和编辑次数可以作为"转录质量指标"

  ---
  最终推荐配置

  | 层面    | 技术选择                  | 实现复杂度    | 用户体验提升    |
  |-------|-----------------------|----------|-----------|
  | 编辑持久化 | localStorage + 防抖自动保存 | ⭐⭐ (2天)  | ⭐⭐⭐⭐⭐ 极大  |
  | 进度通信  | SSE + fallback轮询      | ⭐⭐⭐ (3天) | ⭐⭐⭐⭐ 很好   |
  | 状态管理  | Composables (3个核心)    | ⭐⭐ (2天)  | ⭐⭐⭐⭐ 扩展性好 |
  | 媒体播放  | 原生video + Range请求     | ⭐ (1天)   | ⭐⭐⭐⭐ 流畅   |
  | 导出    | 服务端渲染SRT/TXT          | ⭐ (1天)   | ⭐⭐⭐ 标准    |

  总开发时间估算： 9-11天（前端+后端集成）