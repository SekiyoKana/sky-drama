from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.session import SessionLocal # 👈 引用你配置数据库连接的地方
from app.core.config import settings    # 👈 引用你的配置(SECRET_KEY等)
from app.models.user import User        # 👈 引用你的User模型

# 1. 定义 OAuth2 规范
# 这告诉 FastAPI：去请求头里找 "Authorization: Bearer <token>"
# tokenUrl 指向你的登录接口地址 (用于 Swagger UI 自动通过该地址获取 Token)
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

# 2. 数据库依赖 (Yield 模式)
def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close() # 请求结束后自动关闭连接，防泄漏

# 3. 用户鉴权依赖 (核心安全逻辑)
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    这个函数会作为依赖注入到其他 API 接口中。
    它负责：解析 Token -> 拿 User ID -> 查数据库 -> 返回 User 对象
    """
    try:
        # 解码 JWT
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub") # 通常 sub 存的是 user_id
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 查库获取用户
    user = db.query(User).filter(User.id == token_data).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user