from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    has_completed_onboarding = Column(Boolean, default=False)

    # 关系定义
    api_keys = relationship("ApiKey", back_populates="owner", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="owner", cascade="all, delete-orphan")
    history = relationship("History", back_populates="owner", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    style = relationship("Style", back_populates="owner", cascade="all, delete-orphan")
