# Project Structure and Build Conventions

The repository now uses `apps/ + deploy/ + scripts/` layout as the default.

## Current structure

```text
sky-drama/
├── apps/
│   ├── backend/              # FastAPI service and PyInstaller entry
│   └── frontend/             # Vue + Vite + Tauri desktop shell
├── deploy/
│   └── docker/
│       ├── docker-compose.yml
│       └── .env.example
├── scripts/
│   └── desktop/
│       ├── build.sh          # macOS/Linux desktop packaging entry
│       └── build.bat         # Windows desktop packaging entry
├── docs/
└── Makefile                  # Team command entrypoint
```

## Build command policy

- Preferred command entry:
  - `make setup`
  - `make dev-backend`
  - `make dev-frontend`
  - `make docker-up`
  - `make desktop-build`
- Desktop packaging scripts:
  - macOS/Linux: `./scripts/desktop/build.sh`
  - Windows: `.\scripts\desktop\build.bat`
- CI variables:
  - `SKYDRAMA_SKIP_INSTALL=1`
  - `SKYDRAMA_TAURI_BUNDLES=app`
