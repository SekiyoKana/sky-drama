import json
import os
import time
import uuid
import re
import mimetypes
from urllib.parse import urlparse
from app.utils.http_client import request as http_request, download_headers
import logging
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Union
from openai import OpenAI
from fastapi import HTTPException
import threading

logger = logging.getLogger(__name__)

from app.models.apikey import ApiKey
from app.models.asset import Asset
from app.skills.loader import execute_skill
from app.utils.image_utils import combine_image, split_grid_image, to_base64
from app.schemas.style import StyleBase
from app.utils.sora_api.main import SoraApiFormatter
from app.core.config import settings
from app.utils.think_filter import sanitize_think_payload, strip_think_segments
from app.core.provider_platform import (
    PLATFORM_OLLAMA,
    PLATFORM_VOLCENGINE,
    normalize_platform,
    resolve_base_url,
    resolve_endpoint,
    requires_api_key,
)
from app.utils.ollama_client import OllamaClient, list_ollama_models


class AIEngine:
    def __init__(self, db, user, ai_config):
        self.db = db
        self.user = user
        self.config = ai_config or {}
        client, model, _, _, _ = self._init_client_and_model()
        self.client = client
        self.model_name = model
        self.episode = None
        self.trace = None

    def set_context(self, episode):
        self.episode = episode

    def set_trace(self, trace):
        self.trace = trace

    def _format_sse(self, event_type: str, data: Any):
        if self.trace:
            try:
                self.trace.capture(event_type, data)
            except Exception as e:
                logger.debug(f"Trace capture failed for event '{event_type}': {e}")
        payload = json.dumps({"type": event_type, "payload": data}, ensure_ascii=False)
        return f"data: {payload}\n\n"
        
    def _resolve_local_path(self, path_or_url: str) -> Optional[str]:
        """
        将 URL 或相对路径统一转换为可读取的本地绝对路径
        """
        if not path_or_url:
            return None
            
        # 1. 如果是网络 URL -> 尝试映射本地 assets，否则下载到临时文件
        if path_or_url.startswith("http"):
            try:
                parsed = urlparse(path_or_url)
                if parsed.hostname in {"127.0.0.1", "localhost", "backend"} and parsed.path.startswith("/assets/"):
                    assets_dir = settings.ASSETS_DIR
                    local_rel = parsed.path.replace("/assets/", "", 1)
                    local_path = os.path.join(assets_dir, local_rel)
                    if os.path.exists(local_path):
                        return local_path

                # logger.info(f"Downloading remote resource: {path_or_url}")
                res = http_request("GET", path_or_url, stream=True, timeout=(10, 60))
                try:
                    if res.status_code == 200:
                        ext = path_or_url.split('.')[-1].split('?')[0]
                        if len(ext) > 4 or "/" in ext: ext = "png"
                        
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
                        with open(tmp.name, 'wb') as f:
                            shutil.copyfileobj(res.raw, f)
                        return tmp.name
                    else:
                        logger.error(f"Failed to download image {path_or_url}: Status {res.status_code}")
                        return None
                finally:
                    try:
                        res.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error downloading image {path_or_url}: {e}")
                return None

        # 2. 如果是本地绝对路径 -> 直接返回
        if os.path.isabs(path_or_url) and os.path.exists(path_or_url):
            return path_or_url

        # 3. 如果是 /assets/xxx 相对路径 -> 映射到 ASSETS_DIR
        assets_dir = settings.ASSETS_DIR

        # 移除开头的 / 或 \ 或 .
        clean_path = path_or_url.lstrip("/\\.")
        # 如果路径里包含 assets/ 前缀，也去掉
        if clean_path.startswith("assets/") or clean_path.startswith("assets\\"):
            clean_path = clean_path[7:]
            
        local_path = os.path.join(assets_dir, clean_path)
        
        if os.path.exists(local_path):
            return local_path
            
        return path_or_url

    def _normalize_remote_url(self, url: Optional[str], base_url: Optional[str] = None, response_data: Optional[dict] = None) -> Optional[str]:
        if not url:
            return url

        url = str(url).strip()

        if url.startswith("http://") or url.startswith("https://"):
            return url

        if url.startswith("//"):
            return f"https:{url}"

        host = None
        candidates = []
        if isinstance(response_data, dict):
            candidates.append(response_data)
            data_list = response_data.get("data")
            if isinstance(data_list, list) and data_list:
                if isinstance(data_list[0], dict):
                    candidates.append(data_list[0])

        for candidate in candidates:
            for key in ("host", "domain", "image_host", "cdn_host", "url_prefix", "base_url"):
                val = candidate.get(key)
                if val:
                    host = str(val).strip()
                    break
            if host:
                break

        if host:
            if host.startswith("//"):
                host = f"https:{host}"
            if not host.startswith("http"):
                host = f"https://{host.lstrip('/')}"
            if url.startswith("/"):
                return f"{host.rstrip('/')}{url}"
            return f"{host.rstrip('/')}/{url}"

        if base_url:
            parsed = urlparse(str(base_url))
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
                if url.startswith("/"):
                    return f"{origin}{url}"

        if re.match(r"^[A-Za-z0-9.-]+\\.[A-Za-z]{2,}(/.*)?$", url):
            return f"https://{url}"

        return url

    @staticmethod
    def resolve_prompt_tags(prompt: str, script_data: Optional[dict], text_mode: bool = False) -> str:
        prompt_text = str(strip_think_segments(prompt or "")).strip()
        if not prompt_text or not isinstance(script_data, dict):
            return prompt_text

        characters = script_data.get("characters", [])
        scenes = script_data.get("scenes", [])
        storyboard_marker = "[分镜列表]"
        storyboard_index = prompt_text.find(storyboard_marker)

        def replace_tag(match):
            tag_type = match.group(1)
            tag_suffix = match.group(2)
            if tag_type == "character":
                tag_type = "char"

            possible_ids = [tag_suffix]
            if tag_type == "char":
                possible_ids.append(f"char_{tag_suffix}")
            elif tag_type == "scene":
                possible_ids.append(f"scene_{tag_suffix}")

            is_in_storyboard_list = (
                storyboard_index != -1 and match.start() > storyboard_index
            )

            if tag_type == "char":
                char = next(
                    (c for c in characters if str(c.get("id")) in possible_ids),
                    None,
                )
                if char:
                    if text_mode or is_in_storyboard_list:
                        return char.get("name", "未知角色")
                    return f"[{char.get('name', '未知角色')}: {char.get('description', '')}]"
                return match.group(0)

            if tag_type == "scene":
                scene = next(
                    (s for s in scenes if str(s.get("id")) in possible_ids),
                    None,
                )
                if scene:
                    if text_mode or is_in_storyboard_list:
                        return scene.get("location_name", "未知场景")
                    return f"[{scene.get('location_name', '未知场景')}: {scene.get('mood', '')}]"
                return match.group(0)

            return match.group(0)

        return re.sub(
            r"\{\{(char|character|scene)_([a-zA-Z0-9_]+)\}\}",
            replace_tag,
            prompt_text,
        )

    @staticmethod
    def build_video_request_prompt(prompt: str, video_config: Optional[dict] = None) -> str:
        prompt_text = str(sanitize_think_payload(prompt) if prompt else "").strip()
        if not prompt_text:
            return ""

        cfg = video_config if isinstance(video_config, dict) else {}
        prompt_prefixes: List[str] = []
        if cfg.get("remove_bgm") and "无背景音乐" not in prompt_text:
            prompt_prefixes.append("无背景音乐")
        if cfg.get("keep_voice") and "保留人物声音" not in prompt_text:
            prompt_prefixes.append("保留人物声音")
        if cfg.get("keep_sfx") and "保留人物音效" not in prompt_text:
            prompt_prefixes.append("保留人物音效")
        voice_language = cfg.get("voice_language")
        if voice_language and voice_language not in {"不指定", "unspecified"}:
            lang_prompt = f"{voice_language}配音"
            if lang_prompt not in prompt_text:
                prompt_prefixes.append(lang_prompt)
        if prompt_prefixes:
            prompt_text = f"{'，'.join(prompt_prefixes)}。\n{prompt_text}"
        return prompt_text


    def _init_client_and_model(self, type="text"):
        config = self.config.get(type, {})

        if not config.get("key_id"):
            config = self.config.get("text", {})

        key_id = config.get("key_id")
        model_name = config.get("model")

        if not key_id:
            return None, None, None, None, None

        api_key_record = (
            self.db.query(ApiKey)
            .filter(ApiKey.id == key_id, ApiKey.user_id == self.user.id)
            .first()
        )

        if not api_key_record:
            raise HTTPException(status_code=404, detail="API Key 不存在")
        
        platform = normalize_platform(api_key_record.platform)
        # 直接使用明文 Key
        real_key = api_key_record.encrypted_key or ""
        # try:
        #     real_key = decrypt_data(api_key_record.encrypted_key)
        # except:
        #     raise HTTPException(status_code=500, detail="Key 解密失败")

        base_url = resolve_base_url(platform, api_key_record.base_url)

        if platform == PLATFORM_OLLAMA:
            text_endpoint = resolve_endpoint(
                platform, "text_endpoint", api_key_record.text_endpoint
            )
            if not model_name:
                try:
                    discovered = list_ollama_models(base_url, real_key)
                    if discovered:
                        model_name = discovered[0]
                except Exception:
                    pass
            if type == "text":
                client = OllamaClient(
                    base_url=base_url,
                    api_key=real_key,
                    chat_endpoint=text_endpoint,
                )
                return client, model_name, real_key, base_url, api_key_record
            return None, model_name, real_key, base_url, api_key_record

        if requires_api_key(platform) and not real_key:
            raise HTTPException(status_code=400, detail="API Key 未配置")

        client = OpenAI(api_key=real_key, base_url=base_url)
        return client, model_name, real_key, base_url, api_key_record

    def generate_media_stream(self, media_type: str, prompt: str, style: StyleBase = None, data: dict = None):
        try:
            yield self._format_sse("status", f"Starting {media_type} generation...")
            yield self._format_sse("backend_log", f"--- [Backend] Starting {media_type} generation ---")
            yield self._format_sse("backend_log", f"Prompt: {prompt}")

            _, model_name, real_key, base_url, api_key_record = self._init_client_and_model(
                type=media_type
            )
            platform = normalize_platform(api_key_record.platform) if api_key_record else ""
            if platform == PLATFORM_OLLAMA:
                yield self._format_sse(
                    "error", "Ollama 平台目前仅支持文本工作流，不支持图像/视频生成。"
                )
                return
            if requires_api_key(platform) and not real_key:
                yield self._format_sse(
                    "error", f"No API configuration found for {media_type}"
                )
                return

            yield self._format_sse("status", "Requesting generation API...")

            headers = {
                "Authorization": f"Bearer {real_key}",
                "Content-Type": "application/json",
            }

            progress_value = [1]
            yield self._format_sse("progress", progress_value[0])

            def _bump_progress():
                if progress_value[0] < 99:
                    progress_value[0] += 1
                yield self._format_sse("progress", progress_value[0])

            def _run_with_progress(worker, interval=5):
                result = {}

                def _target():
                    try:
                        result["value"] = worker()
                    except Exception as e:
                        result["error"] = e

                t = threading.Thread(target=_target, daemon=True)
                t.start()
                while t.is_alive():
                    time.sleep(interval)
                    yield from _bump_progress()
                if "error" in result:
                    raise result["error"]
                return result.get("value")

            if media_type == "video":
                video_config = self.config.get("video", {}) if isinstance(self.config, dict) else {}
                prompt = self.build_video_request_prompt(prompt, video_config)

                headers.pop("Content-Type", None)

                target_model = model_name if model_name else "sora-2"
                endpoint = resolve_endpoint(
                    platform,
                    "video_endpoint",
                    api_key_record.video_endpoint if api_key_record else None,
                )
                fetch_endpoint = resolve_endpoint(
                    platform,
                    "video_fetch_endpoint",
                    api_key_record.video_fetch_endpoint if api_key_record else None,
                )
                base_url_str = str(base_url).rstrip('/')
                api_url = f"{base_url_str}{endpoint}"
                yield self._format_sse("backend_log", f"Video Endpoint: {api_url}")
                
                mode = data.get("generation_mode") if isinstance(data, dict) else None
                raw_ref = data.get("input_reference") if isinstance(data, dict) else None
                ref_list: List[str] = []
                if isinstance(raw_ref, (list, tuple)):
                    ref_list = [ref for ref in raw_ref if ref]
                elif raw_ref:
                    ref_list = [raw_ref]

                temp_files: List[str] = []
                image_refs: List[str] = []

                if mode == "keyframes":
                    if not ref_list:
                        yield self._format_sse("error", "未找到分镜参考图，请先生成分镜图后再试。")
                        return
                    if platform == PLATFORM_VOLCENGINE:
                        # Volcengine official API expects content[].image_url, not local multipart files.
                        image_refs = [str(ref) for ref in ref_list if ref]
                    else:
                        grid_ref = ref_list[0]
                        grid_local = self._resolve_local_path(grid_ref) or grid_ref
                        try:
                            frame_paths = split_grid_image(grid_local, rows=3, cols=3)
                        except Exception as e:
                            raise RuntimeError(f"Failed to split storyboard image: {str(e)}")
                        image_refs = frame_paths
                        temp_files.extend(frame_paths)
                else:
                    final_ref = None
                    if ref_list:
                        if platform == PLATFORM_VOLCENGINE:
                            final_ref = ref_list[0]
                        else:
                            local_ref = self._resolve_local_path(ref_list[0])
                            final_ref = local_ref if local_ref else ref_list[0]
                    image_refs = [final_ref] if final_ref else []
                
                formatter = None if platform == PLATFORM_VOLCENGINE else SoraApiFormatter.search(base_url_str)
                task_id = None
                task_data: Dict[str, Any] = {}
                should_poll_task = False
                try:
                    if formatter:
                        yield self._format_sse("status", f"Delegating to {formatter.name} formatter...")
                        
                        try:
                            task_id = formatter.create(
                                base_url=base_url_str,
                                apikey=real_key,
                                model=target_model,
                                prompt=f'{prompt}',
                                seconds=15,
                                size="1280x720",
                                watermark=False,
                                images=image_refs
                            )
                            
                            yield self._format_sse("status", f"Task created: {task_id}, queuing...")

                            def status_listener(status, data):
                                progress = data.get("progress", 0)
                                if progress < 10: progress = 10
                                if progress > 99: progress = 99
                                logger.info(f"[Formatter: {status}] Progress: {progress}%")
                            
                            video_url = yield from _run_with_progress(
                                lambda: formatter.queue(task_id, status_listener)
                            )
                            
                            image_url = video_url
                            ext = "mp4"

                        except Exception as e:
                            raise RuntimeError(f"Formatter Error: {str(e)}")

                    else:
                        should_poll_task = True
                        if platform == PLATFORM_VOLCENGINE:
                            # Official Volcengine video generation API expects JSON body:
                            # { "model": "...", "content": [{ "type":"text","text":"..." }, ...] }
                            content_payload: List[Dict[str, Any]] = [
                                {"type": "text", "text": f"{prompt}"}
                            ]

                            remote_refs: List[str] = []
                            for raw_ref in image_refs:
                                normalized_ref = self._normalize_remote_url(
                                    raw_ref, base_url=None
                                )
                                if normalized_ref and str(normalized_ref).startswith(
                                    ("http://", "https://")
                                ):
                                    remote_refs.append(str(normalized_ref))
                                elif normalized_ref:
                                    yield self._format_sse(
                                        "backend_log",
                                        f"Skip non-public image reference for Volcengine: {normalized_ref}",
                                    )

                            model_lower = (target_model or "").lower()
                            if remote_refs:
                                # i2v models may accept keyframe roles; for other models keep a single image_url.
                                if "i2v" in model_lower and len(remote_refs) >= 2:
                                    content_payload.append(
                                        {
                                            "type": "image_url",
                                            "role": "first_frame",
                                            "image_url": {"url": remote_refs[0]},
                                        }
                                    )
                                    content_payload.append(
                                        {
                                            "type": "image_url",
                                            "role": "last_frame",
                                            "image_url": {"url": remote_refs[-1]},
                                        }
                                    )
                                else:
                                    content_payload.append(
                                        {
                                            "type": "image_url",
                                            "image_url": {"url": remote_refs[0]},
                                        }
                                    )
                            elif "i2v" in model_lower:
                                raise RuntimeError(
                                    "Volcengine i2v 模型需要可公网访问的 image_url 参数。"
                                )

                            request_payload = {
                                "model": target_model,
                                "content": content_payload,
                            }
                            yield self._format_sse(
                                "backend_log",
                                f"Volcengine request: model={target_model}, content_items={len(content_payload)}",
                            )
                            yield self._format_sse(
                                "status", f"Submitting video task to {target_model}..."
                            )

                            volc_headers = dict(headers)
                            volc_headers["Content-Type"] = "application/json"
                            response = http_request(
                                "POST",
                                api_url,
                                json=request_payload,
                                headers=volc_headers,
                                timeout=60000,
                            )
                        else:
                            if not image_refs:
                                yield self._format_sse(
                                    "error", "未找到分镜参考图，请先生成分镜图后再试。"
                                )
                                return

                            form_data = {
                                "model": target_model,
                                "prompt": f'{prompt}',
                                "seconds": "15",
                                "size": "1280x720",
                                "watermark": False,
                            }

                            if mode == "keyframes":
                                files_payload = []
                                file_handles = []
                                try:
                                    for idx, img_path in enumerate(image_refs):
                                        local_path = self._resolve_local_path(img_path) or img_path
                                        if not local_path or not os.path.exists(local_path):
                                            raise RuntimeError("无法读取关键帧参考图，请检查分镜图是否有效。")

                                        mime_type = mimetypes.guess_type(local_path)[0] or "image/png"
                                        ext = os.path.splitext(local_path)[1].lstrip(".") or "png"
                                        filename = f"keyframe_{idx + 1}.{ext}"
                                        file_handle = open(local_path, "rb")
                                        file_handles.append(file_handle)
                                        files_payload.append(
                                            ("input_reference", (filename, file_handle, mime_type))
                                        )

                                    yield self._format_sse("status", f"Submitting video task to {target_model}...")
                                    response = http_request(
                                        "POST",
                                        api_url,
                                        data=form_data,
                                        files=files_payload,
                                        headers=headers,
                                        timeout=60000
                                    )
                                finally:
                                    for file_handle in file_handles:
                                        try:
                                            file_handle.close()
                                        except Exception:
                                            pass
                            else:
                                images_for_combine = [{ "data": image_refs, "direction": "horizontal"}]
                                img_stream, mime_type = combine_image(images_for_combine, direction='vertical')
                                ext = "png" if mime_type == "image/png" else "jpg"
                                filename = f"template.{ext}"

                                files_payload = {
                                    "input_reference": (filename, img_stream, mime_type)
                                }

                                yield self._format_sse("status", f"Submitting video task to {target_model}...")
                                response = http_request(
                                    "POST",
                                    api_url,
                                    data=form_data,
                                    files=files_payload,
                                    headers=headers,
                                    timeout=60000
                                )

                        if response.status_code < 200 or response.status_code >= 300:
                            raise RuntimeError(
                                f"Video Provider Error ({response.status_code}): {response.text}"
                            )

                        task_data = response.json() if response.content else {}
                        if not isinstance(task_data, dict):
                            raise RuntimeError(
                                f"Unexpected task create response: {str(task_data)}"
                            )
                        task_id = (
                            task_data.get("id")
                            or task_data.get("task_id")
                            or task_data.get("detail", {}).get("id")
                            or task_data.get("data", {}).get("id")
                            or task_data.get("data", {}).get("task_id")
                            or task_data.get("data", {}).get("task", {}).get("id")
                        )
                finally:
                    for temp_path in temp_files:
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass

                if should_poll_task:
                    if not task_id:
                        raise RuntimeError(f"No task ID returned: {str(task_data)}")
                    
                    if "{task_id}" in fetch_endpoint:
                        poll_path = fetch_endpoint.replace("{task_id}", str(task_id))
                    elif fetch_endpoint.endswith("/"):
                        poll_path = f"{fetch_endpoint}{task_id}"
                    else:
                        poll_path = f"{fetch_endpoint}/{task_id}"
                    poll_url = f"{str(base_url).rstrip('/')}{poll_path}"
                    yield self._format_sse("backend_log", f"Video Poll URL: {poll_url}")
                    poll_headers = dict(headers)
                    poll_headers.pop("Content-Type", None)
                    poll_headers.update(download_headers())
                    poll_headers["Referer"] = ""
                    
                    max_retries = 10000
                    for i in range(max_retries):
                        time.sleep(5)
                        yield from _bump_progress()
                        try:
                            poll_res = http_request("GET", poll_url, headers=poll_headers, timeout=30)
                            if poll_res.status_code != 200:
                                continue
                                
                            poll_data = poll_res.json()
                            log_msg = f"[{poll_data.get('model')} - {poll_data.get('id')}]｜状态 - {poll_data.get('status')} ｜进度 - {poll_data.get('progress', 0)}%"
                            logger.info(f"\n------------------------------------\n{log_msg}\n------------------------------------\n")
                            yield self._format_sse("backend_log", log_msg)
                            
                            status = str(poll_data.get("status") or "").lower()
                            completed_status = {"completed", "succeeded", "success", "done"}
                            failed_status = {"failed", "error"}

                            if status in completed_status:
                                video_url = poll_data.get("video_url")
                                if not video_url:
                                    video_url = poll_data.get("detail", {}).get("draft_info", {}).get("downloadable_url")
                                if not video_url:
                                    video_url = poll_data.get("url")
                                if not video_url and isinstance(poll_data.get("data"), dict):
                                    video_url = (
                                        poll_data["data"].get("video_url")
                                        or poll_data["data"].get("url")
                                    )
                                
                                if not video_url:
                                    raise RuntimeError("Video completed but URL not found")
                                
                                yield self._format_sse("status", "Downloading video...")
                                data = poll_data
                                image_url = video_url 
                                ext = "mp4"
                                break
                            elif status in failed_status:
                                raise RuntimeError(f"Video generation failed: {poll_data.get('fail_reason', 'Unknown')}")
                            else:
                                yield self._format_sse("status", f"Generating video... ({status})")
                        except Exception as e:
                            logger.error(f"Polling error: {e}")
                            yield self._format_sse("backend_log", f"Polling error: {str(e)}")
                            continue
                    else:
                        raise RuntimeError("Video generation timed out")

            else:
                target_model = model_name if model_name else "nano-banana"
                endpoint = resolve_endpoint(
                    platform,
                    "image_endpoint",
                    api_key_record.image_endpoint if api_key_record else None,
                )
                api_url = f"{str(base_url).rstrip('/')}{endpoint}"
                ext = "png"

                yield self._format_sse("backend_log", f"Image Model: {target_model}")
                yield self._format_sse("backend_log", f"Image Endpoint: {api_url}")

                payload = {
                    "model": target_model,
                    "prompt": prompt,
                    "size": "16x9",
                    "n": 1,
                }
                provider_prompt = prompt
    
                if data and "category" in data:
                    category = data["category"]
                    template_base64 = None
                    assets_dir = settings.ASSETS_DIR
                    if category == "character":
                        template_base64 = to_base64(os.path.join(assets_dir, "static", "character_template.png"))
                    elif category == "scene":
                        template_base64 = to_base64(os.path.join(assets_dir, "static", "scene_template.png"))
                    
                    style_local_path = self._resolve_local_path(style.image_url) if style and style.image_url else None
                    style_image_base64 = to_base64(style_local_path) if style_local_path else None

                    reference_image_base64 = None
                    if data and data.get("reference_image"):
                        ref_local_path = self._resolve_local_path(data.get("reference_image"))
                        if ref_local_path:
                            reference_image_base64 = to_base64(ref_local_path)

                    if category == "storyboard":
                        grid_count = None
                        if data:
                            for key in ("storyboard_grid", "grid", "frame_count"):
                                if data.get(key) is not None:
                                    try:
                                        grid_count = int(data.get(key))
                                    except Exception:
                                        grid_count = None
                                    break
                            if grid_count is None:
                                mode = data.get("generation_mode")
                                if mode == "single":
                                    grid_count = 9
                                elif mode == "keyframes":
                                    grid_count = 9
                        if grid_count not in {6, 9}:
                            grid_count = 9

                        images = []
                        if data and data.get("context_characters"):
                            raw_char_imgs = [char.get("image_url") for char in data.get("context_characters")]
                            char_imgs = [self._resolve_local_path(url) for url in raw_char_imgs]
                            char_imgs = [p for p in char_imgs if p]
                            images.append({ "data": char_imgs, "direction": "horizontal" })
                            
                        if data and data.get("context_scenes"):
                            raw_scene_imgs = [scene.get("image_url") for scene in data.get("context_scenes")]
                            scene_imgs = [self._resolve_local_path(url) for url in raw_scene_imgs]
                            scene_imgs = [p for p in scene_imgs if p]
                            images.append({ "data": scene_imgs, "direction": "horizontal" })

                        if len(images) == 0:
                            yield self._format_sse("error", "请检查角色、场景以及分镜都已生成完毕")
                            return
                        
                        combine_path, _ = combine_image(images, direction='vertical', return_type='path')
                        temp_image_base64 = to_base64(combine_path)
                        if style_image_base64:
                            payload["image"] = [style_image_base64, temp_image_base64]
                            payload["prompt"] = f"参考第一张图片的画风，参考第二张图片的人设与场景，生成一张16:9的{grid_count}宫格分镜图：{prompt}"
                        else:
                            payload["image"] = [temp_image_base64]
                            payload["prompt"] = f"参考第一张图片的人设与场景，生成一张16:9的{grid_count}宫格分镜图：{prompt}"
                    else:
                        if not template_base64:
                            yield self._format_sse("error", f"Failed to load template image for category: {category}")
                            return
                        if style_image_base64 and reference_image_base64:
                            payload["image"] = [style_image_base64, reference_image_base64, template_base64]
                            payload["prompt"] = f"参考第一张图片的图片风格，第二张图片的参考图，以第三张图片作为生成模板生成目标图片，并始终保持模板的第一格为黑幕。 {prompt}"
                        elif reference_image_base64:
                            payload["image"] = [reference_image_base64, template_base64]
                            payload["prompt"] = f"参考第一张图片的参考图，使用第二张图片作为生成模板生成目标图片，并始终保持模板的第一格为黑幕。 {prompt}"
                        else:
                            payload["image"] = [style_image_base64, template_base64] if style_image_base64 else [template_base64]
                            payload["prompt"] = f"使用第一张图片的图片风格，以第二张图片作为生成模板生成目标图片，并始终保持模板的第一格为黑幕。 {prompt}" if style_image_base64 else f"使用这张图片作为生成模板生成目标图片，并始终保持模板的第一格为黑幕。{prompt}"
                provider_prompt = str(payload.get("prompt") or prompt)
    
                yield self._format_sse("backend_log", "Submitting image generation request...")

                response = yield from _run_with_progress(
                    lambda: http_request("POST", api_url, json=payload, headers=headers, timeout=3000)
                )
                yield self._format_sse("backend_log", f"Response Status: {response.status_code}")

                if response.status_code != 200:
                    raise RuntimeError(f"Provider Error: {response.text}")

                data = response.json()

                yield self._format_sse("status", "Processing response...")
    
                image_url = None
                if (
                    "data" in data
                    and isinstance(data["data"], list)
                    and len(data["data"]) > 0
                ):
                    image_url = data["data"][0].get("url")
    
                if not image_url:
                    raise RuntimeError(f"No image URL in response: {str(data)}")

            yield self._format_sse("status", "Downloading asset...")
            image_url = self._normalize_remote_url(image_url, base_url=base_url, response_data=data)
            img_res = yield from _run_with_progress(
                lambda: http_request("GET", image_url, timeout=600, headers=download_headers())
            )
            if img_res.status_code != 200:
                raise RuntimeError("Failed to download asset")
            filename = f"{uuid.uuid4()}.{ext}"
            
            assets_dir = settings.ASSETS_DIR
            if not os.path.exists(assets_dir): os.makedirs(assets_dir)
                
            filepath = os.path.join(assets_dir, filename)
            logger.info(f"💾 Saving generated asset to: {filepath}")

            with open(filepath, "wb") as f:
                f.write(img_res.content)

            asset_url = f"/assets/{filename}"
            asset_meta = {
                "prompt": prompt,
                "provider_prompt": provider_prompt if media_type == "image" else prompt,
                "source_url": image_url,
            }
            if media_type == "video":
                asset_meta["video_request_prompt"] = prompt
            if style and getattr(style, "image_url", None):
                asset_meta["style_image_url"] = str(style.image_url)
            new_asset = Asset(
                episode_id=self.episode.id if self.episode else 0,
                type=media_type,
                url=asset_url,
                meta_data=asset_meta,
            )
            self.db.add(new_asset)
            self.db.commit()
            self.db.refresh(new_asset)
            
            # 返回相对路径给前端，由前端根据运行环境解析
            full_display_url = asset_url

            yield self._format_sse("progress", 100)
            yield self._format_sse("status", "Completed")
            yield self._format_sse(
                "finish",
                {
                    "id": new_asset.id,
                    "url": full_display_url,
                    "type": media_type,
                    "prompt": prompt,
                    "input_prompt": prompt,
                    "final_prompt": provider_prompt if media_type == "image" else prompt,
                    "provider_prompt": provider_prompt if media_type == "image" else prompt,
                    "video_request_prompt": prompt if media_type == "video" else "",
                },
            )

        except GeneratorExit:
            logger.info(f"[AIEngine] Media stream '{media_type}' closed by caller.")
            return
        except Exception as e:
            logger.error(f"Generation Loop Error: {e}")
            yield self._format_sse("error", f"Generation failed: {str(e)}")

    def generate_stream(self, prompt: str, tool_name: str, **kwargs):
        try:
            client, model, _, _, _ = self._init_client_and_model(type="text")
            if not client:
                yield self._format_sse("error", "No API Key configured for text generation")
                return
            if not model:
                yield self._format_sse("error", "No model selected for text generation")
                return
            self.client = client
            self.model_name = model

            yield self._format_sse("status", "Initializing AI Director...")

            skill_args = {"prompt": prompt}

            if "title" in kwargs:
                skill_args["title"] = kwargs["title"]
            if "description" in kwargs:
                skill_args["description"] = kwargs["description"]
            elif prompt:
                skill_args["description"] = prompt

            for k, v in kwargs.items():
                if k not in skill_args and k not in ["title", "description"]:
                    skill_args[k] = v

            if tool_name == "short-video-screenwriter":
                skill_args["existing_data"] = self._collect_project_assets()

            # Inject project-level existing assets for screenwriter
            if tool_name == "short-video-screenwriter":
                existing_data = self._collect_project_assets()
                if "existing_data" in skill_args and isinstance(skill_args["existing_data"], dict):
                    # Merge provided data with project assets (project assets win on id/name)
                    provided = skill_args["existing_data"]
                    merged = {
                        "characters": (provided.get("characters") or []) + (existing_data.get("characters") or []),
                        "scenes": (provided.get("scenes") or []) + (existing_data.get("scenes") or []),
                    }
                    skill_args["existing_data"] = merged
                else:
                    skill_args["existing_data"] = existing_data


            logger.info(f"[AI Director] Executing skill: {tool_name}")
            logger.info(f"[AI Director] Arguments keys: {list(skill_args.keys())}")

            director_gen = execute_skill(
                tool_name, skill_args, client=self.client, model_name=self.model_name
            )

            final_output_accumulator = yield from self._priint_at_director_console(tool_name, director_gen)

            if not final_output_accumulator:
                yield self._format_sse("error", "No output from AI Director")
                return

            yield from self._submit(
                tool_name=tool_name,
                final_output_accumulator=final_output_accumulator,
            )

        except GeneratorExit:
            logger.info(f"[AIEngine] Text stream '{tool_name}' closed by caller.")
            return
        except Exception as e:
            yield self._format_sse("error", f"Execution error: {str(e)}")

    def _priint_at_director_console(self, tool_name, director_gen):
        final_output_accumulator = ""
        
        logger.info(f"[AI Director] Listening to stream from {tool_name}...")
        
        start_time = time.time()
        last_progress = 0

        try:
            for chunk in director_gen:
                # Time-based progress simulation: 1% per second
                elapsed = time.time() - start_time
                current_progress = min(int(elapsed), 98) # Cap at 98%
                
                if current_progress > last_progress:
                    yield self._format_sse("progress", current_progress)
                    last_progress = current_progress

                # logger.debug(f"[Stream Chunk] {chunk}") # Verbose debug
                if not isinstance(chunk, dict):
                    continue

                msg_type = chunk.get("type")
                content = chunk.get("content", "")

                if msg_type == "status":
                    yield self._format_sse("status", content)
                    yield self._format_sse("backend_log", f"[{tool_name}] Status: {content}")
                elif msg_type == "token":
                    final_output_accumulator += content
                    yield self._format_sse("thought", content)
                elif msg_type == "error":
                    logger.error(f"[{tool_name}] Error: {content}")
                    yield self._format_sse("error", f"[{tool_name}] {content}")
                    yield self._format_sse("backend_log", f"[{tool_name}] ERROR: {content}")
        except GeneratorExit:
            logger.info(f"[AI Director] Stream for {tool_name} closed by caller.")
            return final_output_accumulator

        logger.info(f"[AI Director] Stream finished. Total length: {len(final_output_accumulator)}")
        return final_output_accumulator

    def _get_json_block(self, text=None):
        if not text:
            return None
        json_match = None
        try:
            json_blocks = re.findall(
                r"```json\s*([\s\S]*?)\s*```", text
            )

            merged_data = {}
            if json_blocks:
                for block in json_blocks:
                    try:
                        clean_block = re.sub(r"<\|.*?\|>", "", block)
                        clean_block = strip_think_segments(clean_block)
                        data = json.loads(clean_block)
                        if isinstance(data, dict):
                            merged_data.update(data)
                    except:
                        pass

                if merged_data:
                    json_match = json.dumps(merged_data)
            else:
                clean_text = re.sub(r"<\|.*?\|>", "", text)
                clean_text = strip_think_segments(clean_text)
                clean_text = clean_text.replace("```json", "").replace(
                    "```", ""
                )
                parsed = json.loads(clean_text)
                json_match = json.dumps(parsed)

        except:
            pass

        return json_match

    def _get_tag_block(self, text=None, tag_map=None):
        if not text or not tag_map:
            return None
        tag_match: Dict[str, Union[str, List[str]]] = {}
        for tag, key in tag_map.items():
            pattern = rf"<\|{tag}\|>([\s\S]*?)<\|{tag}_END\|>"
            matches = re.findall(pattern, text)
            
            if matches:
                cleaned_matches = [m.strip() for m in matches]
                if len(cleaned_matches) > 1:
                    tag_match[key] = cleaned_matches
                else:
                    tag_match[key] = cleaned_matches[0]
                    
        return tag_match if tag_match.keys() else None

    def _inject_ids(self, data_list, prefix):
        copy_data = data_list.copy()
        if isinstance(copy_data, list):
            for i, item in enumerate(copy_data):
                if isinstance(item, dict) and "id" not in item:
                    item["id"] = (
                        f"{prefix}_{int(time.time())}_{i}_{str(uuid.uuid4())[:4]}"
                    )
        return copy_data

    def _normalize_name(self, value: Optional[str]) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", "", str(value)).strip().lower()

    def _collect_project_assets(self):
        assets = {"characters": [], "scenes": []}
        if not self.episode or not getattr(self.episode, "project", None):
            return assets

        seen_char_ids = set()
        seen_scene_ids = set()
        seen_char_names = set()
        seen_scene_names = set()

        for ep in self.episode.project.episodes:
            if not ep.ai_config or "generated_script" not in ep.ai_config:
                continue
            script = ep.ai_config.get("generated_script", {})

            for char in script.get("characters", []) or []:
                if not isinstance(char, dict):
                    continue
                char_id = str(char.get("id") or "").strip()
                char_name = self._normalize_name(char.get("name"))
                if char_id and char_id in seen_char_ids:
                    continue
                if not char_id and char_name and char_name in seen_char_names:
                    continue
                assets["characters"].append(char)
                if char_id:
                    seen_char_ids.add(char_id)
                if char_name:
                    seen_char_names.add(char_name)

            for scene in script.get("scenes", []) or []:
                if not isinstance(scene, dict):
                    continue
                scene_id = str(scene.get("id") or "").strip()
                scene_name = self._normalize_name(scene.get("location_name"))
                if scene_id and scene_id in seen_scene_ids:
                    continue
                if not scene_id and scene_name and scene_name in seen_scene_names:
                    continue
                assets["scenes"].append(scene)
                if scene_id:
                    seen_scene_ids.add(scene_id)
                if scene_name:
                    seen_scene_names.add(scene_name)

        return assets

    def _merge_with_existing(self, items, existing_items, name_key: str):
        if not isinstance(items, list):
            return items

        existing_by_id = {}
        existing_by_name = {}
        for item in existing_items or []:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if item_id:
                existing_by_id[str(item_id)] = item
            name_val = item.get(name_key) or item.get("name")
            name_norm = self._normalize_name(name_val)
            if name_norm:
                existing_by_name[name_norm] = item

        merged = []
        for item in items:
            if not isinstance(item, dict):
                continue
            match = None
            item_id = item.get("id")
            if item_id and str(item_id) in existing_by_id:
                match = existing_by_id[str(item_id)]
            else:
                name_val = item.get(name_key) or item.get("name")
                name_norm = self._normalize_name(name_val)
                if name_norm and name_norm in existing_by_name:
                    match = existing_by_name[name_norm]

            if match:
                # 复用已存在对象，绝不修改其字段
                merged.append(match)
            else:
                merged.append(item)

        # Deduplicate merged list
        final_items = []
        seen_keys = set()
        for item in merged:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            name_val = item.get(name_key) or item.get("name")
            name_norm = self._normalize_name(name_val)
            key = str(item_id) if item_id else name_norm
            if key and key in seen_keys:
                continue
            if key:
                seen_keys.add(key)
            final_items.append(item)

        return final_items

    def _merge_preserve_existing(self, existing_items, new_items, name_key: str):
        """
        Keep all existing items, append only truly new items.
        Matching by id first, then normalized name.
        """
        if not isinstance(existing_items, list):
            existing_items = []
        if not isinstance(new_items, list):
            return existing_items

        merged = list(existing_items)
        existing_ids = set()
        existing_names = set()

        for item in existing_items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if item_id:
                existing_ids.add(str(item_id))
            name_val = item.get(name_key) or item.get("name")
            name_norm = self._normalize_name(name_val)
            if name_norm:
                existing_names.add(name_norm)

        for item in new_items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            name_val = item.get(name_key) or item.get("name")
            name_norm = self._normalize_name(name_val)

            if item_id and str(item_id) in existing_ids:
                continue
            if name_norm and name_norm in existing_names:
                continue

            merged.append(item)
            if item_id:
                existing_ids.add(str(item_id))
            if name_norm:
                existing_names.add(name_norm)

        return merged

    def _submit(self, tool_name: str, final_output_accumulator: str):
        try:
            if not final_output_accumulator:
                raise ValueError(f"[{tool_name}] 模型未返回任何内容！")

            final_output_accumulator = strip_think_segments(final_output_accumulator)
            yield self._format_sse("status", f"[{tool_name}] 内容格式化...")

            # short_video_storyboard_maker"
            if tool_name == "short-video-storyboard-maker":
                json_match = self._get_json_block(text=final_output_accumulator)
                tag_match = self._get_tag_block(text=final_output_accumulator, tag_map={
                    "STORYBOARD": "storyboard",
                })
                if not tag_match:
                    raise ValueError(f"[{tool_name}] 模型未返回任何内容或格式错误！")
                if not json_match:
                    raise ValueError(f"[{tool_name}] 模型返回内容格式错误！")
                
                try:
                    parsed_data = json.loads(json_match)
                    if "storyboard" in parsed_data:
                        parsed_data["storyboard"] = self._inject_ids(parsed_data["storyboard"], "shot")
                    parsed_data = sanitize_think_payload(parsed_data)
                    json_match = json.dumps(parsed_data)
                except:
                    pass

                yield self._format_sse("finish", {"json": json_match})
                yield self._format_sse("status", "Completed")
                yield from self.save_episode(key="generated_script.storyboard", value=json.loads(json_match)["storyboard"], type='add')
                
            # short_video_screenwriter
            elif tool_name == "short-video-screenwriter":
                json_match = self._get_json_block(text=final_output_accumulator)
                tag_match = self._get_tag_block(text=final_output_accumulator, tag_map={
                    "META": "meta",
                    "OUTLINE": "outline",
                    "CHARACTERS": "characters",
                    "SCENES": "scenes",
                    "STORYBOARD": "storyboard",
                })
                if not tag_match:
                    raise ValueError(f"[{tool_name}] 模型未返回任何内容或格式错误！")
                if not json_match:
                    raise ValueError(f"[{tool_name}] 模型返回内容格式错误！")
                
                try:
                    parsed_data = json.loads(json_match)
                    # Merge characters/scenes with existing project assets
                    existing_assets = self._collect_project_assets()
                    existing_script = {}
                    if self.episode and self.episode.ai_config:
                        existing_script = self.episode.ai_config.get("generated_script", {}) or {}
                    if "characters" in parsed_data:
                        merged_chars = self._merge_with_existing(
                            parsed_data["characters"], existing_assets.get("characters", []), "name"
                        )
                        merged_chars = self._merge_preserve_existing(
                            existing_script.get("characters", []), merged_chars, "name"
                        )
                        parsed_data["characters"] = merged_chars
                    if "scenes" in parsed_data:
                        merged_scenes = self._merge_with_existing(
                            parsed_data["scenes"], existing_assets.get("scenes", []), "location_name"
                        )
                        merged_scenes = self._merge_preserve_existing(
                            existing_script.get("scenes", []), merged_scenes, "location_name"
                        )
                        parsed_data["scenes"] = merged_scenes
                    if "storyboard" in parsed_data:
                        merged_storyboard = self._merge_preserve_existing(
                            existing_script.get("storyboard", []), parsed_data["storyboard"], "action"
                        )
                        parsed_data["storyboard"] = merged_storyboard
                    if "characters" in parsed_data:
                        parsed_data["characters"] = self._inject_ids(parsed_data["characters"], "char")
                    if "scenes" in parsed_data:
                        parsed_data["scenes"] = self._inject_ids(parsed_data["scenes"], "scene")
                    if "storyboard" in parsed_data:
                        parsed_data["storyboard"] = self._inject_ids(parsed_data["storyboard"], "shot")
                    parsed_data = sanitize_think_payload(parsed_data)
                    json_match = json.dumps(parsed_data)
                except:
                    pass

                yield self._format_sse("finish", {"json": json_match})
                yield self._format_sse("status", "Completed")
                self.save_episode(key="generated_script", value=json.loads(json_match))
            
            # other tools
            else:
                yield self._format_sse("text_finish", {"text": strip_think_segments(final_output_accumulator)})

        except Exception as e:
            yield self._format_sse("error", f"{str(e)}")
    
    def save_episode(self, key: str, value: any, type: str = 'replace'):
        try:
            if not self.episode:
                raise ValueError("💾 无法保存剧集，剧本不存在.")

            value = sanitize_think_payload(value)
            current_config = self.episode.ai_config if self.episode.ai_config else {}
            key_path = key.split(".")

            def update_recursive(current_layer, remaining_keys):
                if isinstance(current_layer, dict):
                    new_layer = current_layer.copy()
                else:
                    new_layer = {}

                current_key = remaining_keys[0]
                is_target = len(remaining_keys) == 1

                if is_target:
                    if type == 'replace':
                        new_layer[current_key] = value
                    
                    elif type == 'add':
                        existing_val = new_layer.get(current_key)
                        items_to_add = value if isinstance(value, list) else [value]

                        if existing_val is None:
                            new_layer[current_key] = items_to_add
                        elif isinstance(existing_val, list):
                            new_list = list(existing_val)
                            new_list.extend(items_to_add)
                            new_layer[current_key] = new_list
                        else:
                            raise ValueError(f"类型错误: key '{key}' 对应的值不是数组，无法执行 'add' 操作.")
                    else:
                        raise ValueError(f"未知的操作类型: {type}")
                    
                    return new_layer
                
                else:
                    next_data = new_layer.get(current_key, {})
                    if next_data and not isinstance(next_data, dict):
                        raise ValueError(f"路径冲突: '{current_key}' 已经在配置中存在且不是字典，无法继续深入.")
                    new_layer[current_key] = update_recursive(next_data, remaining_keys[1:])
                    return new_layer

            new_root_config = update_recursive(current_config, key_path)

            self.episode.ai_config = new_root_config
            self.db.add(self.episode)
            self.db.commit()
            self.db.refresh(self.episode)
            
            action_text = "更新" if type == 'replace' else "追加"
            yield self._format_sse(
                "status", f"💾 剧本配置已{action_text}: {key}"
            )
            
        except Exception as e:
            yield self._format_sse(
                "error", f"保存失败: {str(e)}"
            )
