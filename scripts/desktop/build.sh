#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
BACKEND_DIR="$ROOT_DIR/apps/backend"
FRONTEND_DIR="$ROOT_DIR/apps/frontend"
PKG_DIR="${PKG_DIR:-$ROOT_DIR/pkg}"
MIN_NODE_MAJOR=20
MIN_NODE_MINOR=12
MIN_PNPM_MAJOR=9

SKIP_INSTALL=${SKYDRAMA_SKIP_INSTALL:-0}
BUNDLES=${SKYDRAMA_TAURI_BUNDLES:-}

info() {
  printf '[INFO] %s\n' "$1"
}

error() {
  printf '[ERROR] %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  local cmd=$1
  if ! command -v "$cmd" >/dev/null 2>&1; then
    error "Missing required command: $cmd"
  fi
}

check_rust_toolchain() {
  if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
    if [ -f "$HOME/.cargo/env" ]; then
      source "$HOME/.cargo/env"
    fi
  fi

  if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
    error "Rust toolchain is required for desktop build. Install Rust and ensure cargo/rustc are in PATH."
  fi
}

node_major() {
  node -p "parseInt(process.versions.node.split('.')[0], 10)"
}

check_node_version() {
  local major minor has_crypto_hash
  major=$(node_major)
  minor=$(node -p "parseInt(process.versions.node.split('.')[1], 10)")
  has_crypto_hash=$(node -p "typeof require('node:crypto').hash === 'function'")

  if [ "$major" -lt "$MIN_NODE_MAJOR" ] || \
     { [ "$major" -eq "$MIN_NODE_MAJOR" ] && [ "$minor" -lt "$MIN_NODE_MINOR" ]; } || \
     [ "$has_crypto_hash" != "true" ]; then
    error "Node.js >= $MIN_NODE_MAJOR.$MIN_NODE_MINOR is required (crypto.hash needed). Current: $(node -v)"
  fi
}

check_pnpm_version() {
  local major
  major=$(pnpm --version | cut -d. -f1)
  if [ "$major" -lt "$MIN_PNPM_MAJOR" ]; then
    error "pnpm >= $MIN_PNPM_MAJOR is required for pnpm-lock.yaml. Current: $(pnpm --version)"
  fi
}

detect_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi

  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi

  error "Python is not installed."
}

detect_target_triple() {
  local os_name arch_name
  os_name=$(uname -s)
  arch_name=$(uname -m)

  case "${os_name}:${arch_name}" in
    Darwin:x86_64) echo "x86_64-apple-darwin" ;;
    Darwin:arm64) echo "aarch64-apple-darwin" ;;
    Linux:x86_64) echo "x86_64-unknown-linux-gnu" ;;
    Linux:aarch64|Linux:arm64) echo "aarch64-unknown-linux-gnu" ;;
    *)
      error "Unsupported platform for sidecar build: ${os_name}/${arch_name}"
      ;;
  esac
}

install_frontend_deps() {
  local package_manager=$1
  case "$package_manager" in
    corepack-pnpm)
      corepack enable
      corepack pnpm install --frozen-lockfile
      ;;
    pnpm)
      pnpm install --frozen-lockfile
      ;;
    yarn)
      yarn install --frozen-lockfile
      ;;
    npm)
      npm install
      ;;
    *)
      error "Unsupported package manager: $package_manager"
      ;;
  esac
}

run_tauri_build() {
  local package_manager=$1
  shift
  local tauri_args=("$@")

  case "$package_manager" in
    corepack-pnpm)
      corepack enable
      corepack pnpm exec tauri build "${tauri_args[@]}"
      ;;
    pnpm)
      pnpm exec tauri build "${tauri_args[@]}"
      ;;
    yarn)
      yarn tauri build "${tauri_args[@]}"
      ;;
    npm)
      npx tauri build "${tauri_args[@]}"
      ;;
    *)
      error "Unsupported package manager: $package_manager"
      ;;
  esac
}

run_tauri_icon() {
  local package_manager=$1
  local source_icon=$2

  case "$package_manager" in
    corepack-pnpm)
      corepack enable
      corepack pnpm exec tauri icon "$source_icon"
      ;;
    pnpm)
      pnpm exec tauri icon "$source_icon"
      ;;
    yarn)
      yarn tauri icon "$source_icon"
      ;;
    npm)
      npx tauri icon "$source_icon"
      ;;
    *)
      error "Unsupported package manager: $package_manager"
      ;;
  esac
}

ensure_tauri_icons() {
  local package_manager=$1
  local icon_dir="$FRONTEND_DIR/src-tauri/icons"
  local source_icon="$FRONTEND_DIR/public/logo.png"

  if [ -f "$icon_dir/icon.icns" ] && [ -f "$icon_dir/icon.ico" ]; then
    return
  fi

  if [ ! -f "$source_icon" ]; then
    error "Missing icon source file: apps/frontend/public/logo.png"
  fi

  info "Missing Tauri icon files detected, generating icons from public/logo.png..."
  run_tauri_icon "$package_manager" "public/logo.png"
}

