from pydantic import BaseModel
from typing import Optional

class TagBase(BaseModel):
    category: str
    content: str
    type: int = 0
    ref_id: int = 0
    data: Optional[str] = None

class TagCreate(TagBase):
    pass

class TagOut(TagBase):
    id: int

    class Config:
        from_attributes = True