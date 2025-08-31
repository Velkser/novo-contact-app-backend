from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.contact import Contact, ContactDialog, DialogMessage
from app.schemas.contact import ContactCreate, ContactUpdate
import json

def get_contact(db: Session, contact_id: int, user_id: int) -> Optional[Contact]:
    return db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == user_id,
        Contact.is_active == True
    ).first()

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
    return db.query(Contact).filter(
        Contact.user_id == user_id,
        Contact.is_active == True
    ).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: ContactCreate, user_id: int) -> Contact:
    db_contact = Contact(
        user_id=user_id,
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        company=contact.company,
        script=contact.script
    )
    # Устанавливаем теги
    if contact.tags:
        db_contact.set_tags(contact.tags)
    
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(
    db: Session, 
    contact_id: int, 
    contact_update: ContactUpdate, 
    user_id: int
) -> Optional[Contact]:
    db_contact = get_contact(db, contact_id, user_id)
    if db_contact:
        update_data = contact_update.dict(exclude_unset=True)
        
        # Обрабатываем теги отдельно
        if 'tags' in update_data:
            tags = update_data.pop('tags')
            db_contact.set_tags(tags)
        
        for field, value in update_data.items():
            setattr(db_contact, field, value)
        
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int, user_id: int) -> bool:
    db_contact = get_contact(db, contact_id, user_id)
    if db_contact:
        db_contact.is_active = False
        db.commit()
        return True
    return False

# Диалоги
def add_dialog(db: Session, contact_id: int, user_id: int, messages: List[dict], transcript: str = None) -> ContactDialog:
    # Проверяем, что контакт принадлежит пользователю
    contact = get_contact(db, contact_id, user_id)
    if not contact:
        return None
    
    # Создаем диалог
    dialog = ContactDialog(
        contact_id=contact_id,
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
    return dialog

def get_contact_dialogs(db: Session, contact_id: int, user_id: int) -> List[ContactDialog]:
    contact = get_contact(db, contact_id, user_id)
    if not contact:
        return []
    
    return db.query(ContactDialog).filter(
        ContactDialog.contact_id == contact_id
    ).all() 