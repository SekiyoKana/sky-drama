from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Dict, List, Any

from app.api import deps
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagOut

router = APIRouter()

# ==========================================
# 1. 获取标签库 (CRUD: Read)
# ==========================================
@router.get("/", response_model=Dict[str, List[str]])
def read_tags(
    project_id: int = Query(0, description="当前项目ID"),
    episode_id: int = Query(0, description="当前剧集ID"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    获取可用标签库。
    逻辑：合并 [全局标签] + [当前项目标签] + [当前剧集标签]
    返回格式：{'Role': ['tag1', 'tag2'], ...}
    """
    # 构建查询条件
    # 1. 全局标签 (type=0)
    filters = [Tag.type == 0]
    
    # 2. 项目标签 (type=1 & ref_id=project_id)
    if project_id:
        filters.append(and_(Tag.type == 1, Tag.ref_id == project_id))
        
    # 3. 剧集标签 (type=2 & ref_id=episode_id)
    if episode_id:
        filters.append(and_(Tag.type == 2, Tag.ref_id == episode_id))
    
    # 执行查询 (OR 关系)
    tags = db.query(Tag).filter(or_(*filters)).all()
    
    # 格式化数据结构给前端
    result = {
        "Role": [], 
        "Shot": [], 
        "Style": [], 
        "Angle": [], 
        "Scene": []
    }
    
    # 动态分类填充
    for tag in tags:
        # 确保分类键存在 (处理数据库中可能存在的新分类)
        if tag.category not in result:
            result[tag.category] = []
            
        # 去重添加
        if tag.content not in result[tag.category]:
            result[tag.category].append(tag.content)
            
    return result

# ==========================================
# 2. 创建新标签 (CRUD: Create)
# ==========================================
@router.post("/", response_model=TagOut)
def create_tag(
    tag_in: TagCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    创建新标签。
    通常由前端在 TagLibPopover 中触发。
    """
    # 可选：检查是否已存在完全相同的标签以避免重复
    existing = db.query(Tag).filter(
        Tag.category == tag_in.category,
        Tag.content == tag_in.content,
        Tag.type == tag_in.type,
        Tag.ref_id == tag_in.ref_id
    ).first()
    
    if existing:
        return existing

    # 创建新对象
    db_obj = Tag(
        category=tag_in.category,
        content=tag_in.content,
        type=tag_in.type,
        ref_id=tag_in.ref_id
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# ==========================================
# 3. 晋升标签为全局 (New Feature)
# ==========================================
@router.put("/{tag_id}/promote", response_model=TagOut)
def promote_to_global(
    tag_id: int,
    db: Session = Depends(deps.get_db),
    # current_user = Depends(deps.get_current_superuser) # 建议：仅管理员可操作
) -> Any:
    """
    将指定的标签提升为全局标签。
    场景：当某个项目特有的标签非常好用，管理员希望所有项目都能看到它。
    操作：将 type 设为 0，ref_id 设为 0。
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    if tag.type == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag is already global"
        )

    # 执行晋升
    tag.type = 0
    tag.ref_id = 0 # 全局标签不依赖任何 ref
    
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    return tag

# ==========================================
# 4. 删除标签 (CRUD: Delete - 可选)
# ==========================================
@router.delete("/{tag_id}", response_model=TagOut)
def delete_tag(
    tag_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    删除标签
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    db.delete(tag)
    db.commit()
    return tag