from datetime import datetime
from pydantic import BaseModel

class StyleBase(BaseModel):
  id: int
  user_id: int
  name : str
  image_url : str
  created_at : datetime