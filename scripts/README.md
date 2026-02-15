# Scripts Directory

All executable project scripts are centralized here to avoid duplicated logic at
repository root.

## Desktop packaging

- macOS/Linux: `./scripts/desktop/build.sh`
- Windows: `.\scripts\desktop\build.bat`
- Requires Node.js >= 20.12 and pnpm >= 9 (or Corepack). Recommended: Node 23 (`nvm use 23`).
- Requires Rust toolchain (`cargo` and `rustc`) for Tauri desktop packaging.
- If `src-tauri/icons/icon.icns` or `icon.ico` is missing, scripts auto-generate icons from `apps/frontend/public/logo.png`.

## CI environment variables

- `SKYDRAMA_SKIP_INSTALL=1` to skip dependency install steps.
- `SKYDRAMA_TAURI_BUNDLES=app` to control tauri bundle types.
