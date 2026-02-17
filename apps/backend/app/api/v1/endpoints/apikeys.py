from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.apikey import ApiKey
from app.models.user import User
from app.schemas.apikey import ApiKeyCreate, ApiKeyOut, ApiKeyUpdate
from app.core.provider_platform import (
    normalize_platform,
    resolve_base_url,
    resolve_endpoint,
    requires_api_key,
)

router = APIRouter()


def _mask_key(raw_key: str) -> str:
    key = str(raw_key or "")
    if len(key) >= 4:
        return "sk-****" + key[-4:]
    return "sk-****"


def _normalize_key_payload(
    platform: str,
    base_url: str,
    text_endpoint: str,
    image_endpoint: str,
    video_endpoint: str,
    video_fetch_endpoint: str,
    audio_endpoint: str,
):
    normalized_platform = normalize_platform(platform)
    return {
        "platform": normalized_platform,
        "base_url": resolve_base_url(normalized_platform, base_url),
        "text_endpoint": resolve_endpoint(
            normalized_platform, "text_endpoint", text_endpoint
        ),
        "image_endpoint": resolve_endpoint(
            normalized_platform, "image_endpoint", image_endpoint
        ),
        "video_endpoint": resolve_endpoint(
            normalized_platform, "video_endpoint", video_endpoint
        ),
        "video_fetch_endpoint": resolve_endpoint(
            normalized_platform, "video_fetch_endpoint", video_fetch_endpoint
        ),
        "audio_endpoint": resolve_endpoint(
            normalized_platform, "audio_endpoint", audio_endpoint
        ),
    }

@router.get("/", response_model=List[ApiKeyOut])
def read_apikeys(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    获取当前用户的所有 API Key (已脱敏)
    """
    keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
    
    # 手动处理脱敏逻辑
    results = []
    for k in keys:
        masked = _mask_key(k.encrypted_key)
            
        results.append(ApiKeyOut(
            id=k.id,
            platform=k.platform,
            name=k.name,
            base_url=k.base_url,
            text_endpoint=k.text_endpoint,
            image_endpoint=k.image_endpoint,
            video_endpoint=k.video_endpoint,
            video_fetch_endpoint=k.video_fetch_endpoint,
            audio_endpoint=k.audio_endpoint,
            masked_key=masked,
            key=k.encrypted_key # 返回完整 Key (存放在 encrypted_key 字段，但实际上是明文)
        ))
    return results

@router.post("/", response_model=ApiKeyOut)
def create_apikey(
    *,
    db: Session = Depends(deps.get_db),
    key_in: ApiKeyCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # 🔒 不再加密，直接存储明文
    # encrypted = encrypt_data(key_in.key)
    
    normalized_payload = _normalize_key_payload(
        platform=key_in.platform,
        base_url=key_in.base_url,
        text_endpoint=key_in.text_endpoint,
        image_endpoint=key_in.image_endpoint,
        video_endpoint=key_in.video_endpoint,
        video_fetch_endpoint=key_in.video_fetch_endpoint,
        audio_endpoint=key_in.audio_endpoint,
    )
    raw_key = key_in.key or ""
    if requires_api_key(normalized_payload["platform"]) and not raw_key:
        raise HTTPException(status_code=400, detail="API Key is required for this platform")

    new_key = ApiKey(
        user_id=current_user.id,
        platform=normalized_payload["platform"],
        name=key_in.name,
        base_url=normalized_payload["base_url"],
        encrypted_key=raw_key, # 存明文
        text_endpoint=normalized_payload["text_endpoint"],
        image_endpoint=normalized_payload["image_endpoint"],
        video_endpoint=normalized_payload["video_endpoint"],
        video_fetch_endpoint=normalized_payload["video_fetch_endpoint"],
        audio_endpoint=normalized_payload["audio_endpoint"],
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    return ApiKeyOut(
        id=new_key.id,
        platform=new_key.platform,
        name=new_key.name,
        base_url=new_key.base_url,
        text_endpoint=new_key.text_endpoint,
        image_endpoint=new_key.image_endpoint,
        video_endpoint=new_key.video_endpoint,
        video_fetch_endpoint=new_key.video_fetch_endpoint,
        audio_endpoint=new_key.audio_endpoint,
        masked_key=_mask_key(raw_key),
        key=raw_key # 返回完整 Key
    )

@router.put("/{id}", response_model=ApiKeyOut)
def update_apikey(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    key_in: ApiKeyUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    key = db.query(ApiKey).filter(ApiKey.id == id, ApiKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
        
    if key_in.key not in (None, ""):
        key.encrypted_key = key_in.key # 存明文

    normalized_payload = _normalize_key_payload(
        platform=key_in.platform,
        base_url=key_in.base_url,
        text_endpoint=key_in.text_endpoint,
        image_endpoint=key_in.image_endpoint,
        video_endpoint=key_in.video_endpoint,
        video_fetch_endpoint=key_in.video_fetch_endpoint,
        audio_endpoint=key_in.audio_endpoint,
    )

    key.platform = normalized_payload["platform"]
    key.name = key_in.name
    key.base_url = normalized_payload["base_url"]
    key.text_endpoint = normalized_payload["text_endpoint"]
    key.image_endpoint = normalized_payload["image_endpoint"]
    key.video_endpoint = normalized_payload["video_endpoint"]
    key.video_fetch_endpoint = normalized_payload["video_fetch_endpoint"]
    key.audio_endpoint = normalized_payload["audio_endpoint"]
    if requires_api_key(key.platform) and not key.encrypted_key:
        raise HTTPException(status_code=400, detail="API Key is required for this platform")
    
    db.commit()
    db.refresh(key)
    
    masked = _mask_key(key.encrypted_key)
    
    return ApiKeyOut(
        id=key.id,
        platform=key.platform,
        name=key.name,
        base_url=key.base_url,
        text_endpoint=key.text_endpoint,
        image_endpoint=key.image_endpoint,
        video_endpoint=key.video_endpoint,
        video_fetch_endpoint=key.video_fetch_endpoint,
        audio_endpoint=key.audio_endpoint,
        masked_key=masked,
        key=key.encrypted_key # 返回完整 Key
    )

@router.delete("/{id}")
def delete_apikey(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
):
    key = db.query(ApiKey).filter(ApiKey.id == id, ApiKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    db.delete(key)
    db.commit()
    return {"status": "success"}
