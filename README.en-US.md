# Sky Drama ☁️🎬

[简体中文](README.md) | **English** | [日本語](README.ja-JP.md)

<div align="center">

<img src="apps/frontend/public/logo.png" width="200" />

Current Version: 0.1.0 Beta

**An AI-powered short-drama creation platform: from idea to cut**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue.js](https://img.shields.io/badge/Frontend-Vue_3-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Neumorphism](https://img.shields.io/badge/Design-Neumorphism-blue)](https://github.com/SekiyoKana/sky-drama)

</div>

> **AI is cheap, show me your story.**
>
> Your creativity and intent matter more than auto-generated output.
>
> Sky Drama is designed as an AI co-director for creators, not a low-quality content pipeline.

## 📖 Overview

**Sky Drama** is an integrated AI short-drama platform that helps you move from a rough spark to storyboard scripts and video drafts in one workflow.

It bridges the gap between text and video and combines writing, visual design, and editing into one smooth Neumorphism-style workspace.

### Core Support
- 🐳 **Docker Compose** one-command deployment
- 🍎 **macOS App** (Beta)
- 🪟 **Windows App** (Beta)
- 🌐 **Multilingual UI** (Chinese / English / Japanese)
- ✍️ **Novel Mode** (In Development)

---

## ✨ Features & Workflow

#### Current release is heavily optimized for Nano Banana Pro + Sora2 API. More models will be added in later versions.

### 1. Local Account System & Project Management
<div align="center">
   <img src="docs/01_login.gif" style="margin: 0 auto" width="600" />
</div>

### 2. Global API Configuration
Configure multiple providers and switch generation engines flexibly.
<div align="center">
   <img src="docs/05_api_setting.gif" style="margin: 0 auto" width="600" />
</div>

#### API Platform Extensions (OpenAI / Ollama / Volcengine)

- `ApiMatrixTab` now uses a `Platform Type` dropdown with:
  - `OpenAI Compatible`
  - `Ollama`
  - `Volcengine Ark`
- When `Ollama` is selected:
  - Default `Base URL`: `http://127.0.0.1:11434/api`
  - Default text endpoint: `POST /chat` (full path `/api/chat`)
  - Connection test uses `GET /tags` (full path `/api/tags`)
  - Supports local and cloud-hosted Ollama endpoints
- When `Volcengine` is selected:
  - Default `Base URL`: `https://ark.cn-beijing.volces.com/api/v3`
  - Default text endpoint: `POST /chat/completions`
  - Default video task create endpoint: `POST /contents/generations/tasks`
  - Default video task fetch endpoint: `GET /contents/generations/tasks/{task_id}`
  - Uses Ark OpenAI-compatible access mode; use your `Endpoint ID` as model
  - If model list is empty in test connection, you can still input model ID manually (for example `ep-xxxx`)

Official references:
- Ollama API: https://docs.ollama.com/api
- Ollama Authentication: https://docs.ollama.com/api#authentication
- Volcengine Ark Inference: https://www.volcengine.com/docs/82379/1541594
- Volcengine Ark Chat Completions API: https://www.volcengine.com/docs/82379/1330310

#### Backend Platform Config Centralization

- Provider defaults and aliases are centralized in:
  - `apps/backend/app/core/providers/openai.py`
  - `apps/backend/app/core/providers/ollama.py`
  - `apps/backend/app/core/providers/volcengine.py`
- Provider registry and routing:
  - `apps/backend/app/core/providers/registry.py`
- Compatibility layer:
  - `apps/backend/app/core/provider_platform.py`

#### Frontend Platform Config Centralization

- Frontend platform abstractions:
  - `apps/frontend/src/platforms/openai.ts`
  - `apps/frontend/src/platforms/ollama.ts`
  - `apps/frontend/src/platforms/volcengine.ts`
- Frontend registry:
  - `apps/frontend/src/platforms/registry.ts`
- Components like `ApiMatrixTab` read defaults/aliases/endpoints from registry to avoid scattered hard-coded logic.

### 3. Define Your Visual Style
Upload references or use presets to set your project's visual direction.
<div align="center">
   <img src="docs/04_create_styles.gif" style="margin: 0 auto" width="600" />
</div>

### 4. Neumorphism Workbench Design
A tactile and expressive workspace instead of a generic production dashboard.
<div align="center">
   <img src="docs/02_create_story.gif" style="margin: 0 auto" width="600" />
</div>

### 5. Turn Ideas Into Story
Input a brief premise, and the AI Director expands it into outline + screenplay format with dialogue, action notes, and storyboard descriptions.
<div align="center">
   <img src="docs/06_ai_generate_script.gif" style="margin: 0 auto" width="600" />
</div>

### 6. Character & Scene Generation with `@` Reference Injection
Generate character and scene assets and inject them into storyboard prompts with `@` for consistency.
<div align="center">
   <img src="docs/07_generate_character.gif" height="300" />  
   <img src="docs/09_@_object.gif" height="300" />
</div>

### 7. Visual Storybook
Build a global visual bible for characters and scenes.
<div align="center">
   <img src="docs/03_storybook.gif" style="margin: 0 auto" width="600" />
</div>

### 8. Timeline Editing
Built-in NLE timeline for drag-and-drop editing, duration adjustments, and live preview.
<div align="center">
   <img src="docs/08_timeline_editor.gif" style="margin: 0 auto" width="600" />
</div>

### 9. In-App Debug Console (Beta)
Includes frontend and backend logs. Activate with 5 quick `Ctrl` presses.
<div align="center">
   <img src="docs/console.png" style="margin: 0 auto" width="600" />
</div>

### 10. Deep Logs & Director Run Traceback
- Every Director run generates a `trace_id` and streams it to console events.
- Backend persists run logs into `logs/director_runs/<run_id>.json` with statuses, progress, errors, elapsed time, and output summary.
- APIs for history/details:
  - `GET /v1/logs/director-runs`
  - `GET /v1/logs/director-runs/{run_id}`

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Run directly without setting up local Python/Node environments:

```bash
git clone https://github.com/SekiyoKana/sky-drama.git
cd sky-drama
make docker-up
```

Open `http://localhost:5173`.

If Docker Hub access is unstable in your network (for example timeout on `python:3.12-slim`), generate and edit mirror config first:

```bash
make docker-env
# Edit deploy/docker/.env
# Example:
# PYTHON_BASE_IMAGE=docker.m.daocloud.io/python:3.12-slim
# NODE_BASE_IMAGE=docker.m.daocloud.io/node:20-alpine
# NGINX_BASE_IMAGE=docker.m.daocloud.io/nginx:alpine
# Optional proxy:
# HTTP_PROXY=http://host.docker.internal:7890
# HTTPS_PROXY=http://host.docker.internal:7890
# NO_PROXY=localhost,127.0.0.1,backend
make docker-up
```

### Option 2: Desktop App (Beta)

Download installers from [Releases](https://github.com/SekiyoKana/sky-drama/releases), or build locally:

- **macOS / Linux**: `./scripts/desktop/build.sh`
- **Windows**: `.\scripts\desktop\build.bat`

### Option 3: Source Development

#### Prerequisites

- Node.js (recommended v23, minimum v20.12+, use `.nvmrc`)
- pnpm (v9, recommended via Corepack)
- Python (v3.12+)
- Rust toolchain (`cargo` / `rustc`, required for desktop builds)
- **FFmpeg (required)**
  - Download: [FFmpeg official](https://ffmpeg.org/download.html)
  - Add to `PATH` and verify with `ffmpeg` command

#### Setup

1. Clone repository
```bash
git clone https://github.com/SekiyoKana/sky-drama.git
cd sky-drama
nvm use || nvm install
corepack enable
```

2. Backend
```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --host 127.0.0.1 --port 11451 --reload
```

3. Frontend
```bash
cd apps/frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

### Option 4: Team-Friendly Make Commands

Use the root `Makefile` for daily workflows:

```bash
# Install dependencies (backend + frontend)
make setup

# Local development
make dev-backend
make dev-frontend

# Docker deployment
make docker-up

# Desktop build (macOS/Linux)
make desktop-build
```

Desktop build environment variables:
- `SKYDRAMA_SKIP_INSTALL=1`: skip dependency installation (useful for CI cache-hit runs)
- `SKYDRAMA_TAURI_BUNDLES=app`: customize Tauri bundle targets

Project structure guide: `docs/project-structure.md`

---

## 🛠 Tech Stack

### Frontend
- Framework: Vue 3 (Composition API)
- Build: Vite
- Styling: TailwindCSS + custom Neumorphism design
- State: Pinia
- Routing: Vue Router

### Backend
- Framework: FastAPI (Python 3.12+)
- Database: SQLAlchemy (SQLite by default)
- AI integration: modular Skills architecture
- Validation: Pydantic

## ⚠️ Notes

1. **FFmpeg Dependency**
This project depends on FFmpeg for video processing. Without FFmpeg, video generation will fail.

2. **Video Model Support**
Current video workflow is deeply tuned for **Sora 2**. More providers/models (Runway, Pika, etc.) will be added later.

3. **Custom API Adapter**
Default Sora 2 flow assumes `/videos` (create) and `/videos/{task_id}` (fetch).
If your provider uses a different protocol, implement a formatter adapter.

- Example: `apps/backend/app/utils/sora_api/yi.py`
- Add your own provider formatter in `apps/backend/app/utils/sora_api/`:

```python
# apps/backend/app/utils/sora_api/my_provider.py
from .base import Base
from typing import List, Any, Dict

class MyProvider(Base):
    name = "MyProvider"
    base_url_keyword = "api.myprovider.com"

    def create(self, base_url: str, apikey: str, model: str, prompt: str, seconds: int, size: str, watermark: bool, images: List[Any]) -> str:
        self.set_auth(base_url, apikey)
        return "task_123456"

    def _query_status(self, task_id: str) -> Dict[str, Any]:
        return {
            "status": "completed",
            "video_url": "https://...",
            "progress": 100,
            "fail_reason": None,
        }
```

## 🗺️ Roadmap

- [x] **i18n**: Chinese / English / Japanese
- [x] **Local model integration**: Ollama + Volcengine Ark (Seedance2.0)
- [x] **Deep logs**: richer console logs + Director Workbench run records
- [ ] **Advanced video generation** (in progress): first/last-frame control and richer multi-image references
- [ ] **Timeline enhancements**: transition animations on timeline tracks
- [ ] **Project management**: full project export/migration/backup
- [ ] **Custom creation**: custom prompt templates and workflows
- [ ] **Toolbox expansion**: more AI assistant tools
- [ ] **Multi-model support**: seamless switching among Sora/Runway/Pika/Keling/Vidu/Jimeng
- [ ] **Voice cloning**: character-specific AI dubbing

## 📄 License

This project is released under the MIT License.

<div align="center">
<img src="https://api.star-history.com/svg?repos=SekiyoKana/sky-drama&type=Date" style="margin: 0 auto" width="600" />
</div>
