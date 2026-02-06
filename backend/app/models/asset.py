from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Asset(Base):
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episode.id"), nullable=False)
    chapter_id = Column(Integer, default=1) 
    
    type = Column(String) # 'image', 'video', 'audio', 'text'
    url = Column(String)  # 存储路径或 URL
    meta_data = Column(JSON, nullable=True) # 存宽度、高度、时长、Prompt备份
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    episode = relationship("Episode", back_populates="assets")