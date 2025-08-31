from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PromptTemplateBase(BaseModel):
    name: str
    content: str

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplateUpdate(PromptTemplateBase):
    pass

class PromptTemplate(PromptTemplateBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True