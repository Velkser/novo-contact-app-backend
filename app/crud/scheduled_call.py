# app/crud/scheduled_call.py
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.scheduled_call import ScheduledCall
from app.models.contact import Contact
from app.schemas.scheduled_call import ScheduledCallCreate, ScheduledCallUpdate
from datetime import datetime

def get_scheduled_call(db: Session, call_id: int, user_id: int) -> Optional[ScheduledCall]:
    return db.query(ScheduledCall).filter(
        ScheduledCall.id == call_id,
        ScheduledCall.user_id == user_id
    ).first()

def get_scheduled_calls(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ScheduledCall]:
    return db.query(ScheduledCall).filter(
        ScheduledCall.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_upcoming_calls(db: Session, user_id: int, limit: int = 10) -> List[ScheduledCall]:
    now = datetime.utcnow()
    return db.query(ScheduledCall).filter(
        ScheduledCall.user_id == user_id,
        ScheduledCall.status == "pending",
        ScheduledCall.scheduled_time > now if ScheduledCall.scheduled_time else True
    ).order_by(
        ScheduledCall.scheduled_time.asc() if ScheduledCall.scheduled_time else ScheduledCall.start_time_window.asc()
    ).limit(limit).all()

def create_scheduled_call(db: Session, call: ScheduledCallCreate, user_id: int) -> ScheduledCall:
    # Получаем контакт для проверки
    contact = db.query(Contact).filter(
        Contact.id == call.contact_id,
        Contact.user_id == user_id
    ).first()
    
    if not contact:
        raise ValueError("Contact not found")
    
    # Создаем звонок
    db_call = ScheduledCall(
        user_id=user_id,
        contact_id=call.contact_id,
        scheduled_time=call.scheduled_time,
        start_time_window=call.start_time_window,
        end_time_window=call.end_time_window,
        retry_until_success=call.retry_until_success or False,
        script=call.script,
        notes=call.notes,
        status="pending",
        call_attempts=0
    )
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

def update_scheduled_call(
    db: Session, 
    call_id: int, 
    call_update: ScheduledCallUpdate, 
    user_id: int
) -> Optional[ScheduledCall]:
    db_call = get_scheduled_call(db, call_id, user_id)
    if db_call:
        update_data = call_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_call, field, value)
        db_call.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_call)
    return db_call

def delete_scheduled_call(db: Session, call_id: int, user_id: int) -> bool:
    db_call = get_scheduled_call(db, call_id, user_id)
    if db_call:
        db.delete(db_call)
        db.commit()
        return True
    return False

def mark_call_as_attempted(db: Session, call_id: int, success: bool = False) -> Optional[ScheduledCall]:
    """Помечает звонок как попытанный и обновляет статистику"""
    db_call = db.query(ScheduledCall).filter(ScheduledCall.id == call_id).first()
    if db_call:
        db_call.call_attempts += 1
        db_call.last_attempt_at = datetime.utcnow()
        
        if success:
            db_call.status = "completed"
            db_call.next_retry_at = None
        else:
            db_call.status = "failed"
            # Если нужно повторять, устанавливаем время следующей попытки
            if db_call.retry_until_success:
                from datetime import timedelta
                db_call.next_retry_at = datetime.utcnow() + timedelta(hours=1)  # Повтор через 1 час
                db_call.status = "retrying"
            else:
                db_call.next_retry_at = None
        
        db.commit()
        db.refresh(db_call)
    return db_call

def get_calls_for_retry(db: Session, limit: int = 10) -> List[ScheduledCall]:
    """Получает звонки, которые нужно повторить"""
    now = datetime.utcnow()
    return db.query(ScheduledCall).filter(
        ScheduledCall.status == "retrying",
        ScheduledCall.next_retry_at <= now,
        ScheduledCall.call_attempts < 10  # Максимум 10 попыток
    ).limit(limit).all()