copy_artifacts() {
  local bundle_dir="$FRONTEND_DIR/src-tauri/target/release/bundle"
  local copied=0

  mkdir -p "$PKG_DIR"

  for artifact in \
    "$bundle_dir"/macos/*.app \
    "$bundle_dir"/dmg/*.dmg \
    "$bundle_dir"/deb/*.deb \
    "$bundle_dir"/appimage/*.AppImage \
    "$bundle_dir"/rpm/*.rpm \
    "$bundle_dir"/msi/*.msi \
    "$bundle_dir"/nsis/*.exe
  do
    if [ -e "$artifact" ]; then
      cp -R "$artifact" "$PKG_DIR/"
      copied=1
    fi
  done

  if [ "$copied" -eq 0 ]; then
    info "No bundle artifacts found in $bundle_dir"
    return
  fi

  info "Artifacts copied to $PKG_DIR:"
  ls -1 "$PKG_DIR"
}

main() {
  local os_name package_manager python_bin target_triple
  local -a tauri_args

  os_name=$(uname -s)
  python_bin=$(detect_python)

  require_cmd "$python_bin"
  require_cmd node
  check_node_version
  check_rust_toolchain

  if [ -f "$FRONTEND_DIR/pnpm-lock.yaml" ]; then
    if command -v corepack >/dev/null 2>&1; then
      package_manager="corepack-pnpm"
    else
      require_cmd pnpm
      check_pnpm_version
      package_manager="pnpm"
    fi
  elif [ -f "$FRONTEND_DIR/yarn.lock" ]; then
    require_cmd yarn
    package_manager="yarn"
  else
    require_cmd npm
    package_manager="npm"
  fi

  if [ ! -f "$BACKEND_DIR/entry.py" ]; then
    error "apps/backend/entry.py not found."
  fi

  if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
    error "apps/backend/requirements.txt not found."
  fi

  info "Building backend sidecar binary..."
  cd "$BACKEND_DIR"

  if [ ! -d ".venv" ]; then
    "$python_bin" -m venv .venv
  fi

  source .venv/bin/activate

  if [ "$SKIP_INSTALL" != "1" ]; then
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
  fi

  rm -rf build dist backend_api.spec

  pyinstaller_args=(
    -F
    -n backend_api
    --paths .
    --add-data "app/skills:app/skills"
    --add-data "assets:assets"
    --hidden-import sqlite3
    --hidden-import passlib.handlers.bcrypt
    --hidden-import charset_normalizer
    --hidden-import _posixshmem
    --hidden-import multiprocessing
    --clean
    --noconfirm
  )

  sqlite_lib=$(python -c "import _sqlite3; print(_sqlite3.__file__)")
  if [ -n "$sqlite_lib" ]; then
    pyinstaller_args+=(--add-binary "$sqlite_lib:.")
  fi

  for path in \
    /opt/homebrew/lib/libxcb.1.dylib \
    /usr/local/lib/libxcb.1.dylib \
    /opt/X11/lib/libxcb.1.dylib
  do
    if [ -f "$path" ]; then
      pyinstaller_args+=(--add-binary "$path:.")
      break
    fi
  done

  pyinstaller "${pyinstaller_args[@]}" entry.py
  deactivate

  info "Syncing sidecar into apps/frontend/src-tauri/binaries..."
  target_triple=$(detect_target_triple)
  mkdir -p "$FRONTEND_DIR/src-tauri/binaries"
  rm -f "$FRONTEND_DIR"/src-tauri/binaries/backend_api-*
  cp "$BACKEND_DIR/dist/backend_api" \
    "$FRONTEND_DIR/src-tauri/binaries/backend_api-$target_triple"
  chmod +x "$FRONTEND_DIR/src-tauri/binaries/backend_api-$target_triple"

  info "Building desktop app with Tauri..."
  cd "$FRONTEND_DIR"

  if [ "$SKIP_INSTALL" != "1" ]; then
    install_frontend_deps "$package_manager"
  fi

  ensure_tauri_icons "$package_manager"

  tauri_args=()
  if [ -n "$BUNDLES" ]; then
    tauri_args+=(--bundles "$BUNDLES")
  elif [ "$os_name" = "Darwin" ]; then
    # Keep default macOS build lean to avoid DMG issues on local machines.
    tauri_args+=(--bundles app)
  fi

  run_tauri_build "$package_manager" "${tauri_args[@]}"
  copy_artifacts
  info "Desktop build completed."
}

main "$@"
