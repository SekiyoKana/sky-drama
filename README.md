# Sky Drama ☁️🎬

**简体中文** | [English](README.en-US.md) | [日本語](README.ja-JP.md)

<div align="center">

<img src="apps/frontend/public/logo.png" width="200" />

当前版本： 0.1.0 Beta 

**AI 驱动的短剧创作平台：从灵感到成片**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue.js](https://img.shields.io/badge/Frontend-Vue_3-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Neumorphism](https://img.shields.io/badge/Design-Neumorphism-blue)](https://github.com/SekiyoKana/sky-drama)

</div>

> **AI is cheap, show me your story.**
>
> **你的创意与思考远比 AI 的自动生成重要得多**。
>
> Sky Drama 的初衷并非制造“工业流水线的低质量产物”，而是作为真正的创作者的 AI 联合导演，辅助您将脑海中闪烁的故事火花，打磨成触动人心的作品。
>

## 📖 简介

**Sky Drama** 是一个集成的 AI 短剧创作平台，旨在彻底改变短剧创作流程。从最初的一个灵感火花，到完整可视化的分镜脚本和视频草稿，Sky Drama 将作为您的 AI 联合导演全程协助。

它填补了文本与视频之间的鸿沟，将编剧、视觉设计师和剪辑师的功能融合在一个流畅的“软拟态 (Neumorphism)”工作区中。

### 核心支持
- 🐳 **Docker Compose** 一键部署
- 🍎 **macOS App** (Beta) 原生体验
- 🪟 **Windows App** (Beta) 原生体验
- 🌐 **多语言界面**（中文 / English / 日本語）
- ✍️ **小说模式**（开发中）

---

## ✨ 核心功能与工作流

#### Sky Drama 当前版本强依赖于Nano Banana Pro + Sora2 api, 后续版本会接入更多模型。

### 1. 本地账号系统与项目管理
<div align="center">
   <img src="docs/01_login.gif" style="margin: 0 auto" width="600" />
</div>

### 2. 全局 API 配置
支持配置多种第三方服务提供商的 API Key，灵活切换生成引擎。
<div align="center">
   <img src="docs/05_api_setting.gif" style="margin: 0 auto" width="600" />
</div>

#### API 平台扩展（OpenAI / Ollama / 火山引擎）

- `ApiMatrixTab` 新增/编辑连接时，`平台类型` 已改为下拉选框，支持：
  - `OpenAI Compatible`
  - `Ollama`
  - `Volcengine Ark (火山引擎)`
- 选择 `Ollama` 时：
  - 默认 `Base URL` 为 `http://127.0.0.1:11434/api`
  - 默认文本接口为 `POST /chat`（即完整地址 `/api/chat`）
  - 连接测试改为 `GET /tags`（即完整地址 `/api/tags`）
  - 支持配置为本机 Ollama，也支持替换为云服务器提供的 Ollama 服务地址
- 选择 `火山引擎` 时：
  - 默认 `Base URL` 为 `https://ark.cn-beijing.volces.com/api/v3`
  - 默认文本接口为 `POST /chat/completions`
  - 默认视频任务创建接口为 `POST /contents/generations/tasks`
  - 默认视频任务查询接口为 `GET /contents/generations/tasks/{task_id}`
  - 按火山方舟（Ark）OpenAI 兼容方式接入；模型参数应填写对应 `Endpoint ID`
  - 若连接测试未返回模型列表，可在工作台模型配置中手动输入模型 ID（如 `ep-xxxx`）

参考文档（官方）：
- Ollama API: https://docs.ollama.com/api
- Ollama Authentication: https://docs.ollama.com/api#authentication
- 火山引擎方舟模型推理: https://www.volcengine.com/docs/82379/1541594
- 火山引擎方舟 Chat Completions API: https://www.volcengine.com/docs/82379/1330310

#### 后端平台配置集中管理

- 平台默认配置与别名已集中到：
  - `apps/backend/app/core/providers/openai.py`
  - `apps/backend/app/core/providers/ollama.py`
  - `apps/backend/app/core/providers/volcengine.py`
- 平台注册与路由在：
  - `apps/backend/app/core/providers/registry.py`
- 兼容层保留在：
  - `apps/backend/app/core/provider_platform.py`
- 新增平台时，建议新建一个 provider 类并在 registry 注册，避免将平台分支逻辑散落到业务文件中。

#### 前端平台配置集中管理

- 前端平台抽象与默认值已集中到：
  - `apps/frontend/src/platforms/openai.ts`
  - `apps/frontend/src/platforms/ollama.ts`
  - `apps/frontend/src/platforms/volcengine.ts`
- 前端平台注册表在：
  - `apps/frontend/src/platforms/registry.ts`
- 组件（如 `ApiMatrixTab`）统一通过 registry 读取平台默认配置、别名归一化与端点规则，避免在 Vue 文件中硬编码平台分支。

### 3. 自定义您的视觉风格
上传参考图或使用预设，定义项目的整体视觉基调（如：赛博朋克、水墨风、皮克斯风格）。
<div align="center">
   <img src="docs/04_create_styles.gif" style="margin: 0 auto" width="600" />
</div>

### 4. 拟物化界面风格
脱离标准SOP工作台模板的刻板印象，强调拟物化风格。
<div align="center">
   <img src="docs/02_create_story.gif" style="margin: 0 auto" width="600" />
</div>

### 5. 灵感转化为故事
输入一个简短的创意（Premise），AI 导演将为您扩写成完整的故事大纲，并基于大纲自动生成包含对白、动作指导和分镜描述的标准剧本格式。
<div align="center">
   <img src="docs/06_ai_generate_script.gif" style="margin: 0 auto" width="600" />
</div>

### 6. 角色与场景生成，使用@将场景于角色添加进分镜
一键生成角色立绘和场景概念图，保持角色一致性，支持使用@将场景和角色引入分镜参考，增强一致性。
<div align="center">
   <img src="docs/07_generate_character.gif" height="300" />  
   <img src="docs/09_@_object.gif" height="300" />
</div>

### 7. 可视化设定集
将登场人物和场景生成全局设定集，直观预览人物关系走向。
<div align="center">
   <img src="docs/03_storybook.gif" style="margin: 0 auto" width="600" />
</div>


### 8. 时间轴剪辑
内置非线性编辑 (NLE) 时间轴，拖拽素材，调整时长，实时预览最终成片。
<div align="center">
   <img src="docs/08_timeline_editor.gif" style="margin: 0 auto" width="600" />
</div>

### 9. 应用内调试控制台（Beta）
内置前后端输出控制台，可以通过连续敲击5次Ctrl激活控制台
<div align="center">
   <img src="docs/console.png" style="margin: 0 auto" width="600" />
</div>

### 10. 深度日志与导演执行回溯
- 导演工作台每次执行都会生成 `trace_id`，并在控制台流中返回。
- 后端会将执行记录持久化到 `logs/director_runs/<run_id>.json`，包含状态流、进度、错误、耗时与结果摘要。
- 可通过接口查看历史与详情：
  - `GET /v1/logs/director-runs`
  - `GET /v1/logs/director-runs/{run_id}`

---

## 🚀 快速开始

### 方式一：Docker Compose 部署 (推荐)

无需配置复杂的 Python/Node 环境，直接运行：

```bash
git clone [https://github.com/SekiyoKana/sky-drama.git](https://github.com/SekiyoKana/sky-drama.git)
cd sky-drama
make docker-up

```

访问 `http://localhost:5173` 即可开始创作。

如果你所在网络无法访问 Docker Hub（例如拉取 `python:3.12-slim` 超时），可先创建并编辑镜像源配置：

```bash
make docker-env
# 编辑 deploy/docker/.env，按你的网络填入镜像站
# 例如：
# PYTHON_BASE_IMAGE=docker.m.daocloud.io/python:3.12-slim
# NODE_BASE_IMAGE=docker.m.daocloud.io/node:20-alpine
# NGINX_BASE_IMAGE=docker.m.daocloud.io/nginx:alpine
# 如果需要代理，也可配置：
# HTTP_PROXY=http://host.docker.internal:7890
# HTTPS_PROXY=http://host.docker.internal:7890
# NO_PROXY=localhost,127.0.0.1,backend
make docker-up
```

### 方式二：桌面应用 (Beta)

请前往 [Releases](https://github.com/SekiyoKana/sky-drama/releases) 页面下载对应平台的安装包, 或自行打包：

* **macOS / Linux**: 运行 `./scripts/desktop/build.sh`
* **Windows**: 运行 `.\scripts\desktop\build.bat`

### 方式三：源码开发

#### 前置要求

* Node.js (推荐 v23，最低 v20.12+，推荐使用 `.nvmrc`)
* pnpm (v9, 推荐通过 Corepack 管理)
* Python (v3.12+)
* Rust 工具链（`cargo` / `rustc`，仅桌面端打包需要）
* **FFmpeg (核心组件)**: ⚠️ **必须手动安装**。
* 请前往 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载。
* 安装后**必须**将其添加到系统的 `PATH` 环境变量中，确保在终端输入 `ffmpeg` 可直接运行。



#### 安装步骤

1. **克隆仓库**
```bash
git clone [https://github.com/SekiyoKana/sky-drama.git](https://github.com/SekiyoKana/sky-drama.git)
cd sky-drama
nvm use || nvm install
corepack enable

```


2. **后端设置**
```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 运行服务
uvicorn app.main:app --host 127.0.0.1 --port 11451 --reload

```


3. **前端设置**
```bash
cd apps/frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev

```

### 方式四：工程化命令（团队协作推荐）

根目录提供 `Makefile`，可统一日常开发与打包命令：

```bash
# 一次性安装依赖（后端 + 前端）
make setup

# 本地开发
make dev-backend
make dev-frontend

# Docker 一键启动
make docker-up

# 桌面端打包（macOS/Linux）
make desktop-build
```

桌面打包支持以下环境变量：
- `SKYDRAMA_SKIP_INSTALL=1`：跳过依赖安装（适合 CI 缓存命中场景）
- `SKYDRAMA_TAURI_BUNDLES=app`：自定义 Tauri bundles 类型

目录与工程规范详见：`docs/project-structure.md`



---

## 🛠 技术栈

### 前端

* **框架**: Vue 3 (Composition API)
* **构建工具**: Vite
* **样式**: TailwindCSS + 自定义软拟态设计 (Neumorphism)
* **状态管理**: Pinia
* **路由**: Vue Router

### 后端

* **框架**: FastAPI (Python 3.12+)
* **数据库**: SQLAlchemy (SQLite default)
* **AI 集成**: 模块化 "Skills" 架构 (并非claude skills, 未来可能会支持)
* **验证**: Pydantic

## ⚠️ 注意事项

1. **FFmpeg 环境依赖**
本项目强依赖 FFmpeg 进行视频合成、转码及剪辑。**如果您的电脑未安装 FFmpeg，将无法生成视频**。源码运行用户请务必自行下载并配置环境变量。
2. **视频模型支持**
目前视频生成功能仅深度适配 **Sora 2** 模型。由于目前支持 Sora 2 的第三方 API 厂商数量较少，若您需要接入其他视频模型（如 Runway, Pika 等），请耐心等待后续版本的更新与适配。
3. **自定义 API 适配**
Sky Drama 默认的 Sora 2 API 策略基于标准的 `/videos` (创建) 和 `/videos/{task_id}` (查询) 接口格式。
如果您使用的第三方 API 厂商采用了不同的接口规范（例如：流式输出、WebSocket 或非标准端点），您需要自行编写 **转换器 (Formatter)** 进行适配。
* **现有参考示例**: `apps/backend/app/utils/sora_api/yi.py` (针对流式接口的适配实现)
* **如何添加新转换器**:
请在 `apps/backend/app/utils/sora_api/` 目录下创建一个新的 Python 文件（例如 `my_provider.py`），并继承 `Base` 类实现以下逻辑：
```python
# apps/backend/app/utils/sora_api/my_provider.py
from .base import Base
from typing import List, Any, Dict

class MyProvider(Base):
    name = "MyProvider"  # 在前端设置界面中显示的名称
    base_url_keyword = "api.myprovider.com"  # 用于自动识别的 URL 特征

    def create(self, base_url: str, apikey: str, model: str, prompt: str, seconds: int, size: str, watermark: bool, images: List[Any]) -> str:
        # 1. 设置认证信息
        self.set_auth(base_url, apikey)
        # 2. 调用您的第三方 API 创建任务
        # ...
        # 3. 返回任务 ID (task_id)
        return "task_123456"

    def _query_status(self, task_id: str) -> Dict[str, Any]:
        # 1. 调用第三方 API 查询任务状态
        # ...
        # 2. 返回统一格式的状态字典
        return {
            "status": "completed", # 或 "processing", "failed"
            "video_url": "https://...",
            "progress": 100,
            "fail_reason": None
        }

```





## 🗺️ 路线图

- [x] **国际化 I18N**：中、英、日三语支持。
- [x] **本地模型集成**：支持通过 Ollama 调用本地大语言模型，支持火山方舟平台 (Seedance2.0)。
- [x] **深度日志**：提供更详细的 Console 日志和导演工作台 (Director Workbench) 执行记录，便于调试与回溯
- [ ] **高级视频生成**（进行中）：支持更多视频模型的首尾帧控制、多图参考生成等高级功能。
- [ ] **时间轴增强**：支持在时间轴剪辑中添加过渡动画效果。
- [ ] **工程管理**：支持工程文件的完整导出、迁移及备份。
- [ ] **自定义创作**：支持自定义提示词 (Prompt) 模板与工作流。
- [ ] **工具箱扩展**：集成更多的 AI 辅助工具。
- [ ] **多模型支持**：在 Sora、Runway、Pika、Keling、Vidu、Jimeng 等视频模型间无缝切换。
- [ ] **声音克隆**：为角色生成专属 AI 配音。

## 📄 许可证

本项目采用 MIT 许可证。

<div align="center">
<img src="https://api.star-history.com/svg?repos=SekiyoKana/sky-drama&type=Date" style="margin: 0 auto" width="600" />
</div>
