@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT_DIR=%%~fI"

set "BACKEND_DIR=%ROOT_DIR%\apps\backend"
set "FRONTEND_DIR=%ROOT_DIR%\apps\frontend"
set "PKG_DIR=%ROOT_DIR%\pkg"
set "MIN_NODE_MAJOR=20"
set "MIN_NODE_MINOR=12"
set "MIN_PNPM_MAJOR=9"

set "SKIP_INSTALL=%SKYDRAMA_SKIP_INSTALL%"
if "%SKIP_INSTALL%"=="" set "SKIP_INSTALL=0"

set "BUNDLES=%SKYDRAMA_TAURI_BUNDLES%"

if not exist "%PKG_DIR%" mkdir "%PKG_DIR%"

echo [INFO] Checking build prerequisites...
where python >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Missing required command: python
  goto :error
)

where node >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Missing required command: node
  goto :error
)

where cargo >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Missing required command: cargo
  echo [ERROR] Install Rust from https://rustup.rs and restart terminal.
  goto :error
)

where rustc >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Missing required command: rustc
  echo [ERROR] Install Rust from https://rustup.rs and restart terminal.
  goto :error
)

for /f "tokens=1 delims=." %%a in ('node -p "process.versions.node"') do set "NODE_MAJOR=%%a"
for /f "tokens=2 delims=." %%a in ('node -p "process.versions.node"') do set "NODE_MINOR=%%a"
for /f %%a in ('node -p "typeof require('node:crypto').hash === 'function'"') do set "HAS_CRYPTO_HASH=%%a"
if %NODE_MAJOR% lss %MIN_NODE_MAJOR% (
  echo [ERROR] Node.js >= %MIN_NODE_MAJOR%.%MIN_NODE_MINOR% is required. Current: 
  node -v
  goto :error
)
if %NODE_MAJOR% equ %MIN_NODE_MAJOR% if %NODE_MINOR% lss %MIN_NODE_MINOR% (
  echo [ERROR] Node.js >= %MIN_NODE_MAJOR%.%MIN_NODE_MINOR% is required. Current:
  node -v
  goto :error
)
if /I not "%HAS_CRYPTO_HASH%"=="true" (
  echo [ERROR] Current Node runtime does not support crypto.hash.
  node -v
  goto :error
)

if exist "%FRONTEND_DIR%\pnpm-lock.yaml" (
  where corepack >nul 2>&1
  if %errorlevel% equ 0 (
    set "PACKAGE_MANAGER=corepack-pnpm"
  ) else (
    set "PACKAGE_MANAGER=pnpm"
  )
) else if exist "%FRONTEND_DIR%\yarn.lock" (
  set "PACKAGE_MANAGER=yarn"
) else (
  set "PACKAGE_MANAGER=npm"
)

if /I "%PACKAGE_MANAGER%"=="pnpm" (
  where pnpm >nul 2>&1
  if %errorlevel% neq 0 (
    echo [ERROR] Missing required command: pnpm
    goto :error
  )
  for /f "tokens=1 delims=." %%a in ('pnpm --version') do set "PNPM_MAJOR=%%a"
  if %PNPM_MAJOR% lss %MIN_PNPM_MAJOR% (
    echo [ERROR] pnpm >= %MIN_PNPM_MAJOR% is required for pnpm-lock.yaml. Current:
    pnpm --version
    goto :error
  )
)

if /I "%PACKAGE_MANAGER%"=="yarn" (
  where yarn >nul 2>&1
  if %errorlevel% neq 0 (
    echo [ERROR] Missing required command: yarn
    goto :error
  )
)

echo [INFO] Building backend sidecar binary...
cd /d "%BACKEND_DIR%"

if not exist ".venv\Scripts\activate.bat" (
  python -m venv .venv
  if %errorlevel% neq 0 goto :error
)

call ".venv\Scripts\activate.bat"
if %errorlevel% neq 0 goto :error

if not "%SKIP_INSTALL%"=="1" (
  python -m pip install --upgrade pip
  if %errorlevel% neq 0 goto :error
  python -m pip install -r requirements.txt
  if %errorlevel% neq 0 goto :error
)

if exist build rd /s /q build
if exist dist rd /s /q dist
if exist backend_api.spec del backend_api.spec

pyinstaller -F -n backend_api --paths . ^
  --add-data "app\skills;app\skills" ^
  --add-data "assets;assets" ^
  --hidden-import sqlite3 ^
  --hidden-import passlib.handlers.bcrypt ^
  --hidden-import charset_normalizer ^
  --clean --noconfirm entry.py
