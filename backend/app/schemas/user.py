from typing import Optional
from pydantic import BaseModel, EmailStr

# 基础字段
class UserBase(BaseModel):
    email: EmailStr

# 注册时需要密码
class UserCreate(UserBase):
    password: str

# 数据库返回时包含 ID，但不包含密码
class UserOut(UserBase):
    id: int
    is_active: bool
    has_completed_onboarding: bool = False

    class Config:
        from_attributes = True