from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Project(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="projects")
    episodes = relationship("Episode", back_populates="project", cascade="all, delete-orphan")

class Episode(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    title = Column(String)
    status = Column(String, default="draft") # draft, generating, finished
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ai_config = Column(JSON, nullable=True)
    
    @property
    def duration(self):
        return "00:00"
    
    project = relationship("Project", back_populates="episodes")
    assets = relationship("Asset", back_populates="episode", cascade="all, delete-orphan")