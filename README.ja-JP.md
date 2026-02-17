# Sky Drama ☁️🎬

[简体中文](README.md) | [English](README.en-US.md) | **日本語**

<div align="center">

<img src="apps/frontend/public/logo.png" width="200" />

現在のバージョン: 0.1.0 Beta

**AI駆動のショートドラマ制作プラットフォーム: アイデアから完成まで**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue.js](https://img.shields.io/badge/Frontend-Vue_3-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Neumorphism](https://img.shields.io/badge/Design-Neumorphism-blue)](https://github.com/SekiyoKana/sky-drama)

</div>

> **AI is cheap, show me your story.**
>
> 大切なのは、AIの自動生成よりもあなたの発想と意図です。
>
> Sky Drama は大量生産のためのツールではなく、創作者のための AI 共同監督として設計されています。

## 📖 概要

**Sky Drama** は、ひらめきから絵コンテ脚本・動画ドラフトまでを一気通貫で支援する統合型 AI ショートドラマ制作プラットフォームです。

テキストと動画の間を埋め、脚本・ビジュアル設計・編集を Neumorphism スタイルのワークスペースに統合します。

### 主な対応
- 🐳 **Docker Compose** ワンコマンド起動
- 🍎 **macOS App** (Beta)
- 🪟 **Windows App** (Beta)
- 🌐 **多言語 UI**（中文 / English / 日本語）

---

## ✨ 主要機能と制作フロー

#### 現行バージョンは Nano Banana Pro + Sora2 API に最適化されています。今後さらに多くのモデルを追加予定です。

### 1. ローカルアカウントとプロジェクト管理
<div align="center">
   <img src="docs/01_login.gif" style="margin: 0 auto" width="600" />
</div>

### 2. グローバル API 設定
複数のプロバイダ API Key を登録し、生成エンジンを柔軟に切り替えできます。
<div align="center">
   <img src="docs/05_api_setting.gif" style="margin: 0 auto" width="600" />
</div>

#### API プラットフォーム拡張（OpenAI / Ollama / 火山引擎）

- `ApiMatrixTab` の接続追加/編集で `Platform Type` を選択可能:
  - `OpenAI Compatible`
  - `Ollama`
  - `Volcengine Ark`
- `Ollama` を選ぶと:
  - 既定 `Base URL`: `http://127.0.0.1:11434/api`
  - 既定テキスト API: `POST /chat`（フルパス `/api/chat`）
  - 接続テスト: `GET /tags`（フルパス `/api/tags`）
  - ローカル/クラウドの Ollama エンドポイントに対応
- `Volcengine` を選ぶと:
  - 既定 `Base URL`: `https://ark.cn-beijing.volces.com/api/v3`
  - 既定テキスト API: `POST /chat/completions`
  - 既定動画タスク作成 API: `POST /contents/generations/tasks`
  - 既定動画タスク取得 API: `GET /contents/generations/tasks/{task_id}`
  - Ark の OpenAI 互換方式で接続（モデルには `Endpoint ID` を指定）
  - 接続テストでモデル一覧が空でも、手動でモデル ID（例: `ep-xxxx`）を入力可能

公式ドキュメント:
- Ollama API: https://docs.ollama.com/api
- Ollama Authentication: https://docs.ollama.com/api#authentication
- 火山方舟 推論: https://www.volcengine.com/docs/82379/1541594
- 火山方舟 Chat Completions API: https://www.volcengine.com/docs/82379/1330310

#### バックエンド: プラットフォーム設定の集中管理

- プロバイダ既定値とエイリアス:
  - `apps/backend/app/core/providers/openai.py`
  - `apps/backend/app/core/providers/ollama.py`
  - `apps/backend/app/core/providers/volcengine.py`
- プロバイダ登録とルーティング:
  - `apps/backend/app/core/providers/registry.py`
- 互換レイヤー:
  - `apps/backend/app/core/provider_platform.py`

#### フロントエンド: プラットフォーム設定の集中管理

- フロントエンド側の抽象レイヤー:
  - `apps/frontend/src/platforms/openai.ts`
  - `apps/frontend/src/platforms/ollama.ts`
  - `apps/frontend/src/platforms/volcengine.ts`
- レジストリ:
  - `apps/frontend/src/platforms/registry.ts`
- `ApiMatrixTab` などはレジストリから既定値/エイリアス/エンドポイント規則を読み込み、ハードコード分岐を削減。

### 3. ビジュアルスタイルの定義
参照画像やプリセットでプロジェクト全体の画風を定義します。
<div align="center">
   <img src="docs/04_create_styles.gif" style="margin: 0 auto" width="600" />
</div>

### 4. Neumorphism ワークベンチ
一般的な定型 UI ではなく、触感のある制作向けインターフェース。
<div align="center">
   <img src="docs/02_create_story.gif" style="margin: 0 auto" width="600" />
</div>

### 5. アイデアを物語へ
短い Premise を入力すると、AI Director がアウトラインと脚本形式（台詞/動作/絵コンテ記述）に展開します。
<div align="center">
   <img src="docs/06_ai_generate_script.gif" style="margin: 0 auto" width="600" />
</div>

### 6. キャラ/シーン生成 + `@` 参照注入
キャラとシーン素材を生成し、`@` で絵コンテ生成時に参照して一貫性を向上できます。
<div align="center">
   <img src="docs/07_generate_character.gif" height="300" />  
   <img src="docs/09_@_object.gif" height="300" />
</div>

### 7. ビジュアル設定集（Storybook）
登場人物・シーンを統合して、作品設定を俯瞰できます。
<div align="center">
   <img src="docs/03_storybook.gif" style="margin: 0 auto" width="600" />
</div>

### 8. タイムライン編集
NLE タイムラインでドラッグ編集・尺調整・プレビューが可能です。
<div align="center">
   <img src="docs/08_timeline_editor.gif" style="margin: 0 auto" width="600" />
</div>

### 9. アプリ内デバッグコンソール（Beta）
フロント/バック両方のログを表示。`Ctrl` を 5 回連続で押すと表示されます。
<div align="center">
   <img src="docs/console.png" style="margin: 0 auto" width="600" />
</div>

### 10. 詳細ログと Director 実行トレース
- Director 実行ごとに `trace_id` を生成し、コンソールイベントに出力
- バックエンドは `logs/director_runs/<run_id>.json` に状態・進捗・エラー・所要時間・結果要約を保存
- 履歴/詳細 API:
  - `GET /v1/logs/director-runs`
  - `GET /v1/logs/director-runs/{run_id}`

---

## 🚀 クイックスタート

### 方法1: Docker Compose（推奨）

ローカルの Python/Node 構築なしで起動可能です。

```bash
git clone https://github.com/SekiyoKana/sky-drama.git
cd sky-drama
make docker-up
```

`http://localhost:5173` にアクセスしてください。

Docker Hub への接続が不安定な場合（例: `python:3.12-slim` 取得タイムアウト）は、先にミラー設定を作成・編集してください。

```bash
make docker-env
# deploy/docker/.env を編集
# 例:
# PYTHON_BASE_IMAGE=docker.m.daocloud.io/python:3.12-slim
# NODE_BASE_IMAGE=docker.m.daocloud.io/node:20-alpine
# NGINX_BASE_IMAGE=docker.m.daocloud.io/nginx:alpine
# 必要に応じてプロキシ:
# HTTP_PROXY=http://host.docker.internal:7890
# HTTPS_PROXY=http://host.docker.internal:7890
# NO_PROXY=localhost,127.0.0.1,backend
make docker-up
```

### 方法2: デスクトップアプリ（Beta）

[Releases](https://github.com/SekiyoKana/sky-drama/releases) から配布物を取得、または自前ビルド:

- **macOS / Linux**: `./scripts/desktop/build.sh`
- **Windows**: `.\scripts\desktop\build.bat`

### 方法3: ソース開発

#### 前提条件

- Node.js（推奨 v23、最低 v20.12+、`.nvmrc` 推奨）
- pnpm（v9、Corepack 推奨）
- Python（v3.12+）
- Rust ツールチェーン（`cargo` / `rustc`、デスクトップビルド時に必要）
- **FFmpeg（必須）**
  - ダウンロード: [FFmpeg 公式](https://ffmpeg.org/download.html)
  - `PATH` 追加後、`ffmpeg` コマンドで動作確認

#### セットアップ

1. リポジトリ取得
```bash
git clone https://github.com/SekiyoKana/sky-drama.git
cd sky-drama
nvm use || nvm install
corepack enable
```

2. バックエンド
```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --host 127.0.0.1 --port 11451 --reload
```

3. フロントエンド
```bash
cd apps/frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

### 方法4: Makefile ベース運用（チーム推奨）

ルート `Makefile` で日常作業を統一できます。

```bash
# 依存関係の一括インストール（backend + frontend）
make setup

# ローカル開発
make dev-backend
make dev-frontend

# Docker 起動
make docker-up

# デスクトップビルド（macOS/Linux）
make desktop-build
```

デスクトップビルド用の環境変数:
- `SKYDRAMA_SKIP_INSTALL=1`: 依存インストールをスキップ（CI キャッシュ向け）
- `SKYDRAMA_TAURI_BUNDLES=app`: Tauri の bundle タイプを指定

構成ガイド: `docs/project-structure.md`

---

## 🛠 技術スタック

### フロントエンド
- Framework: Vue 3 (Composition API)
- Build: Vite
- Styling: TailwindCSS + カスタム Neumorphism
- State: Pinia
- Router: Vue Router

### バックエンド
- Framework: FastAPI (Python 3.12+)
- Database: SQLAlchemy（デフォルト SQLite）
- AI Integration: モジュール化 Skills アーキテクチャ
- Validation: Pydantic

## ⚠️ 注意事項

1. **FFmpeg 依存**
動画処理に FFmpeg が必須です。未導入の場合、動画生成は失敗します。

2. **動画モデル対応**
現状は **Sora 2** に最適化。Runway/Pika など他モデルは今後順次対応します。

3. **カスタム API アダプタ**
標準は `/videos`（作成）と `/videos/{task_id}`（取得）前提です。
別仕様のプロバイダを使う場合は Formatter を実装してください。

- 参考: `apps/backend/app/utils/sora_api/yi.py`
- 追加例:

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

## 🗺️ ロードマップ

- [x] **i18n**: 中文 / English / 日本語
- [x] **ローカルモデル連携**: Ollama + Volcengine Ark (Seedance2.0)
- [·] **高度な動画生成**: 先頭/末尾フレーム制御・複数画像参照の拡張
- [ ] **タイムライン強化**: トランジションアニメーション対応
- [x] **詳細ログ**: Console ログと Director Workbench 実行記録の強化
- [ ] **プロジェクト管理**: 完全エクスポート/移行/バックアップ
- [ ] **カスタム制作**: Prompt テンプレートとワークフロー
- [ ] **ツール拡張**: 追加 AI 補助ツール
- [ ] **マルチモデル対応**: Sora/Runway/Pika/Keling/Vidu/Jimeng のシームレス切替
- [ ] **音声クローン**: キャラクター専用 AI ボイス

## 📄 ライセンス

本プロジェクトは MIT ライセンスです。

<div align="center">
<img src="https://api.star-history.com/svg?repos=SekiyoKana/sky-drama&type=Date" style="margin: 0 auto" width="600" />
</div>
