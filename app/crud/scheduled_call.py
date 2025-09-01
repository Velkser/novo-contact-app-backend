from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.scheduled_call import ScheduledCall
from app.schemas.scheduled_call import ScheduledCallCreate, ScheduledCallUpdate

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
    from datetime import datetime
    return db.query(ScheduledCall).filter(
        ScheduledCall.user_id == user_id,
        ScheduledCall.scheduled_time > datetime.utcnow(),
        ScheduledCall.status == "pending"
    ).order_by(ScheduledCall.scheduled_time).limit(limit).all()

def create_scheduled_call(db: Session, call: ScheduledCallCreate, user_id: int) -> ScheduledCall:
    db_call = ScheduledCall(
        user_id=user_id,
        contact_id=call.contact_id,
        scheduled_time=call.scheduled_time,
        script=call.script,
        notes=call.notes,
        status="pending"
    )
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

def update_scheduled_call(
        db: Session, 
        call_id: int, 
        call_update: ScheduledCallUpdate,  # ← Тип аннотации
        user_id: int
    ) -> Optional[ScheduledCall]:
    db_call = get_scheduled_call(db, call_id, user_id)
    if db_call:
        # Используем exclude_unset=True для обновления только переданных полей
        update_data = call_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_call, field, value)
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