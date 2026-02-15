from sqlalchemy import Column, Integer, String, Index, Text
from app.db.base import Base

class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # 例如: Role, Shot, Style, Angle, Scene
    content = Column(String(100), nullable=False)  # 标签内容，例如: 赛博朋克
    
    # type: 0=全局(Global), 1=项目(Project), 2=剧集(Episode)
    type = Column(Integer, default=0, index=True)
    
    # 关联ID: 如果type=0则为0，type=1则是project_id，type=2则是episode_id
    ref_id = Column(Integer, default=0, index=True)
    data = Column(Text, nullable=True)

    # 联合索引优化查询
    __table_args__ = (
        Index('idx_tag_type_ref', 'type', 'ref_id'),
    )