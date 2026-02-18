from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Dict, List, Optional, Set
import re
import logging
import os
import shutil
import uuid
from urllib.parse import urlparse
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel

from app.api import deps
from app.services.ai_engine import AIEngine
from app.models.apikey import ApiKey
from app.models.project import Episode
from app.models.asset import Asset
from app.models.style import Style
from app.core.config import settings
from app.core.director_trace import DirectorTrace
from app.core.provider_platform import (
    normalize_platform,
    resolve_base_url,
    requires_api_key,
)
from app.utils.http_client import request as http_request
from app.utils.ollama_client import list_ollama_models
from app.utils.think_filter import sanitize_think_payload, strip_think_segments

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateRequest(BaseModel):
    project_id: int
    episode_id: int
    prompt: str
    type: str = "text"
    skill: str = "short-video-screenwriter"
    data: Optional[dict] = None


class TestConnectionRequest(BaseModel):
    api_key_id: int


_MODEL_TYPES = ("text", "image", "video", "audio")


def _new_model_groups() -> Dict[str, List[str]]:
    return {k: [] for k in _MODEL_TYPES}


def _append_group(groups: Dict[str, List[str]], model_type: str, model_id: str):
    if model_type not in groups:
        return
    if model_id not in groups[model_type]:
        groups[model_type].append(model_id)


