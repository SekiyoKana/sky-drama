import sys
import os
import io
import signal
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
    app_work_dir = os.environ.get("APP_WORK_DIR")
    if app_work_dir:
        load_dotenv(Path(app_work_dir) / ".env", override=False)
except Exception:
    pass

from app.utils.http_client import init_network_env
init_network_env()

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
        Base.metadata.create_all(bind=engine)
        logger.info("[Life] Database schema check completed.")
    except Exception as e:
        logger.error(f"[Life] [ERR] Database schema creation failed: {e}")
    
    try:
        from app.utils.asset_cleaner import clean_orphan_assets
        clean_orphan_assets()
    except Exception as e:
        logger.warning(f"[Life] Asset cleaner failed: {e}")

    yield
    logger.info("[Life] Application shutdown.")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
assets_dir = settings.ASSETS_DIR 

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

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/v1/login", tags=["auth_legacy"])
app.include_router(projects.router, prefix="/v1/projects", tags=["projects_legacy"])
app.include_router(ai.router, prefix="/v1/ai", tags=["ai_legacy"])
app.include_router(apikeys.router, prefix="/v1/apikeys", tags=["apikeys_legacy"])
app.include_router(prompts.router, prefix="/v1/prompts", tags=["prompts_legacy"])
app.include_router(tags.router, prefix="/v1/tags", tags=["tags_legacy"])
app.include_router(style.router, prefix="/v1/styles", tags=["styles"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(logs.router, prefix="/v1/logs", tags=["logs"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if "/logs/latest" in request.url.path or "/ws/logs" in request.url.path:
        return await call_next(request)
    response = await call_next(request)
    return response

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
