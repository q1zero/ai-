
# 项目核心约束 (System Rules)

1. **技术栈严格限制**:
   - 后端: Django 4.2+, DRF, Celery, Redis.
   - 前端: React 18, Vite, TypeScript, TailwindCSS, Ant Design.
   - AI 工具: Edge-TTS (Python库), OpenAI SDK (调用 DeepSeek), MoviePy.
   - 数据库: PostgreSQL (开发环境可用 SQLite 代替，但需保持兼容).

2. **代码风格**:
   - Python 代码必须有 Type Hints (类型提示)。
   - React 组件必须是 Functional Components + Hooks。
   - 所有关键函数必须写注释 (Docstrings)。
   - 严禁使用过时的库 (如 pyttsx3)，必须使用我指定的 edge-tts。

3. **文件结构**:
   - 保持 Django 标准结构 (apps 分离)。
   - 前端组件放在 `frontend/src/components`。
   
这份计划的核心架构设计为：**Django (数据中心/渲染中心) + React (控制台) + n8n (AI 资源调度链)**。

---

# 项目名称：基于热点舆情的自动化视频生成系统 (AutoVideo-Gen)

## 1. 技术栈规范 (Tech Stack)
*   **后端**: Python 3.9+, Django 4.2+, Django REST Framework (DRF), Celery (异步任务), Redis (缓存/消息队列).
*   **视频处理**: `MoviePy` (Python库，用于合成视频，**这是关键，避免纯调包**) 或 `FFmpeg`.
*   **前端**: React 18 (Vite), TypeScript, TailwindCSS, Ant Design (或 Shadcn/ui), React Query.
*   **AI 工作流**: n8n (Docker部署), LLM (OpenAI/DeepSeek), Stable Diffusion/Midjourney (绘图), Edge-TTS (免费语音合成).
*   **数据库**: PostgreSQL.

---

## 2. 数据库设计方案 (Database Schema)
**指令给 AI：** 请按照以下 Model 结构创建 Django App `core` 和 `video`。

### 2.1 应用：`core` (基础数据)
*   **Model: `HotTopic` (热点话题)**
    *   `title` (Char): 标题
    *   `platform` (Char): 来源平台 (Weibo, Zhihu, Baidu)
    *   `hot_value` (Int): 热度值
    *   `summary` (Text): AI 自动生成的摘要
    *   `created_at` (DateTime): 抓取时间
    *   `is_used` (Boolean): 是否已用于生成视频

*   **Model: `PromptTemplate` (提示词模板)**
    *   `name` (Char): 模板名称 (e.g., "悬疑解说风", "新闻播报风")
    *   `script_prompt` (Text): 用于生成脚本的 System Prompt
    *   `image_prompt_prefix` (Text): 用于生成绘图提示词的前缀

### 2.2 应用：`video` (视频业务)
*   **Model: `VideoProject` (视频项目)**
    *   `topic` (ForeignKey -> HotTopic)
    *   `status` (Enum): `DRAFT` (草稿/脚本生成中), `WAIT_CONFIRM` (待人工确认脚本), `RENDERING` (合成中), `COMPLETED` (完成), `FAILED` (失败)
    *   `video_file` (FileField): 最终视频文件
    *   `cover_image` (ImageField): 封面图

*   **Model: `VideoScript` (分镜脚本 - 核心)**
    *   `project` (ForeignKey -> VideoProject)
    *   `content` (JSON): 存储分镜列表。
    *   *JSON 结构示例*:
        ```json
        [
          {
            "order": 1,
            "text": "今天微博热搜第一名...",
            "image_prompt": "A crowd of people holding smartphones...",
            "image_path": "/media/temp/1_img.png",
            "audio_path": "/media/temp/1_audio.mp3",
            "duration": 5.0
          }
        ]
        ```

---

## 3. 后端开发任务清单 (Backend Tasks)

### 3.1 爬虫与数据清洗 (Service Layer)
*   **任务**: 编写 `utils/crawler.py`。
*   **功能**:
    1.  抓取微博热搜榜 API。
    2.  抓取知乎热榜 API。
    3.  **数据清洗**: 使用 `jieba` 进行简单关键词聚类，避免重复话题入库。
*   **定时任务**: 使用 Celery Beat 每 2 小时执行一次 `fetch_hot_topics` 任务。

### 3.2 核心业务逻辑 (Views & Serializers)
*   **API**: `POST /api/video/generate_script/`
    *   **逻辑**: 接收 `topic_id` 和 `template_id` -> 调用 LLM (或 n8n webhook) -> 生成分镜脚本 JSON -> 存入 `VideoScript` -> 状态变更为 `WAIT_CONFIRM`。
*   **API**: `POST /api/video/confirm_render/`
    *   **逻辑**: 用户在前端修改完脚本后点击确认 -> 触发 Celery 任务 `task_render_video`。

