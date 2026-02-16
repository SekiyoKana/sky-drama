import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logger import get_log_dir

logger = logging.getLogger(__name__)

_TRACE_LOCK = threading.Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _trace_dir() -> str:
    base = os.path.join(get_log_dir(), "director_runs")
    os.makedirs(base, exist_ok=True)
    return base


def _coerce_int(val: Any) -> Optional[int]:
    try:
        return int(val)
    except Exception:
        return None


class DirectorTrace:
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = (run_id or "").strip() or f"run_{int(time.time())}_{os.getpid()}"
        self.path = os.path.join(_trace_dir(), f"{self.run_id}.json")
        self._last_progress = -1
        self._max_events = 2000
        self._finished = False
        self._started_ts = time.time()
        self.record: Dict[str, Any] = {
            "run_id": self.run_id,
            "status": "initialized",
            "started_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "ended_at": None,
            "duration_ms": None,
            "context": {},
            "metrics": {
                "events": 0,
                "statuses": 0,
                "progress_updates": 0,
                "backend_logs": 0,
                "errors": 0,
                "thought_chunks": 0,
                "thought_chars": 0,
            },
            "result": {},
            "events": [],
        }

    def start(self, context: Dict[str, Any]):
        with _TRACE_LOCK:
            self.record["status"] = "running"
            self.record["context"] = self._sanitize(context, max_str=600, depth=0)
            self.record["updated_at"] = _utc_now_iso()
            self._flush_locked()

    def has_errors(self) -> bool:
        return int(self.record.get("metrics", {}).get("errors", 0)) > 0

    def capture(self, event_type: str, payload: Any):
        if self._finished:
            return

        metrics = self.record["metrics"]
        metrics["events"] += 1

        if event_type == "status":
            metrics["statuses"] += 1
        elif event_type == "progress":
            metrics["progress_updates"] += 1
        elif event_type == "backend_log":
            metrics["backend_logs"] += 1
        elif event_type == "error":
            metrics["errors"] += 1
        elif event_type == "thought":
            text = payload if isinstance(payload, str) else str(payload)
            metrics["thought_chunks"] += 1
            metrics["thought_chars"] += len(text)

        event_payload = self._normalize_event_payload(event_type, payload)
        if event_payload is None:
            return

        with _TRACE_LOCK:
            self.record["events"].append(
                {"ts": _utc_now_iso(), "type": event_type, "payload": event_payload}
            )
            if len(self.record["events"]) > self._max_events:
                self.record["events"] = self.record["events"][-self._max_events :]

            if event_type in {"finish", "text_finish"}:
                self.record["result"] = self._summarize_result(payload)

            self.record["updated_at"] = _utc_now_iso()
            self._flush_locked()

    def finish(self, status: str = "completed", error: Optional[str] = None):
        if self._finished:
            return

        with _TRACE_LOCK:
            if error:
                self.record["metrics"]["errors"] += 1

            final_status = status
            if final_status == "completed" and self.has_errors():
                final_status = "error"

            self.record["status"] = final_status
            self.record["ended_at"] = _utc_now_iso()
            self.record["updated_at"] = self.record["ended_at"]
            self.record["duration_ms"] = int((time.time() - self._started_ts) * 1000)
            if error:
                self.record["result"]["error"] = str(error)[:2000]

            self._flush_locked()
            self._finished = True

    def _normalize_event_payload(self, event_type: str, payload: Any) -> Optional[Any]:
        if event_type == "thought":
            text = payload if isinstance(payload, str) else str(payload)
            # Token stream can be huge; keep sparse samples + tagged sections.
            chunk_count = int(self.record["metrics"]["thought_chunks"])
            should_store = "<|" in text or chunk_count % 80 == 1
            if not should_store:
                return None
            return {"sample": text[:600], "sample_len": len(text)}

        if event_type == "progress":
            value = _coerce_int(payload)
            if value is None:
                return {"value": payload}
            # Keep only changed progress and sparse checkpoints.
            if value == self._last_progress:
                return None
            if value not in {0, 1, 100} and value % 5 != 0:
                return None
            self._last_progress = value
            return {"value": value}

        return self._sanitize(payload)

    def _summarize_result(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            result = {}
            if "json" in payload:
                text = str(payload.get("json") or "")
                result["json_length"] = len(text)
                result["json_preview"] = text[:800]
            if "text" in payload:
                text = str(payload.get("text") or "")
                result["text_length"] = len(text)
                result["text_preview"] = text[:800]
            if "url" in payload:
                result["url"] = str(payload.get("url"))
            if not result:
                result = self._sanitize(payload, max_str=1000, depth=0)
            return result

        text = str(payload or "")
        return {"text_length": len(text), "text_preview": text[:800]}

    def _sanitize(
        self,
        value: Any,
        *,
        max_str: int = 1200,
        max_list: int = 30,
        depth: int = 0,
        max_depth: int = 4,
    ) -> Any:
        if depth > max_depth:
            return "[max-depth]"

        if value is None:
            return None

        if isinstance(value, (bool, int, float)):
            return value

        if isinstance(value, str):
            return value if len(value) <= max_str else value[:max_str] + "...[truncated]"

        if isinstance(value, dict):
            output = {}
            for i, (k, v) in enumerate(value.items()):
                if i >= 80:
                    output["..."] = "[truncated]"
                    break
                output[str(k)] = self._sanitize(
                    v,
                    max_str=max_str,
                    max_list=max_list,
                    depth=depth + 1,
                    max_depth=max_depth,
                )
            return output

        if isinstance(value, list):
            sliced = value[:max_list]
            out = [
                self._sanitize(
                    item,
                    max_str=max_str,
                    max_list=max_list,
                    depth=depth + 1,
                    max_depth=max_depth,
                )
                for item in sliced
            ]
            if len(value) > max_list:
                out.append(f"...[{len(value) - max_list} more]")
            return out

        if isinstance(value, tuple):
            return self._sanitize(list(value), max_str=max_str, max_list=max_list, depth=depth, max_depth=max_depth)

        return self._sanitize(str(value), max_str=max_str, max_list=max_list, depth=depth, max_depth=max_depth)

    def _flush_locked(self):
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.record, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)


