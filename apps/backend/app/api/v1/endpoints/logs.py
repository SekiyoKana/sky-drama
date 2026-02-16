from fastapi import APIRouter, HTTPException
import os
from app.core.logger import logger, get_log_dir
from app.core.director_trace import list_director_runs, get_director_run

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


@router.get("/director-runs")
async def get_director_runs(
    limit: int = 20, project_id: int | None = None, episode_id: int | None = None
):
    runs = list_director_runs(limit=limit, project_id=project_id, episode_id=episode_id)
    return {"runs": runs}


@router.get("/director-runs/{run_id}")
async def get_director_run_detail(run_id: str):
    record = get_director_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Director run not found")
    return record
