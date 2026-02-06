from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.apikey import ApiKey
from app.models.user import User
from app.schemas.apikey import ApiKeyCreate, ApiKeyOut, ApiKeyUpdate

router = APIRouter()

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
        # 明文存储，直接脱敏
        if k.encrypted_key and len(str(k.encrypted_key)) >= 4:
            masked = "sk-****" + str(k.encrypted_key)[-4:]
        else:
            masked = "sk-****"
            
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
    
    new_key = ApiKey(
        user_id=current_user.id,
        platform=key_in.platform,
        name=key_in.name,
        base_url=key_in.base_url,
        encrypted_key=key_in.key, # 存明文
        text_endpoint=key_in.text_endpoint,
        image_endpoint=key_in.image_endpoint,
        video_endpoint=key_in.video_endpoint,
        video_fetch_endpoint=key_in.video_fetch_endpoint,
        audio_endpoint=key_in.audio_endpoint
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
        masked_key="sk-****" + key_in.key[-4:],
        key=key_in.key # 返回完整 Key
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
        
    if key_in.key:
        key.encrypted_key = key_in.key # 存明文
        
    key.platform = key_in.platform
    key.name = key_in.name
    key.base_url = key_in.base_url
    key.text_endpoint = key_in.text_endpoint
    key.image_endpoint = key_in.image_endpoint
    key.video_endpoint = key_in.video_endpoint
    key.video_fetch_endpoint = key_in.video_fetch_endpoint
    key.audio_endpoint = key_in.audio_endpoint
    
    db.commit()
    db.refresh(key)
    
    if key_in.key and len(key_in.key) >= 4:
        masked = "sk-****" + key_in.key[-4:]
    else:
        masked = "sk-****"
    
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