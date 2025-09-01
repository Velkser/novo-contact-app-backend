# app/schemas/scheduled_call.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScheduledCallBase(BaseModel):
    contact_id: int
    scheduled_time: datetime
    script: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ScheduledCallCreate(ScheduledCallBase):
    pass

class ScheduledCallUpdate(BaseModel):
    # Делаем все поля необязательными для обновления
    contact_id: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    script: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ScheduledCall(ScheduledCallBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True