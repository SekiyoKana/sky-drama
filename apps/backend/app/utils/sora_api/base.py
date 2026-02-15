import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable

import logging

logger = logging.getLogger(__name__)

class Base(ABC):
    name: str = "base"
    base_url_keyword: str = ""
    
    # Store context for queueing if needed (optional design, but helps if queue signature is restricted)
    _base_url: str = ""
    _apikey: str = ""
    _headers: Dict = {}

    def match(self, base_url: str) -> bool:
        return self.base_url_keyword == base_url if self.base_url_keyword else False

    def set_auth(self, base_url: str, apikey: str):
        self._base_url = base_url.rstrip('/')
        self._apikey = apikey
        self._headers = {
            "Authorization": f"Bearer {apikey}",
            "Content-Type": "application/json"
        }

    @abstractmethod
    def create(self, base_url: str, apikey: str, model: str, prompt: str, seconds: int, size: str, watermark: bool, images: List[Any]) -> str:
        """
        执行创建任务。
        Returns: task_id
        Raises: Exception if failed
        """
        pass

    def queue(self, task_id: str, listener: Callable[[str, Any], None]) -> str:
        """
        监听任务状态。
        listener: function(status: str, data: Any)
        Returns: video_url
        Raises: Exception if failed
        """
        max_retries = 120 # 120 * 5s = 10 minutes
        for i in range(max_retries):
            time.sleep(5)
            try:
                # Use query logic here
                result = self._query_status(task_id)
                status = result.get("status")
                
                # Notify listener
                listener(status, result)

                if status == "completed":
                    video_url = result.get("video_url")
                    if not video_url:
                         raise Exception("Video completed but URL not found")
                    return video_url
                
                elif status == "failed":
                    raise Exception(f"Video generation failed: {result.get('fail_reason')}")
                
            except Exception as e:
                # If it's our own exception from failed status, re-raise
                if "Video generation failed" in str(e) or "URL not found" in str(e):
                    raise e
                # Network errors during polling: log and continue
                logger.info(f"Polling error: {e}")
                continue
        
        raise Exception("Video generation timed out")

    @abstractmethod
    def _query_status(self, task_id: str) -> Dict[str, Any]:
        """
        Abstract method to query specific API.
        Returns: {
            "status": "completed" | "processing" | "failed",
            "progress": int,
            "video_url": str | None,
            "fail_reason": str | None,
            ...other data
        }
        """
        pass
