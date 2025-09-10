# app/api/v1/endpoints/contacts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.models.contact import Contact, ContactDialog, DialogMessage
from app.schemas.contact import ContactCreate, ContactUpdate, Contact as ContactSchema
from app.schemas.contact import ContactDialog as ContactDialogSchema
from app.crud.contact import (
    get_contact, get_contacts, create_contact, 
    update_contact, delete_contact
)
import json
from datetime import datetime

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.get("/", response_model=List[ContactSchema])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка контактов пользователя"""
    contacts = get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
    
    # Преобразуем теги для ответа
    result = []
    for contact in contacts:
        contact_dict = contact.__dict__.copy()
        contact_dict['tags'] = contact.get_tags()
        result.append(contact_dict)
    
    return result

@router.post("/", response_model=ContactSchema, status_code=status.HTTP_201_CREATED)
def create_contact_endpoint(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание нового контакта"""
    db_contact = create_contact(db=db, contact=contact, user_id=current_user.id)
    
    # Преобразуем теги для ответа
    contact_dict = db_contact.__dict__.copy()
    contact_dict['tags'] = db_contact.get_tags()
    
    return contact_dict

@router.get("/{contact_id}", response_model=ContactSchema)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретного контакта"""
    db_contact = get_contact(db, contact_id=contact_id, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Преобразуем теги и диалоги для ответа
    contact_dict = db_contact.__dict__.copy()
    contact_dict['tags'] = db_contact.get_tags()
    
    # Получаем диалоги контакта
    dialogs = db.query(ContactDialog).filter(
        ContactDialog.contact_id == contact_id
    ).all()
    
    # Преобразуем диалоги и сообщения
    dialogs_list = []
    for dialog in dialogs:
        # Получаем сообщения диалога
        messages = db.query(DialogMessage).filter(
            DialogMessage.dialog_id == dialog.id
        ).order_by(DialogMessage.timestamp.asc()).all()
        
        # Преобразуем сообщения
        messages_list = [
            {
                "role": msg.role,
                "text": msg.text,
                "timestamp": msg.timestamp
            } for msg in messages
        ]
        
        dialogs_list.append({
            "id": dialog.id,
            "contact_id": dialog.contact_id,
            "date": dialog.date,
            "transcript": dialog.transcript,
            "messages": messages_list
        })
    
    contact_dict['dialogs'] = dialogs_list
    
    return contact_dict

@router.put("/{contact_id}", response_model=ContactSchema)
def update_contact_endpoint(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Обновление контакта"""
    db_contact = update_contact(
        db=db, 
        contact_id=contact_id, 
        contact_update=contact, 
        user_id=current_user.id
    )
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Преобразуем теги для ответа
    contact_dict = db_contact.__dict__.copy()
    contact_dict['tags'] = db_contact.get_tags()
    
    return contact_dict

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_endpoint(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление контакта (soft delete)"""
    success = delete_contact(
        db=db, 
        contact_id=contact_id, 
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return

# Диалоги
@router.post("/{contact_id}/dialogs", response_model=ContactDialogSchema)
def add_dialog(
    contact_id: int,
    messages: List[Dict[str, str]],  # [{"role": "agent", "text": "Hello"}, ...]
    transcript: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Добавление диалога к контакту"""
    # Проверяем существование контакта
    contact = get_contact(db, contact_id=contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        # Создаем диалог
        dialog = ContactDialog(
            contact_id=contact_id,
            date=datetime.utcnow(),
            transcript=transcript
        )
        db.add(dialog)
        db.commit()
        db.refresh(dialog)
        
        # Добавляем сообщения
        for msg_data in messages:
            message = DialogMessage(
                dialog_id=dialog.id,
                role=msg_data['role'],
                text=msg_data['text']
            )
            db.add(message)
        
        db.commit()
        db.refresh(dialog)
        
        # Получаем сообщения для ответа
        db_messages = db.query(DialogMessage).filter(
            DialogMessage.dialog_id == dialog.id
        ).order_by(DialogMessage.timestamp.asc()).all()
        
        messages_list = [
            {
                "role": msg.role,
                "text": msg.text,
                "timestamp": msg.timestamp
            } for msg in db_messages
        ]
        
        return {
            "id": dialog.id,
            "contact_id": dialog.contact_id,
            "date": dialog.date,
            "transcript": dialog.transcript,
            "messages": messages_list
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add dialog: {str(e)}")

@router.get("/{contact_id}/dialogs", response_model=List[ContactDialogSchema])
def get_dialogs(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение всех диалогов контакта"""
    # Проверяем существование контакта
    contact = get_contact(db, contact_id=contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Получаем диалоги
    dialogs = db.query(ContactDialog).filter(
        ContactDialog.contact_id == contact_id
    ).order_by(ContactDialog.date.desc()).all()
    
    # Преобразуем диалоги и сообщения для ответа
    result = []
    for dialog in dialogs:
        # Получаем сообщения диалога
        messages = db.query(DialogMessage).filter(
            DialogMessage.dialog_id == dialog.id
        ).order_by(DialogMessage.timestamp.asc()).all()
        
        # Преобразуем сообщения
        messages_list = [
            {
                "role": msg.role,
                "text": msg.text,
                "timestamp": msg.timestamp
            } for msg in messages
        ]
        
        result.append({
            "id": dialog.id,
            "contact_id": dialog.contact_id,
            "date": dialog.date,
            "transcript": dialog.transcript,
            "messages": messages_list
        })
    
    return result