### 3.3 视频渲染引擎 (Heavy Logic)
*   **方案**: 这是一个纯 Python 的实现，用于展示工作量。
*   **Celery 任务 `task_render_video(project_id)`**:
    1.  读取 `VideoScript` 中的 JSON。
    2.  **资源准备**:
        *   遍历分镜，检查是否有图片和音频。如果为空，调用 n8n Webhook 或直接调 API 补充资源（下载到本地）。
    3.  **合成**:
        *   使用 `MoviePy` 加载音频。
        *   加载图片并设置 `set_duration` 等于音频长度。
        *   添加缩放效果 (Zoom-in effect) 增加动态感。
        *   使用 `TextClip` 生成字幕（可选，难度较高，可用 SRT 字幕文件代替）。
        *   `concatenate_videoclips` 合成最终 mp4。
    4.  保存文件路径，状态更新为 `COMPLETED`。

---

## 4. n8n 自动化工作流设计 (Workflow Design)

**指令给 AI：** 请设计一个 n8n 工作流 JSON 逻辑，用于辅助 Django 生成素材。

### 工作流 A：素材生成器 (Asset Generator)
*   **Trigger**: Webhook (接收 Django 发来的：`{"prompt": "...", "type": "image/audio"}`)
*   **Branch 1 (Image)**:
    *   Node: OpenAI (DALL-E 3) 或 Stable Diffusion API。
    *   Output: 图片 URL。
*   **Branch 2 (Audio)**:
    *   Node: HTTP Request (调用 Edge-TTS 服务)。
    *   Output: 音频文件 (Base64 或 URL)。
*   **Response**: 返回生成的资源地址给 Django。

*(注：为了毕设简单化，建议脚本生成直接在 Django 里调 OpenAI 接口，n8n 主要用来做“多模态资源的获取”，或者干脆在 Django 里全部写 Python 代码调 API，n8n 作为备选方案展示)*

---

## 5. 前端开发任务清单 (Frontend Tasks)

### 5.1 页面结构
1.  **Dashboard (首页)**
    *   左侧：**热搜列表** (Tabs: 微博/知乎)。列表项包含：排名、标题、热度、"生成视频"按钮。
    *   右侧：**项目状态概览** (进行中/已完成)。
2.  **Script Editor (脚本工坊 - 核心亮点)**
    *   界面：左侧是分镜列表（卡片式），右侧是实时预览（文字+图片占位符）。
    *   **功能**:
        *   **可编辑**: 用户可以修改 AI 生成的台词。
        *   **重绘**: 点击图片的“重新生成”按钮，调用 API 换图。
        *   **试听**: 点击台词旁的播放按钮，调用 TTS 试听语音。
        *   **底部按钮**: "确认并开始渲染"。
3.  **Gallery (视频库)**
    *   视频播放器，支持下载，支持查看元数据（生成耗时、使用的 Prompt）。

---

## 6. 开发步骤与 Prompt 指令 (Copy to AI)

你可以按照以下顺序，一段一段发给 AI 助手：

### 第一步：初始化后端
> "请帮我初始化一个 Django 项目，使用 DRF。创建两个 App：`core` 和 `video`。请根据以下 Model 定义写出 `models.py` 代码..." (附上第2节的数据库设计)

### 第二步：编写爬虫与信号
> "在 `core` app 下创建一个 `utils` 文件夹，帮我写一个 `crawler.py`。需要使用 `requests` 和 `BeautifulSoup` 爬取微博热搜榜的前 10 条数据，并保存到 `HotTopic` 表中。如果标题已存在则更新热度，不存在则创建。"

### 第三步：实现脚本生成逻辑
> "请在 `video` app 中编写一个 ViewSet。当接收到 POST 请求时，调用 OpenAI 的 API（请封装成 Service），根据热点标题生成一个 JSON 格式的视频分镜脚本。JSON 结构需要包含：序号、分镜描述、旁白台词、画面提示词。将结果存入 `VideoScript` 模型。"

### 第四步：前端脚本编辑器 (难点)
> "请使用 React + Ant Design 创建一个脚本编辑组件。数据源是一个包含分镜信息的数组。每个分镜卡片需要包含：文本域（修改台词）、图片预览区、重新生成图片按钮。请帮我写出核心的 JSX 结构和 State 管理逻辑。"

### 第五步：视频合成 (Python MoviePy)
> "请帮我写一个 Celery Task。输入是 `VideoScript` 的 ID。逻辑是：1. 遍历脚本中的图片 URL 下载到本地；2. 调用 Edge-TTS 库将台词转为 mp3；3. 使用 `moviepy` 库将图片和音频对齐，合成一个 mp4 视频；4. 保存到 Django 的 Media 目录。"

---

## 7. 毕设创新点总结 (用于论文/答辩)

1.  **Human-in-the-loop (人在回路)**: 并非全自动黑盒，而是引入了“脚本编辑器”环节，用户可以对 AI 生成的内容进行修正，保证了视频的质量和准确性。
2.  **动态工作流编排**: 后端架构解耦，Prompt 模板与渲染逻辑分离，支持不同风格（幽默、严肃）的视频生成。
3.  **自动化数据管道**: 从舆情发现到内容生产的全链路自动化，模拟了现代媒体机构的工业化生产流程。