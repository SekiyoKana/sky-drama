import sys
import os
import io
import signal
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# 1. 设置标准输出编码 (保留，防止中文乱码)
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

# ---------------------------------------------------------
# ❌ 删除：所有 [Init] 代码 (设置 CWD, Database Path, SQLite)
# 这些工作现在全权由 entry.py 负责，main.py 不应再插手。
# ---------------------------------------------------------

# 2. 正常导入业务模块
# 此时 os.environ["DATABASE_URL"] 已经被 entry.py 设置为正确的可写路径了
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.core.ws_logger import manager
from app.core.logger import setup_logging, get_log_dir
from app.api.v1.endpoints import auth, projects, ai, apikeys, prompts, tags, users, style, logs

# 初始化日志 (Loguru)
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Life] Checking database schema...")
    try:
        # 使用 entry.py 注入的数据库路径创建表
        Base.metadata.create_all(bind=engine)
        logger.info("[Life] Database schema check completed.")
    except Exception as e:
        logger.error(f"[Life] [ERR] Database schema creation failed: {e}")
    
    # 清理孤儿资源
    try:
        from app.utils.asset_cleaner import clean_orphan_assets
        clean_orphan_assets()
    except Exception as e:
        logger.warning(f"[Life] Asset cleaner failed: {e}")

    yield
    logger.info("[Life] Application shutdown.")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# --- Assets 挂载 ---
# 使用 settings 读取环境变量 (entry.py 已经设置了 ASSETS_DIR)
assets_dir = settings.ASSETS_DIR 

# 增加容错：如果目录不存在，尝试创建（在 Application Support 下是允许创建的）
if not os.path.exists(assets_dir):
    try:
        os.makedirs(assets_dir, exist_ok=True)
        logger.info(f"[Assets] Created directory: {assets_dir}")
    except Exception as e:
        logger.error(f"[Assets] [ERR] Failed to create dir: {e}")

if os.path.exists(assets_dir):
    try:
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        logger.info(f"[Assets] Mounted /assets to: {assets_dir}")
    except Exception as e:
        logger.error(f"[Assets] [ERR] Mount failed: {e}")
else:
    logger.warning(f"[Assets] Directory missing: {assets_dir}. Static files disabled.")

# --- Logs 挂载 ---
log_dir = get_log_dir()
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir, exist_ok=True)
        logger.info(f"[Logs] Created directory: {log_dir}")
    except Exception as e:
        logger.error(f"[Logs] [ERR] Failed to create dir: {e}")

if os.path.exists(log_dir):
    try:
        app.mount("/logs", StaticFiles(directory=log_dir), name="logs")
        logger.info(f"[Logs] Mounted /logs to: {log_dir}")
    except Exception as e:
        logger.error(f"[Logs] [ERR] Mount failed: {e}")

# --- CORS 配置 ---
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 路由注册 ---
app.include_router(auth.router, prefix="/v1/login", tags=["auth_legacy"])
app.include_router(projects.router, prefix="/v1/projects", tags=["projects_legacy"])
app.include_router(ai.router, prefix="/v1/ai", tags=["ai_legacy"])
app.include_router(apikeys.router, prefix="/v1/apikeys", tags=["apikeys_legacy"])
app.include_router(prompts.router, prefix="/v1/prompts", tags=["prompts_legacy"])
app.include_router(tags.router, prefix="/v1/tags", tags=["tags_legacy"])
app.include_router(style.router, prefix="/v1/styles", tags=["styles"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(logs.router, prefix="/v1/logs", tags=["logs"])

# --- 中间件 ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 过滤掉日志轮询，防止刷屏
    if "/logs/latest" in request.url.path or "/ws/logs" in request.url.path:
        return await call_next(request)
    # logger.info(f"-> {request.method} {request.url.path}") 
    response = await call_next(request)
    return response

# --- WebSocket ---
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_text("[Backend] Log Stream Connected")
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# --- 优雅退出 ---
@app.get("/shutdown")
def shutdown_server():
    logger.info("Shutdown request received. Exiting...")
    def kill():
        pid = os.getpid()
        if sys.platform == "win32":
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGINT)
    threading.Timer(0.5, kill).start()
    return {"status": "shutting down"}

# --- 全局异常 ---
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_msg = f"[Internal Server Error] {str(exc)}"
    logger.error(error_msg)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

@app.get("/")
def root():
    return {"message": "Welcome to AI Drama Platform API", "status": "running"}