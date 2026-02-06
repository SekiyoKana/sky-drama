from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship

class History(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    action = Column(String) # 'create_project', 'generate_video', 'delete_asset'
    target_id = Column(Integer, nullable=True) # 关联的对象ID
    params = Column(JSON) # 记录当时的参数 (Prompt, Model, Seed等)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="history")