from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.schemas.scheduled_call import ScheduledCall, ScheduledCallCreate, ScheduledCallUpdate
from app.crud import scheduled_call as crud_call

router = APIRouter(prefix="/scheduled-calls", tags=["scheduled_calls"])

@router.get("/", response_model=List[ScheduledCall])
def read_scheduled_calls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка запланированных звонков"""
    calls = crud_call.get_scheduled_calls(db, user_id=current_user.id, skip=skip, limit=limit)
    return calls

@router.get("/upcoming", response_model=List[ScheduledCall])
def read_upcoming_calls(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение предстоящих звонков"""
    calls = crud_call.get_upcoming_calls(db, user_id=current_user.id, limit=limit)
    return calls

@router.post("/", response_model=ScheduledCall, status_code=status.HTTP_201_CREATED)
def create_scheduled_call(
    call: ScheduledCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание запланированного звонка"""
    return crud_call.create_scheduled_call(db=db, call=call, user_id=current_user.id)

@router.get("/{call_id}", response_model=ScheduledCall)
def read_scheduled_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретного запланированного звонка"""
    db_call = crud_call.get_scheduled_call(db, call_id=call_id, user_id=current_user.id)
    if db_call is None:
        raise HTTPException(status_code=404, detail="Scheduled call not found")
    return db_call

@router.put("/{call_id}", response_model=ScheduledCall)
def update_scheduled_call(
        call_id: int,
        call: ScheduledCallUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(deps.get_current_active_user)
    ):
    """Обновление запланированного звонка"""
    print(f"Received update request for call {call_id}")
    print(f"Update data: {call.dict(exclude_unset=True)}")
    print(f"User ID: {current_user.id}")
    
    try:
        db_call = crud_call.update_scheduled_call(
            db=db, 
            call_id=call_id, 
            call_update=call,
            user_id=current_user.id
        )
        if db_call is None:
            raise HTTPException(status_code=404, detail="Scheduled call not found")
        print(f"Successfully updated call {db_call.id}")
        return db_call
    except Exception as e:
        print(f"Error updating call: {str(e)}")
        raise

@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление запланированного звонка"""
    success = crud_call.delete_scheduled_call(
        db=db, 
        call_id=call_id, 
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled call not found")
    return