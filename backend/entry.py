import sys
import os
import multiprocessing
import logging
import shutil
import time
import socket
import signal
from pathlib import Path

# 配置基础日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("entry")

def kill_port(port):
    """启动前清理端口占用 (Windows/macOS 通用)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return # 端口未被占用
        
        logger.warning(f"Port {port} occupied. Cleaning up...")
        if sys.platform == "win32":
            os.system(f"for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{port}') do taskkill /f /pid %a")
        else:
            try:
                import subprocess
                pid_bytes = subprocess.check_output(["lsof", "-ti", f":{port}"])
                pids = pid_bytes.decode().strip().split('\n')
                for pid in pids:
                    if pid:
                        os.kill(int(pid), signal.SIGKILL)
            except Exception:
                pass
        time.sleep(1)
    except Exception as e:
        logger.error(f"Kill port error: {e}")

def get_app_data_dir():
    """
    获取应用数据目录 (用于存放数据库和持久化资源)
    策略：
    - Windows: 绿色模式 (EXE同级目录/data)，方便携带。
    - macOS: 标准模式 (Application Support)，符合苹果规范。
    - Linux: 标准模式 (.local/share)。
    """
    # 1. 如果环境变量强制指定了工作目录，优先级最高 (用于开发调试或特殊部署)
    env_work_dir = os.environ.get("APP_WORK_DIR")
    if env_work_dir:
        path = Path(env_work_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # 2. 获取当前是否为打包环境
    is_frozen = getattr(sys, 'frozen', False)
    home = Path.home()

    # === Windows 绿色版逻辑 ===
    if sys.platform == "win32":
        if is_frozen:
            # 在打包环境下，sys.executable 指向实际的 .exe 文件路径
            # 我们把数据存放在 .exe 同级的 data 目录下
            exe_path = Path(sys.executable).parent
            app_data = exe_path / "data"
            # 只有当路径变化时才打印日志，避免刷屏
            if not app_data.exists():
                logger.info(f"🪟 Windows Portable Mode: Initializing data at {app_data}")
        else:
            # 开发环境，存放在项目根目录下的 data
            app_data = Path(__file__).parent / "data"
    
    # === macOS 逻辑 ===
    elif sys.platform == "darwin":
        app_data = home / "Library" / "Application Support" / "com.sekiyo.skydrama"
    
    # === Linux 逻辑 ===
    else:
        app_data = home / ".local" / "share" / "com.sekiyo.skydrama"
    
    # 创建目录
    try:
        app_data.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # 如果在 Windows C:\Program Files 下可能没有写权限，回退到 AppData
        if sys.platform == "win32":
            logger.warning("⚠️ No write permission in EXE folder, falling back to AppData")
            app_data = home / "AppData" / "Roaming" / "com.sekiyo.skydrama"
            app_data.mkdir(parents=True, exist_ok=True)
        else:
            raise

    return app_data

def sync_internal_assets(bundle_dir, app_data_dir):
    """
    将包内资源同步到外部数据目录
    目的：让程序生成的图片有地方存，且不会随程序关闭而消失
    """
    source_assets = bundle_dir / "assets"
    target_assets = app_data_dir / "assets"
    
    # 如果包里没有 assets 文件夹，直接跳过
    if not source_assets.exists():
        return

    try:
        # 情况 1: 外部 assets 文件夹完全不存在 -> 完整拷贝
        if not target_assets.exists():
            shutil.copytree(source_assets, target_assets)
            logger.info(f"✅ Assets initialized at {target_assets}")
        
        # 情况 2: 外部文件夹存在 -> 检查是否需要补全 static 资源
        # 我们只补全 static 文件夹，不覆盖根目录，以免覆盖用户生成的内容
        else:
            source_static = source_assets / "static"
            target_static = target_assets / "static"
            # 如果源包里有 static 且目标里没有，补充进去
            if source_static.exists() and not target_static.exists():
                shutil.copytree(source_static, target_static)
                logger.info(f"✅ Static assets restored")
            
    except Exception as e:
        logger.error(f"❌ Asset sync failed: {e}")

def setup_environment():
    """设置环境变量和路径"""
    if getattr(sys, 'frozen', False):
        # --- 打包环境 ---
        bundle_dir = Path(sys._MEIPASS) # PyInstaller 解压出来的临时目录 (只读资源)
        app_data_dir = get_app_data_dir() # 持久化存储目录 (Windows下是 EXE同级/data)
        
        # 1. 数据库路径
        db_path = app_data_dir / "database.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        
        # 2. 资源路径处理 (所有平台统一策略)
        # 将临时目录的 assets 同步到持久化目录，并将 ASSETS_DIR 指向持久化目录
        sync_internal_assets(bundle_dir, app_data_dir)
        
        os.environ["ASSETS_DIR"] = str(app_data_dir / "assets")
        
        if sys.platform == "darwin":
            logger.info("🍎 macOS mode: Assets synced to Application Support")
        else:
            logger.info(f"🪟 Windows mode: Assets synced to {os.environ['ASSETS_DIR']}")

        # 通用配置
        os.environ.setdefault("PROJECT_NAME", "Sky Drama")
        os.environ.setdefault("SECRET_KEY", "desktop-secret-key")

    else:
        # --- 开发环境 ---
        dev_assets = Path(__file__).parent / "assets"
        os.environ["ASSETS_DIR"] = str(dev_assets)
        
        # 开发环境数据库也放在本地 data 目录
        dev_data = Path(__file__).parent / "data"
        dev_data.mkdir(exist_ok=True)
        os.environ["DATABASE_URL"] = f"sqlite:///{dev_data}/database.db"

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    try:
        kill_port(11451)
        setup_environment()
        
        logger.info(f"💾 DATABASE: {os.environ.get('DATABASE_URL')}")
        logger.info(f"📂 ASSETS: {os.environ.get('ASSETS_DIR')}")

        import uvicorn
        from app.main import app
        
        uvicorn.run(app, host="127.0.0.1", port=11451, log_level="info")
        sys.exit(0)
        
    except Exception as e:
        # Ignore benign cancellation errors during shutdown
        if "CancelledError" in str(e) or "KeyboardInterrupt" in str(e):
             sys.exit(0)

        import traceback
        err_path = Path.home() / "skydrama_startup_error.log"
        with open(err_path, "w") as f:
            f.write(f"Startup Error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
