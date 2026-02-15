from fastapi import APIRouter
import os
from app.core.logger import logger, get_log_dir

router = APIRouter()

@router.get("/latest")
async def get_latest_logs(limit: int = 100):
    """
    Retrieve the latest logs from the backend.
    Reads the active log file (app.log).
    """
    log_root = get_log_dir()
    log_file = os.path.join(log_root, "app.log")
    
    if not os.path.exists(log_file):
        return {"logs": []}
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return {"logs": lines[-limit:]}
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        return {"logs": [f"Error reading logs: {str(e)}"]}
