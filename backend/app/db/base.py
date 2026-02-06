from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: Any
    __name__: str

    # 自动生成表名：将类名转为小写 (例如 User -> user)
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()