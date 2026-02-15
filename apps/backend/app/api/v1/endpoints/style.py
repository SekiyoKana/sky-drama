from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from pydantic import BaseModel
from datetime import datetime

from app.api import deps
from app.models.style import Style
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class StyleBase(BaseModel):
    name: str

class StyleCreate(StyleBase):
    pass

class StyleOut(StyleBase):
    id: int
    image_url: str
    created_at: datetime
    
    class Config:
        from_attributes = True

ASSETS_DIR = os.path.join(settings.ASSETS_DIR, "styles")
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

@router.get("/", response_model=List[StyleOut])
def read_style(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_user),
):
    templates = db.query(Style).filter(Style.user_id == current_user.id).offset(skip).limit(limit).all()
    return templates

@router.post("/", response_model=StyleOut)
async def create_style(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    
    import re
    safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
    file_name = f"temp_{safe_name}.png"
    file_path = os.path.join(ASSETS_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"/assets/styles/{file_name}"
    
    db_obj = Style(
        name=name,
        image_url=image_url,
        user_id=current_user.id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.delete("/{id}")
def delete_style(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    item = db.query(Style).filter(Style.id == id, Style.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Style template not found")
    
    try:
        if item.image_url.startswith("/assets/styles/"):
            filename = item.image_url.replace("/assets/styles/", "")
            file_path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        logger.info(f"Error deleting file: {e}")

    db.delete(item)
    db.commit()
    return {"status": "success"}

@router.put("/{id}", response_model=StyleOut)
def update_style(
    id: int,
    name: str = Form(None),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    item = db.query(Style).filter(Style.id == id, Style.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Style template not found")
    
    if name:
        item.name = name
    
    db.commit()
    db.refresh(item)
    return item
