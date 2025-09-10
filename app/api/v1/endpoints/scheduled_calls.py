# app/api/v1/endpoints/scheduled_calls.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.models.contact import Contact
from app.models.scheduled_call import ScheduledCall
from app.schemas.scheduled_call import (
    ScheduledCallCreate, 
    ScheduledCallUpdate, 
    ScheduledCallResponse
)
from app.crud.scheduled_call import (
    get_scheduled_call, 
    get_scheduled_calls, 
    create_scheduled_call, 
    update_scheduled_call, 
    delete_scheduled_call,
    get_upcoming_calls
)

router = APIRouter(prefix="/scheduled-calls", tags=["scheduled_calls"])

@router.get("/", response_model=List[ScheduledCallResponse])
def read_scheduled_calls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка запланированных звонков"""
    calls = get_scheduled_calls(db, user_id=current_user.id, skip=skip, limit=limit)
    
    # Добавляем информацию о контакте
    calls_with_contact_info = []
    for call in calls:
        contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
        if contact:
            calls_with_contact_info.append(ScheduledCallResponse(
                id=call.id,
                user_id=call.user_id,
                contact_id=call.contact_id,
                scheduled_time=call.scheduled_time,
                start_time_window=call.start_time_window,
                end_time_window=call.end_time_window,
                retry_until_success=call.retry_until_success,
                script=call.script,
                notes=call.notes,
                status=call.status,
                call_attempts=call.call_attempts,
                last_attempt_at=call.last_attempt_at,
                next_retry_at=call.next_retry_at,
                created_at=call.created_at,
                updated_at=call.updated_at,
                contact_name=contact.name,
                contact_phone=contact.phone,
                contact_company=contact.company
            ))
        else:
            calls_with_contact_info.append(ScheduledCallResponse(
                id=call.id,
                user_id=call.user_id,
                contact_id=call.contact_id,
                scheduled_time=call.scheduled_time,
                start_time_window=call.start_time_window,
                end_time_window=call.end_time_window,
                retry_until_success=call.retry_until_success,
                script=call.script,
                notes=call.notes,
                status=call.status,
                call_attempts=call.call_attempts,
                last_attempt_at=call.last_attempt_at,
                next_retry_at=call.next_retry_at,
                created_at=call.created_at,
                updated_at=call.updated_at,
                contact_name="Unknown",
                contact_phone="",
                contact_company=""
            ))
    
    return calls_with_contact_info

@router.post("/", response_model=ScheduledCallResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_call_endpoint(
    call_data: ScheduledCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание запланированного звонка"""
    try:
        new_call = create_scheduled_call(db=db, call=call_data, user_id=current_user.id)
        
        # Получаем информацию о контакте
        contact = db.query(Contact).filter(Contact.id == new_call.contact_id).first()
        
        if contact:
            return ScheduledCallResponse(
                id=new_call.id,
                user_id=new_call.user_id,
                contact_id=new_call.contact_id,
                scheduled_time=new_call.scheduled_time,
                start_time_window=new_call.start_time_window,
                end_time_window=new_call.end_time_window,
                retry_until_success=new_call.retry_until_success,
                script=new_call.script,
                notes=new_call.notes,
                status=new_call.status,
                call_attempts=new_call.call_attempts,
                last_attempt_at=new_call.last_attempt_at,
                next_retry_at=new_call.next_retry_at,
                created_at=new_call.created_at,
                updated_at=new_call.updated_at,
                contact_name=contact.name,
                contact_phone=contact.phone,
                contact_company=contact.company
            )
        else:
            return ScheduledCallResponse(
                id=new_call.id,
                user_id=new_call.user_id,
                contact_id=new_call.contact_id,
                scheduled_time=new_call.scheduled_time,
                start_time_window=new_call.start_time_window,
                end_time_window=new_call.end_time_window,
                retry_until_success=new_call.retry_until_success,
                script=new_call.script,
                notes=new_call.notes,
                status=new_call.status,
                call_attempts=new_call.call_attempts,
                last_attempt_at=new_call.last_attempt_at,
                next_retry_at=new_call.next_retry_at,
                created_at=new_call.created_at,
                updated_at=new_call.updated_at,
                contact_name="Unknown",
                contact_phone="",
                contact_company=""
            )
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming", response_model=List[ScheduledCallResponse])
def read_upcoming_calls(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение предстоящих звонков"""
    calls = get_upcoming_calls(db, user_id=current_user.id, limit=limit)
    
    # Добавляем информацию о контакте
    calls_with_contact_info = []
    for call in calls:
        contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
        if contact:
            calls_with_contact_info.append(ScheduledCallResponse(
                id=call.id,
                user_id=call.user_id,
                contact_id=call.contact_id,
                scheduled_time=call.scheduled_time,
                start_time_window=call.start_time_window,
                end_time_window=call.end_time_window,
                retry_until_success=call.retry_until_success,
                script=call.script,
                notes=call.notes,
                status=call.status,
                call_attempts=call.call_attempts,
                last_attempt_at=call.last_attempt_at,
                next_retry_at=call.next_retry_at,
                created_at=call.created_at,
                updated_at=call.updated_at,
                contact_name=contact.name,
                contact_phone=contact.phone,
                contact_company=contact.company
            ))
        else:
            calls_with_contact_info.append(ScheduledCallResponse(
                id=call.id,
                user_id=call.user_id,
                contact_id=call.contact_id,
                scheduled_time=call.scheduled_time,
                start_time_window=call.start_time_window,
                end_time_window=call.end_time_window,
                retry_until_success=call.retry_until_success,
                script=call.script,
                notes=call.notes,
                status=call.status,
                call_attempts=call.call_attempts,
                last_attempt_at=call.last_attempt_at,
                next_retry_at=call.next_retry_at,
                created_at=call.created_at,
                updated_at=call.updated_at,
                contact_name="Unknown",
                contact_phone="",
                contact_company=""
            ))
    
    return calls_with_contact_info

@router.get("/{call_id}", response_model=ScheduledCallResponse)
def read_scheduled_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретного запланированного звонка"""
    db_call = get_scheduled_call(db, call_id=call_id, user_id=current_user.id)
    if db_call is None:
        raise HTTPException(status_code=404, detail="Scheduled call not found")
    
    # Получаем информацию о контакте
    contact = db.query(Contact).filter(Contact.id == db_call.contact_id).first()
    
    if contact:
        return ScheduledCallResponse(
            id=db_call.id,
            user_id=db_call.user_id,
            contact_id=db_call.contact_id,
            scheduled_time=db_call.scheduled_time,
            start_time_window=db_call.start_time_window,
            end_time_window=db_call.end_time_window,
            retry_until_success=db_call.retry_until_success,
            script=db_call.script,
            notes=db_call.notes,
            status=db_call.status,
            call_attempts=db_call.call_attempts,
            last_attempt_at=db_call.last_attempt_at,
            next_retry_at=db_call.next_retry_at,
            created_at=db_call.created_at,
            updated_at=db_call.updated_at,
            contact_name=contact.name,
            contact_phone=contact.phone,
            contact_company=contact.company
        )
    else:
        return ScheduledCallResponse(
            id=db_call.id,
            user_id=db_call.user_id,
            contact_id=db_call.contact_id,
            scheduled_time=db_call.scheduled_time,
            start_time_window=db_call.start_time_window,
            end_time_window=db_call.end_time_window,
            retry_until_success=db_call.retry_until_success,
            script=db_call.script,
            notes=db_call.notes,
            status=db_call.status,
            call_attempts=db_call.call_attempts,
            last_attempt_at=db_call.last_attempt_at,
            next_retry_at=db_call.next_retry_at,
            created_at=db_call.created_at,
            updated_at=db_call.updated_at,
            contact_name="Unknown",
            contact_phone="",
            contact_company=""
        )

@router.put("/{call_id}", response_model=ScheduledCallResponse)
def update_scheduled_call_endpoint(
    call_id: int,
    call_update: ScheduledCallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Обновление запланированного звонка"""
    db_call = update_scheduled_call(
        db=db, 
        call_id=call_id, 
        call_update=call_update, 
        user_id=current_user.id
    )
    if db_call is None:
        raise HTTPException(status_code=404, detail="Scheduled call not found")
    
    # Получаем информацию о контакте
    contact = db.query(Contact).filter(Contact.id == db_call.contact_id).first()
    
    if contact:
        return ScheduledCallResponse(
            id=db_call.id,
            user_id=db_call.user_id,
            contact_id=db_call.contact_id,
            scheduled_time=db_call.scheduled_time,
            start_time_window=db_call.start_time_window,
            end_time_window=db_call.end_time_window,
            retry_until_success=db_call.retry_until_success,
            script=db_call.script,
            notes=db_call.notes,
            status=db_call.status,
            call_attempts=db_call.call_attempts,
            last_attempt_at=db_call.last_attempt_at,
            next_retry_at=db_call.next_retry_at,
            created_at=db_call.created_at,
            updated_at=db_call.updated_at,
            contact_name=contact.name,
            contact_phone=contact.phone,
            contact_company=contact.company
        )
    else:
        return ScheduledCallResponse(
            id=db_call.id,
            user_id=db_call.user_id,
            contact_id=db_call.contact_id,
            scheduled_time=db_call.scheduled_time,
            start_time_window=db_call.start_time_window,
            end_time_window=db_call.end_time_window,
            retry_until_success=db_call.retry_until_success,
            script=db_call.script,
            notes=db_call.notes,
            status=db_call.status,
            call_attempts=db_call.call_attempts,
            last_attempt_at=db_call.last_attempt_at,
            next_retry_at=db_call.next_retry_at,
            created_at=db_call.created_at,
            updated_at=db_call.updated_at,
            contact_name="Unknown",
            contact_phone="",
            contact_company=""
        )

@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_call_endpoint(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление запланированного звонка"""
    success = delete_scheduled_call(
        db=db, 
        call_id=call_id, 
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled call not found")
    return

# Добавляем endpoint для получения звонков контакта
@router.get("/contact/{contact_id}", response_model=List[ScheduledCallResponse])
def get_contact_scheduled_calls(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение всех запланированных звонков для контакта"""
    # Проверяем, что контакт принадлежит пользователю
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    calls = db.query(ScheduledCall).filter(
        ScheduledCall.contact_id == contact_id,
        ScheduledCall.user_id == current_user.id
    ).all()
    
    # Добавляем информацию о контакте
    calls_with_contact_info = []
    for call in calls:
        calls_with_contact_info.append(ScheduledCallResponse(
            id=call.id,
            user_id=call.user_id,
            contact_id=call.contact_id,
            scheduled_time=call.scheduled_time,
            start_time_window=call.start_time_window,
            end_time_window=call.end_time_window,
            retry_until_success=call.retry_until_success,
            script=call.script,
            notes=call.notes,
            status=call.status,
            call_attempts=call.call_attempts,
            last_attempt_at=call.last_attempt_at,
            next_retry_at=call.next_retry_at,
            created_at=call.created_at,
            updated_at=call.updated_at,
            contact_name=contact.name,
            contact_phone=contact.phone,
            contact_company=contact.company
        ))
    
    return calls_with_contact_info