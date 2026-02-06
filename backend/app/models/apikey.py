from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ApiKey(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    platform = Column(String) # 'openai', 'gemini'
    name = Column(String)     # 别名
    encrypted_key = Column(String, nullable=False) # 🔒 加密存储
    base_url = Column(String, nullable=True) # 支持自定义代理地址
    
    # 接口路径配置 (nullable=True, 使用默认值)
    text_endpoint = Column(String, default="/chat/completions", nullable=True)
    image_endpoint = Column(String, default="/images/generations", nullable=True)
    video_endpoint = Column(String, default="/videos", nullable=True)
    video_fetch_endpoint = Column(String, nullable=True) # 视频状态查询接口
    audio_endpoint = Column(String, nullable=True)

    owner = relationship("User", back_populates="api_keys")
