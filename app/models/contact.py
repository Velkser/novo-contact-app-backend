from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import json

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    company = Column(String, nullable=True)
    script = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON строка с тегами
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связь с пользователем
    user = relationship("User", back_populates="contacts")
    
    # Связь с диалогами
    dialogs = relationship("ContactDialog", back_populates="contact", cascade="all, delete-orphan")

    def get_tags(self):
        """Получение тегов как список"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []

    def set_tags(self, tags_list):
        """Установка тегов из списка"""
        if tags_list:
            self.tags = json.dumps(tags_list)
        else:
            self.tags = None

class ContactDialog(Base):
    __tablename__ = "contact_dialogs"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    date = Column(DateTime, default=func.now())
    transcript = Column(Text, nullable=True)  # Полный текст диалога
    
    # Связь с контактом
    contact = relationship("Contact", back_populates="dialogs")
    
    # Связь с сообщениями
    messages = relationship("DialogMessage", back_populates="dialog", cascade="all, delete-orphan")

class DialogMessage(Base):
    __tablename__ = "dialog_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    dialog_id = Column(Integer, ForeignKey("contact_dialogs.id"), nullable=False)
    role = Column(String, nullable=False)  # "agent" или "client"
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    
    # Связь с диалогом
    dialog = relationship("ContactDialog", back_populates="messages")