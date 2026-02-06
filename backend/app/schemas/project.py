from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class EpisodeBase(BaseModel):
    title: Optional[str] = None
    status: str = "Draft"
    ai_config: Optional[Dict[str, Any]] = None  

class EpisodeCreate(EpisodeBase):
    pass

class EpisodeUpdate(EpisodeBase):
    title: Optional[str] = None
    status: Optional[str] = None
    ai_config: Optional[Dict[str, Any]] = None

class EpisodeOut(EpisodeBase):
    id: int
    project_id: int
    duration: Optional[str] = "00:00"
    created_at: datetime
    ai_config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True