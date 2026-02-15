from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api import deps
from app.models.user import User
from app.schemas.user import UserOut
from app.core import security

router = APIRouter()

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/me", response_model=UserOut)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get current user info
    """
    return current_user

@router.post("/me/onboarding", response_model=UserOut)
def complete_onboarding(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Mark onboarding as completed
    """
    current_user.has_completed_onboarding = True
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Change user password
    """
    if not security.verify_password(data.current_password, current_user.hashed_password):
        return {"status": "error", "message": "当前密码不正确"}
        
    current_user.hashed_password = security.get_password_hash(data.new_password)
    db.add(current_user)
    db.commit()
    
    return {"status": "success", "message": "密码修改成功"}