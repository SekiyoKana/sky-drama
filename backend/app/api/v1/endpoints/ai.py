from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import re
import logging
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
from openai import OpenAI

from app.api import deps
from app.services.ai_engine import AIEngine
from app.models.apikey import ApiKey
from app.models.project import Episode
from app.models.style import Style

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
        base_url = (
            str(api_key_record.base_url)
            if api_key_record.base_url is not None
            else "https://api.openai.com/v1"
        )
        client = OpenAI(api_key=real_key, base_url=base_url, timeout=10.0)

        response = client.models.list()
        available_models = [model.id for model in response.data]
        available_models.sort()

        return {
            "status": "success",
            "message": "Connection Successful",
            "models": available_models,
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

    def update_in_list(data_list):
        nonlocal found
        if not isinstance(data_list, list):
            return
        for item in data_list:
            if isinstance(item, dict) and item.get("id") == req.item_id:
                item.update(req.updates)
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


@router.post("/generate")
async def generate_content(
    req: GenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    episode = db.query(Episode).filter(Episode.id == req.episode_id).first()

    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # --- Prompt Resolution Logic ---
    if episode.ai_config and "generated_script" in episode.ai_config:
        script_data = episode.ai_config["generated_script"]
        characters = script_data.get("characters", [])
        scenes = script_data.get("scenes", [])
        # Helper to determine context based on prompt structure
        storyboard_marker = "[分镜列表]"
        storyboard_index = req.prompt.find(storyboard_marker)

        def replace_tag(match):
            tag_type = match.group(1)  # char or scene
            tag_suffix = match.group(2)  # The ID part after the prefix

            # Normalize tag_type 'character' to 'char'
            if tag_type == "character":
                tag_type = "char"

            # Construct possible IDs to check
            possible_ids = [tag_suffix]
            if tag_type == "char":
                possible_ids.append(f"char_{tag_suffix}")
            elif tag_type == "scene":
                possible_ids.append(f"scene_{tag_suffix}")

            # Check if this tag appears after [分镜列表]
            is_in_storyboard_list = False
            if storyboard_index != -1 and match.start() > storyboard_index:
                is_in_storyboard_list = True

            if tag_type == "char":
                # Find character
                char = next(
                    (c for c in characters if str(c.get("id")) in possible_ids), None
                )
                if char:
                    if req.type == "text":
                        return char.get("name", "未知角色")
                    elif is_in_storyboard_list:
                        return char.get("name", "未知角色")
                    else:
                        return f"[{char.get('name', '未知角色')}: {char.get('description', '')}]"
                return match.group(0)

            elif tag_type == "scene":
                scene = next(
                    (s for s in scenes if str(s.get("id")) in possible_ids), None
                )
                if scene:
                    if req.type == "text":
                        return scene.get("location_name", "未知场景")
                    elif is_in_storyboard_list:
                        return scene.get("location_name", "未知场景")
                    else:
                        return f"[{scene.get('location_name', '未知场景')}: {scene.get('mood', '')}]"
                return match.group(0)

            return match.group(0)
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

        req.prompt = re.sub(
            r"\{\{(char|character|scene)_([a-zA-Z0-9_]+)\}\}", replace_tag, req.prompt
        )

        if req.type != "text" and referenced_images:
            if req.data is None:
                req.data = {}
            req.data["reference_images"] = referenced_images
            if "image" not in req.data and len(referenced_images) > 0:
                req.data["image"] = referenced_images[0]
            if "input_reference" not in req.data and len(referenced_images) > 0:
                req.data["input_reference"] = referenced_images[0]

    engine = AIEngine(db, current_user, episode.ai_config)
    engine.set_context(episode)

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

    return StreamingResponse(stream_gen, media_type="text/event-stream")