def list_director_runs(
    limit: int = 20, project_id: Optional[int] = None, episode_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    root = _trace_dir()
    records: List[Dict[str, Any]] = []

    files = [name for name in os.listdir(root) if name.endswith(".json")]
    for name in files:
        path = os.path.join(root, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        ctx = data.get("context", {})
        if project_id is not None and _coerce_int(ctx.get("project_id")) != int(project_id):
            continue
        if episode_id is not None and _coerce_int(ctx.get("episode_id")) != int(episode_id):
            continue

        records.append(
            {
                "run_id": data.get("run_id"),
                "status": data.get("status"),
                "started_at": data.get("started_at"),
                "updated_at": data.get("updated_at"),
                "ended_at": data.get("ended_at"),
                "duration_ms": data.get("duration_ms"),
                "context": {
                    "project_id": ctx.get("project_id"),
                    "episode_id": ctx.get("episode_id"),
                    "user_id": ctx.get("user_id"),
                    "type": ctx.get("type"),
                    "skill": ctx.get("skill"),
                    "prompt_preview": ctx.get("prompt_preview"),
                },
                "metrics": data.get("metrics", {}),
            }
        )

    records.sort(key=lambda item: item.get("started_at") or "", reverse=True)
    return records[: max(1, min(int(limit), 200))]


def get_director_run(run_id: str) -> Optional[Dict[str, Any]]:
    run_id = (run_id or "").strip()
    if not run_id:
        return None

    path = os.path.join(_trace_dir(), f"{run_id}.json")
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read director trace '{run_id}': {e}")
        return None
