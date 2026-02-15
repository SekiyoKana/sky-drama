from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.prompt import Prompt
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptOut

router = APIRouter()

@router.get("/", response_model=List[PromptOut])
def read_prompts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    type: str = None # 支持按类型筛选
) -> Any:
    query = db.query(Prompt).filter(Prompt.user_id == current_user.id)
    if type:
        query = query.filter(Prompt.type == type)
    return query.all()

@router.post("/", response_model=PromptOut)
def create_prompt(
    *,
    db: Session = Depends(deps.get_db),
    prompt_in: PromptCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    prompt = Prompt(
        user_id=current_user.id,
        title=prompt_in.title,
        content=prompt_in.content,
        type=prompt_in.type
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.delete("/{id}")
def delete_prompt(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
):
    p = db.query(Prompt).filter(Prompt.id == id, Prompt.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.delete(p)
    db.commit()
    return {"status": "success"}