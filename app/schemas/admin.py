from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class AdminUserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True


class AdminUserCreate(AdminUserBase):
    password: str  # принимаем обычный пароль, хэшируем уже в сервисе


class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUser(AdminUserBase):
    id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
