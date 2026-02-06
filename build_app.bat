@echo off
setlocal enabledelayedexpansion

:: ==========================================
::   SKY-DRAMA BUILD SCRIPT (Universal Fix)
::   Supports: x86_64 AND aarch64 (ARM)
:: ==========================================

echo [INFO] Initializing...

set "ROOT_DIR=%cd%"
set "BACKEND_DIR=%ROOT_DIR%\backend"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "PKG_DIR=%ROOT_DIR%\pkg"

if not exist "%PKG_DIR%" mkdir "%PKG_DIR%"

:: --- 1. Environment Check ---
echo [INFO] Checking Python Environment...

python -c "import sys; print(sys.version)" | findstr /i "anaconda conda" >nul
if %errorlevel% equ 0 (
    echo.
    echo [ERROR] DETECTED CONDA ENVIRONMENT!
    echo [ERROR] Please use a clean Python venv.
    goto :error
)

if exist "%BACKEND_DIR%\.venv\Scripts\activate.bat" (
    echo [INFO] Found .venv, activating...
    call "%BACKEND_DIR%\.venv\Scripts\activate.bat"
)

:: --- 2. Build Backend (PyInstaller) ---
echo [INFO] Building Backend...
cd /d "%BACKEND_DIR%"

if exist build rd /s /q build
if exist dist rd /s /q dist
if exist backend_api.spec del backend_api.spec

if not exist "entry.py" (
    echo [ERROR] Cannot find entry.py!
    goto :error
)

echo [INFO] Running PyInstaller...
pyinstaller -F -w -n backend_api --paths . ^
 --add-data "app\skills;app\skills" ^
 --add-data "assets;assets" ^
 --hidden-import passlib.handlers.bcrypt ^
 entry.py --clean --noconfirm

if %errorlevel% neq 0 goto :error
if not exist "dist\backend_api.exe" goto :error

echo [INFO] Backend binary created.

:: --- 3. Prepare Sidecar (Universal) ---
echo [INFO] Preparing Sidecar...
cd /d "%FRONTEND_DIR%"

if not exist "src-tauri\binaries" mkdir "src-tauri\binaries"
del /q "src-tauri\binaries\*"

:: 关键修改：同时复制为 x86_64 和 aarch64 两种名称
:: 这样无论系统判定是 Intel 还是 ARM，都能找到对应的文件

set "SIDE_X64=backend_api-x86_64-pc-windows-msvc.exe"
set "SIDE_ARM=backend_api-aarch64-pc-windows-msvc.exe"

echo [INFO] Creating x86_64 Sidecar...
copy "%BACKEND_DIR%\dist\backend_api.exe" "src-tauri\binaries\%SIDE_X64%" >nul

echo [INFO] Creating aarch64 Sidecar (Compatibility Mode)...
copy "%BACKEND_DIR%\dist\backend_api.exe" "src-tauri\binaries\%SIDE_ARM%" >nul

:: --- 4. Build Tauri ---
echo [INFO] Building Tauri App...

where pnpm >nul 2>&1
if %errorlevel% equ 0 ( set "CMD=pnpm" ) else ( set "CMD=npm run" )

echo [INFO] Using package manager: %CMD%
call %CMD% tauri build

if %errorlevel% neq 0 (
    echo [ERROR] Tauri build failed!
    goto :error
)

:: --- 5. Collect Artifacts ---
echo [INFO] Collecting artifacts...
set "BUNDLE_DIR=src-tauri\target\release\bundle"

xcopy "%BUNDLE_DIR%\msi\*.msi" "%PKG_DIR%\" /Y /S /I >nul 2>&1
xcopy "%BUNDLE_DIR%\nsis\*.exe" "%PKG_DIR%\" /Y /S /I >nul 2>&1

echo.
echo [SUCCESS] Build Complete! Check folder: %PKG_DIR%
echo.
pause
exit /b 0

:error
echo [FAIL] Error occurred.
pause
exit /b 1