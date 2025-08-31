from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

class ContactBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    company: Optional[str] = None
    script: Optional[str] = None
    tags: Optional[List[str]] = []

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DialogMessage(BaseModel):
    role: str  # "agent" или "client"
    text: str
    timestamp: Optional[datetime] = None

class ContactDialog(BaseModel):
    id: int
    contact_id: int
    date: datetime
    transcript: Optional[str] = None
    messages: List[DialogMessage] = []
    
    class Config:
        from_attributes = True