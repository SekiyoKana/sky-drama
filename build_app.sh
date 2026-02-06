#!/bin/bash
set -eo pipefail

# ==========================================
#   🚀 SKY-DRAMA BUILD SYSTEM (No-DMG Ver)
#   Target: macOS & Linux
# ==========================================

# --- 配置 ---
APP_PORT=11451
MIN_NODE_VERSION=23
MIN_PYTHON_VERSION_MAJOR=3
MIN_PYTHON_VERSION_MINOR=11

# --- 颜色 ---
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${CYAN}ℹ️  [INFO] $1${NC}"; }
log_success() { echo -e "${GREEN}✅ [SUCCESS] $1${NC}"; }
log_error() { echo -e "${RED}❌ [ERROR] $1${NC}"; exit 1; }
log_warn() { echo -e "${YELLOW}⚠️  [WARN] $1${NC}"; }

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PKG_DIR="$ROOT_DIR/pkg"

mkdir -p "$PKG_DIR"

# ==========================================
# 0. 端口清理 (防止 Address already in use)
# ==========================================
ZOMBIE_PID=$(lsof -ti :$APP_PORT || true)
if [ -n "$ZOMBIE_PID" ]; then
    log_warn "Killing zombie process $ZOMBIE_PID on port $APP_PORT..."
    kill -9 $ZOMBIE_PID
fi

# ==========================================
# 1. 环境检查
# ==========================================
if ! command -v node &> /dev/null; then log_error "Node.js not found."; fi
if command -v python3 &> /dev/null; then PY_BIN="python3"; else PY_BIN="python"; fi

# ==========================================
# 2. 后端构建
# ==========================================
log_info "Setting up Backend..."
cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    log_warn "Creating .venv..."
    $PY_BIN -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip --quiet
    if [ -f "requirements.txt" ]; then pip install -r requirements.txt; fi
else
    source .venv/bin/activate
fi

# 核心：自动补全缺失的动态库
PYINSTALLER_ARGS="--paths . --add-data app/skills:app/skills --add-data assets:assets --hidden-import sqlite3 --hidden-import passlib.handlers.bcrypt --hidden-import charset_normalizer --hidden-import _posixshmem --hidden-import multiprocessing --clean --noconfirm"

# 修复 SQLite
SQLITE_LIB=$(python -c "import _sqlite3; print(_sqlite3.__file__)")
if [ -n "$SQLITE_LIB" ]; then PYINSTALLER_ARGS="$PYINSTALLER_ARGS --add-binary $SQLITE_LIB:."; fi

# 修复 libxcb
LIBXCB_PATH=""
POSSIBLE_PATHS=("/opt/homebrew/lib/libxcb.1.dylib" "/usr/local/lib/libxcb.1.dylib" "/opt/X11/lib/libxcb.1.dylib")
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -f "$path" ]; then LIBXCB_PATH="$path"; break; fi
done
if [ -n "$LIBXCB_PATH" ]; then PYINSTALLER_ARGS="$PYINSTALLER_ARGS --add-binary $LIBXCB_PATH:."; fi

log_info "Building Backend Binary..."
rm -rf build dist backend_api.spec
pyinstaller -F -n backend_api $PYINSTALLER_ARGS entry.py

# ==========================================
# 3. Sidecar 同步
# ==========================================
log_info "Syncing Sidecar..."
OS_NAME=$(uname -s)
ARCH_NAME=$(uname -m)
HOST_TRIPLE=""
if [ "$OS_NAME" == "Darwin" ]; then
    [ "$ARCH_NAME" == "x86_64" ] && HOST_TRIPLE="x86_64-apple-darwin"
    [ "$ARCH_NAME" == "arm64" ] && HOST_TRIPLE="aarch64-apple-darwin"
fi

cd "$FRONTEND_DIR"
mkdir -p src-tauri/binaries
TARGET="$FRONTEND_DIR/src-tauri/binaries/backend_api-$HOST_TRIPLE"
cp "$BACKEND_DIR/dist/backend_api" "$TARGET"
chmod +x "$TARGET"

# ==========================================
# 4. 前端构建 (跳过 DMG 报错)
# ==========================================
log_info "Building Tauri App..."
if [ -f "pnpm-lock.yaml" ]; then CMD="pnpm"; elif [ -f "yarn.lock" ]; then CMD="yarn"; else CMD="npm run"; fi

# [核心修改] macOS 上只打 .app 包，跳过 .dmg 以避免脚本错误
if [ "$OS_NAME" == "Darwin" ]; then
    log_info "Targeting macOS .app bundle only (skipping DMG to avoid script errors)..."
    $CMD tauri build --bundles app
else
    $CMD tauri build
fi

# ==========================================
# 5. 收集产物
# ==========================================
log_info "Collecting Artifacts..."
BUNDLE_DIR="src-tauri/target/release/bundle"

if [ "$OS_NAME" == "Darwin" ]; then
    # 复制 .app 到 pkg 目录
    cp -r "$BUNDLE_DIR/macos/"*.app "$PKG_DIR/" 2>/dev/null || true
elif [ "$OS_NAME" == "Linux" ]; then
    cp "$BUNDLE_DIR/deb/"*.deb "$PKG_DIR/" 2>/dev/null || true
fi

log_success "Build Complete! App is ready in: $PKG_DIR"