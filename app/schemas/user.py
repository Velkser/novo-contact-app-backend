from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    role: str = "user"
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None