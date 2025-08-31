from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связь с пользователем
    user = relationship("User", back_populates="prompt_templates")