def _normalize_capability_token(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _collect_modalities(model_row: dict) -> Set[str]:
    tokens: Set[str] = set()
    for key in ("modality", "modalities", "input_modalities", "output_modalities"):
        val = model_row.get(key)
        if isinstance(val, str):
            token = _normalize_capability_token(val)
            if token:
                tokens.add(token)
        elif isinstance(val, list):
            for item in val:
                token = _normalize_capability_token(item)
                if token:
                    tokens.add(token)

    capabilities = model_row.get("capabilities")
    if isinstance(capabilities, dict):
        for k, v in capabilities.items():
            key_token = _normalize_capability_token(k)
            if isinstance(v, bool):
                if v:
                    tokens.add(key_token)
            elif isinstance(v, str):
                val_token = _normalize_capability_token(v)
                if val_token in {"true", "yes", "enabled", "supported"}:
                    tokens.add(key_token)
            elif isinstance(v, (int, float)):
                if v:
                    tokens.add(key_token)
    return tokens


def _infer_model_capabilities(platform: str, model_id: str, model_row: Optional[dict] = None) -> Set[str]:
    text_words = (
        "chat",
        "gpt",
        "claude",
        "deepseek",
        "qwen",
        "llama",
        "gemini",
        "doubao",
        "text",
        "instruct",
        "reasoner",
    )
    image_words = (
        "image",
        "vision",
        "flux",
        "sd",
        "stable_diffusion",
        "dall",
        "dalle",
        "seedream",
        "nano_banana",
        "recraft",
        "pixart",
        "cogview",
    )
    video_words = (
        "video",
        "sora",
        "seedance",
        "runway",
        "pika",
        "veo",
        "kling",
        "wanx",
        "hunyuan_video",
        "i2v",
        "t2v",
    )
    audio_words = (
        "audio",
        "speech",
        "tts",
        "voice",
        "whisper",
        "asr",
        "transcribe",
    )

    value = _normalize_capability_token(model_id)
    capabilities: Set[str] = set()

    if any(word in value for word in text_words):
        capabilities.add("text")
    if any(word in value for word in image_words):
        capabilities.add("image")
    if any(word in value for word in video_words):
        capabilities.add("video")
    if any(word in value for word in audio_words):
        capabilities.add("audio")

    if isinstance(model_row, dict):
        tokens = _collect_modalities(model_row)
        if any(tok in tokens for tok in {"text", "chat", "completion"}):
            capabilities.add("text")
        if any(tok in tokens for tok in {"image", "vision"}):
            capabilities.add("image")
        if "video" in tokens:
            capabilities.add("video")
        if any(tok in tokens for tok in {"audio", "speech", "tts", "asr", "transcription"}):
            capabilities.add("audio")

    if platform == "ollama":
        # Ollama /api/tags does not provide reliable capability metadata.
        capabilities.add("text")

    if not capabilities:
        capabilities.add("text")

    return capabilities


@router.post("/test-connection")
async def test_connection(
    req: TestConnectionRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    api_key_record = (
        db.query(ApiKey)
        .filter(ApiKey.id == req.api_key_id, ApiKey.user_id == current_user.id)
        .first()
    )

    if not api_key_record:
        raise HTTPException(status_code=404, detail="API Key not found")

    # 直接使用存储的 key (明文)
    real_key = str(api_key_record.encrypted_key)
    # try:
    #     real_key = decrypt_data(str(api_key_record.encrypted_key))
    # except Exception:
    #     raise HTTPException(status_code=500, detail="Key decryption failed")

    try:
        platform = normalize_platform(api_key_record.platform)
        base_url = resolve_base_url(platform, api_key_record.base_url)

        if requires_api_key(platform) and not real_key:
            raise HTTPException(status_code=400, detail="Auth failed: API Key is required")

        model_groups = _new_model_groups()
        model_capabilities: Dict[str, List[str]] = {}

        if platform == "ollama":
            available_models = list_ollama_models(base_url, real_key)
            for model_id in available_models:
                caps = sorted(_infer_model_capabilities(platform, model_id))
                model_capabilities[model_id] = caps
                for cap in caps:
                    _append_group(model_groups, cap, model_id)
        else:
            # Prefer raw HTTP for compatibility across OpenAI-compatible providers.
            headers = {"Content-Type": "application/json"}
            if real_key:
                headers["Authorization"] = f"Bearer {real_key}"

            models_res = http_request(
                "GET",
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=(10.0, 30.0),
            )
            if models_res.status_code != 200:
                raise RuntimeError(models_res.text)

            payload = models_res.json() if models_res.content else {}
            rows = payload.get("data", []) if isinstance(payload, dict) else []
            available_models = sorted(
                [str(model.get("id")) for model in rows if isinstance(model, dict) and model.get("id")]
            )
            for row in rows:
                if not isinstance(row, dict):
                    continue
                model_id = str(row.get("id") or "").strip()
                if not model_id:
                    continue
                caps = sorted(_infer_model_capabilities(platform, model_id, row))
                model_capabilities[model_id] = caps
                for cap in caps:
                    _append_group(model_groups, cap, model_id)

        # Keep deterministic order consistent with available_models
        for model_type in _MODEL_TYPES:
            ordered = [m for m in available_models if m in set(model_groups[model_type])]
            model_groups[model_type] = ordered

        return {
            "status": "success",
            "message": "Connection Successful",
            "models": available_models,
            "models_by_type": model_groups,
            "model_capabilities": model_capabilities,
        }

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            raise HTTPException(status_code=400, detail="Auth failed: Invalid API Key")
        elif "404" in error_msg:
            raise HTTPException(status_code=400, detail="Path error: Invalid Base URL")
        else:
            raise HTTPException(
                status_code=400, detail=f"Connection failed: {error_msg}"
            )


class UpdateScriptItemRequest(BaseModel):
    episode_id: int
    item_id: str
    updates: dict


class DeleteScriptItemRequest(BaseModel):
    episode_id: int
    item_id: str


def _normalize_asset_url(url: str) -> str:
    if not url:
        return ""
    text = str(url).strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        try:
            parsed = urlparse(text)
            return parsed.path or ""
        except Exception:
            return text
    return text


@router.post("/script/delete_item")
async def delete_script_item(
    req: DeleteScriptItemRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    episode = db.query(Episode).filter(Episode.id == req.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    if not episode.ai_config or "generated_script" not in episode.ai_config:
        raise HTTPException(status_code=404, detail="No script found for this episode")

    import copy

    current_config = copy.deepcopy(dict(episode.ai_config))
    script_data = current_config["generated_script"]
    found = False

    def remove_from_list(data_list):
        nonlocal found
        if not isinstance(data_list, list):
            return
        initial_len = len(data_list)
        # Filter out the item with the given ID
        data_list[:] = [item for item in data_list if isinstance(item, dict) and item.get("id") != req.item_id]
        if len(data_list) < initial_len:
            found = True

    if "characters" in script_data:
        remove_from_list(script_data["characters"])
    if not found and "scenes" in script_data:
        remove_from_list(script_data["scenes"])
    if not found and "storyboard" in script_data:
        remove_from_list(script_data["storyboard"])

    if not found:
        raise HTTPException(
            status_code=404, detail=f"Item with id {req.item_id} not found"
        )

    episode.ai_config = current_config
    flag_modified(episode, "ai_config")

    db.add(episode)
    db.commit()
    db.refresh(episode)

    return {"status": "success", "message": "Item deleted", "item_id": req.item_id}


@router.post("/script/update_item")
async def update_script_item(
    req: UpdateScriptItemRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    episode = db.query(Episode).filter(Episode.id == req.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    if not episode.ai_config or "generated_script" not in episode.ai_config:
        raise HTTPException(status_code=404, detail="No script found for this episode")

    import copy

    current_config = copy.deepcopy(dict(episode.ai_config))
    script_data = current_config["generated_script"]
    found = False
    sanitized_updates = sanitize_think_payload(req.updates or {})

    def update_in_list(data_list):
        nonlocal found
        if not isinstance(data_list, list):
            return
        for item in data_list:
            if isinstance(item, dict) and item.get("id") == req.item_id:
                item.update(sanitized_updates)
                found = True
                return

    if "characters" in script_data:
        update_in_list(script_data["characters"])
    if not found and "scenes" in script_data:
        update_in_list(script_data["scenes"])
    if not found and "storyboard" in script_data:
        update_in_list(script_data["storyboard"])

    if not found:
        raise HTTPException(
            status_code=404, detail=f"Item with id {req.item_id} not found"
        )

    episode.ai_config = current_config
    flag_modified(episode, "ai_config")

    db.add(episode)
    db.commit()
    db.refresh(episode)

    return {"status": "success", "message": "Item updated", "item_id": req.item_id}


@router.get("/script/storyboard_prompts")
async def get_storyboard_prompts(
    episode_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    script_data = {}
    if episode.ai_config and "generated_script" in episode.ai_config:
        script_data = episode.ai_config.get("generated_script") or {}

    storyboard = script_data.get("storyboard") if isinstance(script_data, dict) else None
    if not isinstance(storyboard, list):
        return {"status": "success", "records": {}}

    video_config = {}
    if isinstance(episode.ai_config, dict):
        raw_video_config = episode.ai_config.get("video")
        if isinstance(raw_video_config, dict):
            video_config = raw_video_config

    storyboard_refs = []
    image_urls: Set[str] = set()
    video_urls: Set[str] = set()
    for idx, item in enumerate(storyboard):
        if not isinstance(item, dict):
            continue
        image_url_raw = str(item.get("image_url") or "").strip()
        video_url_raw = str(item.get("video_url") or "").strip()
        image_url_norm = _normalize_asset_url(image_url_raw)
        video_url_norm = _normalize_asset_url(video_url_raw)
        image_url = image_url_norm if image_url_norm.startswith("/assets/") else image_url_raw
        video_url = video_url_norm if video_url_norm.startswith("/assets/") else video_url_raw
        image_asset_url = image_url_norm if image_url_norm.startswith("/assets/") else ""
        video_asset_url = video_url_norm if video_url_norm.startswith("/assets/") else ""
        if image_asset_url:
            image_urls.add(image_asset_url)
        if video_asset_url:
            video_urls.add(video_asset_url)
        item_id = str(item.get("id") or f"storyboard_{idx}")
        fallback_prompt = str(
            item.get("video_generation_prompt")
            or item.get("visual_prompt")
            or item.get("action")
            or ""
        )
        storyboard_refs.append(
            {
                "item_id": item_id,
                "image_url": image_url,
                "image_asset_url": image_asset_url,
                "video_url": video_url,
                "video_asset_url": video_asset_url,
                "fallback_prompt": fallback_prompt,
            }
        )

    all_urls = set(image_urls) | set(video_urls)
    assets = []
    if all_urls:
        assets = (
            db.query(Asset)
            .filter(
                Asset.episode_id == episode_id,
                Asset.url.in_(list(all_urls)),
                Asset.type.in_(["image", "video"]),
            )
            .all()
        )

    def _video_request_prompt(meta_data: dict) -> str:
        text = (
            meta_data.get("video_request_prompt")
            or meta_data.get("prompt")
            or meta_data.get("provider_prompt")
            or ""
        )
        return str(sanitize_think_payload(text) if text else "")

    image_assets: Dict[str, Asset] = {}
    video_assets: Dict[str, Asset] = {}
    for asset in assets:
        if asset.type == "image":
            prev = image_assets.get(asset.url)
            if prev is None or asset.id > prev.id:
                image_assets[asset.url] = asset
        elif asset.type == "video":
            prev = video_assets.get(asset.url)
            if prev is None or asset.id > prev.id:
                video_assets[asset.url] = asset

    records = {}
    for ref in storyboard_refs:
        key = str(ref.get("item_id") or "").strip()
        if not key:
            continue

        image_asset_url = str(ref.get("image_asset_url") or "")
        video_asset_url = str(ref.get("video_asset_url") or "")
        image_asset = image_assets.get(image_asset_url) if image_asset_url else None
        video_asset = video_assets.get(video_asset_url) if video_asset_url else None

        image_meta = (
            image_asset.meta_data
            if image_asset and isinstance(image_asset.meta_data, dict)
            else {}
        )
        video_meta = (
            video_asset.meta_data
            if video_asset and isinstance(video_asset.meta_data, dict)
            else {}
        )

        video_prompt = _video_request_prompt(video_meta)
        if not video_prompt:
            resolved_fallback = AIEngine.resolve_prompt_tags(
                str(ref.get("fallback_prompt") or ""),
                script_data,
                text_mode=False,
            )
            video_prompt = AIEngine.build_video_request_prompt(resolved_fallback, video_config)
        style_image_url = str(image_meta.get("style_image_url") or "")
        records[key] = {
            "item_id": key,
            "video_prompt": video_prompt,
            "style_image_url": style_image_url,
            "image_url": str(ref.get("image_url") or ""),
            "video_url": str(ref.get("video_url") or ""),
        }

    return {"status": "success", "records": records}


@router.post("/upload-reference")
async def upload_reference_image(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    current_user=Depends(deps.get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    safe_ext = os.path.splitext(file.filename)[1].lower()
    if safe_ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        safe_ext = ".png"

    subdir = "references"
    if category in {"character", "scene"}:
        subdir = f"references/{category}"

    assets_dir = os.path.join(settings.ASSETS_DIR, subdir)
    os.makedirs(assets_dir, exist_ok=True)

    filename = f"ref_{uuid.uuid4().hex}{safe_ext}"
    file_path = os.path.join(assets_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/assets/{subdir}/{filename}"
    return {"url": image_url}


@router.post("/generate")
async def generate_content(
    req: GenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    episode = db.query(Episode).filter(Episode.id == req.episode_id).first()

    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    req.prompt = strip_think_segments(req.prompt or "")

    # --- Prompt Resolution Logic ---
    if episode.ai_config and "generated_script" in episode.ai_config:
        script_data = episode.ai_config["generated_script"]
        characters = script_data.get("characters", [])
        scenes = script_data.get("scenes", [])
        referenced_images = []

        if req.type != "text":
            matches = re.finditer(
                r"\{\{(char|character|scene)_([a-zA-Z0-9_]+)\}\}", req.prompt
            )
            for match in matches:
                tag_type = match.group(1)
                tag_suffix = match.group(2)

                if tag_type == "character":
                    tag_type = "char"

                possible_ids = [tag_suffix]
                possible_ids.append(f"{tag_type}_{tag_suffix}")

                item = None
                if tag_type == "char":
                    item = next(
                        (c for c in characters if str(c.get("id")) in possible_ids),
                        None,
                    )
                elif tag_type == "scene":
                    item = next(
                        (s for s in scenes if str(s.get("id")) in possible_ids), None
                    )

                if item:
                    if not item.get("image_url"):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Referenced {tag_type} '{item.get('name') or item.get('location_name')}' does not have a generated image yet. Please generate it first.",
                        )
                    referenced_images.append(item.get("image_url"))

        req.prompt = AIEngine.resolve_prompt_tags(
            req.prompt,
            script_data,
            text_mode=req.type == "text",
        )

        if req.type != "text" and referenced_images:
            if req.data is None:
                req.data = {}
            req.data["reference_images"] = referenced_images
            if "image" not in req.data and len(referenced_images) > 0:
                req.data["image"] = referenced_images[0]
            if "input_reference" not in req.data and len(referenced_images) > 0:
                req.data["input_reference"] = referenced_images[0]

    req_data = req.data if isinstance(req.data, dict) else {}
    trace_id = str(req_data.get("trace_id") or uuid.uuid4().hex)
    if isinstance(req.data, dict):
        req.data.pop("trace_id", None)
    trace = DirectorTrace(run_id=trace_id)
    trace.start(
        {
            "user_id": getattr(current_user, "id", None),
            "project_id": req.project_id,
            "episode_id": req.episode_id,
            "type": req.type,
            "skill": req.skill,
            "prompt_length": len(req.prompt or ""),
            "prompt_preview": (req.prompt or "")[:240],
            "data_keys": sorted(list(req_data.keys())),
        }
    )

    engine = AIEngine(db, current_user, episode.ai_config)
    engine.set_context(episode)
    engine.set_trace(trace)

    style_id = None
    if episode.ai_config and episode.ai_config.get("style", None) and episode.ai_config["style"].get("id"):
        style_id = episode.ai_config["style"]["id"]

    style = db.query(Style).filter(Style.id == style_id).first() if style_id else None

    if req.type == "text":
        project_name = episode.project.name if episode.project else "未知项目"
        episode_title = episode.title if episode.title is not None else "未知章节"
        full_title = f"{project_name} - {episode_title}"

        logger.info(
            f"\n--- [Backend Debug] Generate Request Prompt ({req.skill}) ---\n{req.prompt}\n----------------------------------------------------\n"
        )

        kwargs = {}
        if req.data:
            kwargs.update(req.data)

        stream_gen = engine.generate_stream(
            tool_name=req.skill,
            prompt=req.prompt,
            title=full_title,
            description=req.prompt,
            **kwargs,
        )
    else:
        logger.info(
            f"\n--- [Backend Debug] Generate Request Prompt ({req.type}) ---\n{req.prompt}\n----------------------------------------------------\n"
        )
        stream_gen = engine.generate_media_stream(
            media_type=req.type,
            prompt=req.prompt,
            data=req.data if req.data else None,
            style=style
        )

    def trace_stream():
        try:
            yield engine._format_sse(
                "trace",
                {
                    "run_id": trace.run_id,
                    "status": "running",
                    "started_at": trace.record.get("started_at"),
                },
            )
            for chunk in stream_gen:
                yield chunk

            trace.finish(status="error" if trace.has_errors() else "completed")
        except GeneratorExit:
            trace.finish(status="aborted", error="Client disconnected")
            return
        except Exception as e:
            trace.finish(status="error", error=str(e))
            raise

    return StreamingResponse(trace_stream(), media_type="text/event-stream")
