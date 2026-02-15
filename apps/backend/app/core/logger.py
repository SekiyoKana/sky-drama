import sys
import os
import asyncio
import platform
import logging
import logging.handlers
import tempfile
from app.core.ws_logger import manager

# Helper to get a writable logs directory
def get_log_dir():
    base = None
    
    # 1. First Priority: Check environment variable from Tauri / Entry
    # 这是最理想的情况，由 entry.py 或 lib.rs 传入绝对路径
    app_work_dir = os.environ.get("APP_WORK_DIR")
    if app_work_dir:
        base = os.path.join(app_work_dir, "logs")
    
    # 2. Second Priority: Frozen (PyInstaller) paths fallback
    elif getattr(sys, 'frozen', False):
        if platform.system() == 'Windows':
            exe_dir = os.path.dirname(sys.executable)
            base = os.path.join(exe_dir, 'logs')
        elif platform.system() == 'Darwin':
            # macOS 必须遵守沙盒/签名规范，通常写在 Library/Logs
            base = os.path.expanduser("~/Library/Logs/SkyDrama")
        else:
            # Linux 等其他系统，尝试写在程序目录或 local share
            base = os.path.join(os.path.dirname(sys.executable), 'logs')
    
    # 3. Third Priority: Development mode
    else:
        # 开发模式：使用当前目录下的 logs
        base = os.path.abspath("logs")
    
    if not os.path.exists(base):
        try:
            os.makedirs(base, exist_ok=True)
            # 这里的 print 在 PyInstaller w 模式下可能看不见，但如果有控制台就能看到
            sys.stderr.write(f"[Logger] Created log directory at: {base}\n")
        except Exception as e:
            sys.stderr.write(f"⚠️ Failed to create log dir at {base}: {e}\n")
            # Fallback to temp directory if permission denied (最后一道防线)
            base = os.path.join(tempfile.gettempdir(), "SkyDrama", "logs")
            try:
                os.makedirs(base, exist_ok=True)
                sys.stderr.write(f"✅ Fallback log dir created at {base}\n")
            except Exception as e2:
                sys.stderr.write(f"❌ Failed to create fallback log dir: {e2}\n")
    
    return base

class PollingFilter(logging.Filter):
    def filter(self, record):
        return "/v1/logs/latest" not in record.getMessage()

class WebSocketHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.INFO:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast("LOG_UPDATE"))
            except RuntimeError:
                pass
            except Exception:
                pass

def setup_logging():
    log_dir = get_log_dir()
    log_file = os.path.join(log_dir, "app.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    root_logger.handlers = []

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(PollingFilter())
    root_logger.addHandler(console_handler)

    try:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(PollingFilter())
        root_logger.addHandler(file_handler)
    except Exception as e:
        # 防止文件权限问题导致整个应用启动失败
        sys.stderr.write(f"❌ Could not setup file logging: {e}\n")

    ws_handler = WebSocketHandler()
    ws_handler.setLevel(logging.INFO)
    root_logger.addHandler(ws_handler)
    
    for log_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        log_instance = logging.getLogger(log_name)
        log_instance.handlers = []
        log_instance.propagate = True
    
    logging.getLogger("uvicorn.access").addFilter(PollingFilter())
    
    return root_logger

# Initialize logger
logger = setup_logging()

# Export for compatibility
log = logger
