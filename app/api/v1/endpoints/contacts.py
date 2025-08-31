from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.schemas.contact import Contact, ContactCreate, ContactUpdate, ContactDialog
from app.crud import contact as crud_contact

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.get("/", response_model=List[Contact])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка контактов пользователя"""
    contacts = crud_contact.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
    # Преобразуем теги из строки в список для ответа
    for contact in contacts:
        contact.tags = contact.get_tags()
    return contacts

@router.post("/", response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание нового контакта"""
    db_contact = crud_contact.create_contact(db=db, contact=contact, user_id=current_user.id)
    # Преобразуем теги для ответа
    db_contact.tags = db_contact.get_tags()
    return db_contact

@router.get("/{contact_id}", response_model=Contact)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретного контакта"""
    db_contact = crud_contact.get_contact(db, contact_id=contact_id, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    # Преобразуем теги для ответа
    db_contact.tags = db_contact.get_tags()
    return db_contact

@router.put("/{contact_id}", response_model=Contact)
def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Обновление контакта"""
    db_contact = crud_contact.update_contact(
        db=db, 
        contact_id=contact_id, 
        contact_update=contact, 
        user_id=current_user.id
    )
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    # Преобразуем теги для ответа
    db_contact.tags = db_contact.get_tags()
    return db_contact

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление контакта (soft delete)"""
    success = crud_contact.delete_contact(
        db=db, 
        contact_id=contact_id, 
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return

# Диалоги
@router.post("/{contact_id}/dialogs", response_model=ContactDialog)
def add_dialog(
    contact_id: int,
    messages: List[dict],  # [{"role": "agent", "text": "Hello"}, ...]
    transcript: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Добавление диалога к контакту"""
    dialog = crud_contact.add_dialog(
        db=db,
        contact_id=contact_id,
        user_id=current_user.id,
        messages=messages,
        transcript=transcript
    )
    if dialog is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return dialog

@router.get("/{contact_id}/dialogs", response_model=List[ContactDialog])
def get_dialogs(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение всех диалогов контакта"""
    dialogs = crud_contact.get_contact_dialogs(
        db=db,
        contact_id=contact_id,
        user_id=current_user.id
    )
    return dialogs