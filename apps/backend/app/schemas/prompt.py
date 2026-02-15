from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class PromptBase(BaseModel):
    title: str
    content: str
    type: str = "text"

class PromptCreate(PromptBase):
    pass

class PromptOut(PromptBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True