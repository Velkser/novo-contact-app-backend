# app/models/group.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import secrets

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="groups")
    group_members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    scheduled_group_calls = relationship("ScheduledGroupCall", back_populates="group", cascade="all, delete-orphan")

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    added_at = Column(DateTime, default=func.now())
    
    # Связи
    group = relationship("Group", back_populates="group_members")
    contact = relationship("Contact", back_populates="group_memberships")

class ScheduledGroupCall(Base):
    __tablename__ = "scheduled_group_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    
    # Добавлен недостающий столбец
    scheduled_time = Column(DateTime, nullable=True)      # Конкретное время звонка
    start_time_window = Column(DateTime, nullable=True)   # Начало временного окна
    end_time_window = Column(DateTime, nullable=True)     # Конец временного окна
    
    script = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed, cancelled, retrying
    call_attempts = Column(Integer, default=0)           # Количество попыток звонка
    last_attempt_at = Column(DateTime, nullable=True)    # Время последней попытки
    next_retry_at = Column(DateTime, nullable=True)      # Время следующей попытки
    retry_until_success = Column(Boolean, default=False)  # Повторять пока не дозвонимся
    retry_interval = Column(Integer, default=60)         # Интервал повторения в минутах
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="scheduled_group_calls")
    group = relationship("Group", back_populates="scheduled_group_calls")