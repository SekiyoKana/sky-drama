from typing import Optional
from pydantic import BaseModel

class ApiKeyBase(BaseModel):
    platform: str
    name: str
    base_url: Optional[str] = None
    text_endpoint: Optional[str] = "/chat/completions"
    image_endpoint: Optional[str] = "/images/generations"
    video_endpoint: Optional[str] = "/videos"
    video_fetch_endpoint: Optional[str] = '/videos/{task_id}'
    audio_endpoint: Optional[str] = None

class ApiKeyCreate(ApiKeyBase):
    key: Optional[str] = None  # Ollama 本地可不填

class ApiKeyUpdate(ApiKeyBase):
    key: Optional[str] = None # 更新时 Key 可选

class ApiKeyOut(ApiKeyBase):
    id: int
    masked_key: str 
    key: Optional[str] = None # 返回完整 Key (既然已经放弃加密，就满足前端回显需求)

    class Config:
        from_attributes = True
