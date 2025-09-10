# app/schemas/group.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    contact_ids: Optional[List[int]] = []

class GroupUpdate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GroupMemberBase(BaseModel):
    group_id: int
    contact_id: int

class GroupMemberCreate(GroupMemberBase):
    pass

class GroupMember(GroupMemberBase):
    id: int
    added_at: datetime
    
    class Config:
        from_attributes = True

class GroupWithMembers(Group):
    members: List[GroupMember] = []
    contacts: List['Contact'] = []  # Будет определено позже
    
    class Config:
        from_attributes = True

class ScheduledGroupCallBase(BaseModel):
    group_id: int
    start_time_window: datetime
    end_time_window: datetime
    script: Optional[str] = None
    notes: Optional[str] = None
    retry_until_success: Optional[bool] = False
    retry_interval: Optional[int] = 60

class ScheduledGroupCallCreate(ScheduledGroupCallBase):
    pass

class ScheduledGroupCallUpdate(BaseModel):
    script: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    retry_until_success: Optional[bool] = None
    retry_interval: Optional[int] = None

class ScheduledGroupCall(ScheduledGroupCallBase):
    id: int
    user_id: int
    status: str
    call_attempts: int
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GroupResponse(GroupWithMembers):
    member_count: int = 0
    scheduled_calls_count: int = 0
    
    class Config:
        from_attributes = True

# Обновление импортов в конце файла
from app.schemas.contact import Contact
GroupWithMembers.update_forward_refs()