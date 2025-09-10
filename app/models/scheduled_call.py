# app/models/scheduled_call.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ScheduledCall(Base):
    __tablename__ = "scheduled_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    
    # Поддержка обоих вариантов: конкретное время или временное окно
    scheduled_time = Column(DateTime, nullable=True)      # Конкретное время звонка
    start_time_window = Column(DateTime, nullable=True)   # Начало временного окна
    end_time_window = Column(DateTime, nullable=True)     # Конец временного окна
    
    retry_until_success = Column(Boolean, default=False)  # Повторять пока не дозвонимся
    script = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed, cancelled, retrying
    
    # Статистика звонков
    call_attempts = Column(Integer, default=0)           # Количество попыток звонка
    last_attempt_at = Column(DateTime, nullable=True)    # Время последней попытки
    next_retry_at = Column(DateTime, nullable=True)      # Время следующей попытки
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="scheduled_calls")
    contact = relationship("Contact", back_populates="scheduled_calls")