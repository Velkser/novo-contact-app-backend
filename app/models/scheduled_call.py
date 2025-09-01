from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ScheduledCall(Base):
    __tablename__ = "scheduled_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    script = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="scheduled_calls")
    contact = relationship("Contact", back_populates="scheduled_calls")