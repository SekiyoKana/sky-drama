from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship

class Prompt(Base):
    __tablename__ = "prompt"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    title = Column(String, index=True)       # 指令标题
    content = Column(Text, nullable=False)   # 指令内容
    type = Column(String, default="text")    # text/image/video/audio
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="prompts")