if %errorlevel% neq 0 goto :error

if not exist "dist\backend_api.exe" (
  echo [ERROR] Backend binary not found.
  goto :error
)

echo [INFO] Syncing sidecar into apps/frontend/src-tauri/binaries...
cd /d "%FRONTEND_DIR%"
if not exist "src-tauri\binaries" mkdir "src-tauri\binaries"
del /q "src-tauri\binaries\backend_api-*" >nul 2>&1

if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
  set "HOST_TRIPLE=aarch64-pc-windows-msvc"
) else (
  set "HOST_TRIPLE=x86_64-pc-windows-msvc"
)

copy "%BACKEND_DIR%\dist\backend_api.exe" "src-tauri\binaries\backend_api-%HOST_TRIPLE%.exe" >nul
if %errorlevel% neq 0 goto :error

echo [INFO] Installing frontend dependencies...
if not "%SKIP_INSTALL%"=="1" (
  if /I "%PACKAGE_MANAGER%"=="corepack-pnpm" (
    call corepack enable
    if %errorlevel% neq 0 goto :error
    call corepack pnpm install --frozen-lockfile
    if %errorlevel% neq 0 goto :error
  ) else if /I "%PACKAGE_MANAGER%"=="pnpm" (
    call pnpm install --frozen-lockfile
    if %errorlevel% neq 0 goto :error
  ) else if /I "%PACKAGE_MANAGER%"=="yarn" (
    call yarn install --frozen-lockfile
    if %errorlevel% neq 0 goto :error
  ) else (
    call npm install
    if %errorlevel% neq 0 goto :error
  )
)

set "NEED_ICONS=0"
if not exist "src-tauri\icons\icon.icns" set "NEED_ICONS=1"
if not exist "src-tauri\icons\icon.ico" set "NEED_ICONS=1"

if "%NEED_ICONS%"=="1" (
  if not exist "public\logo.png" (
    echo [ERROR] Missing icon source file: apps/frontend/public/logo.png
    goto :error
  )

  echo [INFO] Missing Tauri icon files detected, generating icons from public/logo.png...
  if /I "%PACKAGE_MANAGER%"=="corepack-pnpm" (
    call corepack enable
    if %errorlevel% neq 0 goto :error
    call corepack pnpm exec tauri icon public/logo.png
    if %errorlevel% neq 0 goto :error
  ) else if /I "%PACKAGE_MANAGER%"=="pnpm" (
    call pnpm exec tauri icon public/logo.png
    if %errorlevel% neq 0 goto :error
  ) else if /I "%PACKAGE_MANAGER%"=="yarn" (
    call yarn tauri icon public/logo.png
    if %errorlevel% neq 0 goto :error
  ) else (
    call npx tauri icon public/logo.png
    if %errorlevel% neq 0 goto :error
  )
)

echo [INFO] Building desktop app with Tauri...
if /I "%PACKAGE_MANAGER%"=="corepack-pnpm" (
  call corepack enable
  if %errorlevel% neq 0 goto :error
  if "%BUNDLES%"=="" (
    call corepack pnpm exec tauri build
  ) else (
    call corepack pnpm exec tauri build --bundles "%BUNDLES%"
  )
) else if /I "%PACKAGE_MANAGER%"=="pnpm" (
  if "%BUNDLES%"=="" (
    call pnpm exec tauri build
  ) else (
    call pnpm exec tauri build --bundles "%BUNDLES%"
  )
) else if /I "%PACKAGE_MANAGER%"=="yarn" (
  if "%BUNDLES%"=="" (
    call yarn tauri build
  ) else (
    call yarn tauri build --bundles "%BUNDLES%"
  )
) else (
  if "%BUNDLES%"=="" (
    call npx tauri build
  ) else (
    call npx tauri build --bundles "%BUNDLES%"
  )
)
if %errorlevel% neq 0 goto :error

echo [INFO] Collecting artifacts...
set "BUNDLE_DIR=%FRONTEND_DIR%\src-tauri\target\release\bundle"
xcopy "%BUNDLE_DIR%\msi\*.msi" "%PKG_DIR%\" /Y /I >nul 2>&1
xcopy "%BUNDLE_DIR%\nsis\*.exe" "%PKG_DIR%\" /Y /I >nul 2>&1

echo [INFO] Desktop build completed. Artifacts: %PKG_DIR%
exit /b 0

:error
echo [ERROR] Build failed.
exit /b 1
