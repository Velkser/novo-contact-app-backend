# app/api/v1/endpoints/twilio_calls.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.models.contact import Contact
from app.services.twilio_service import twilio_service
from app.schemas.twilio_call import TwilioCallCreate, TwilioCallResponse, TwilioCallStatus
from app.crud.contact import get_contact

router = APIRouter(prefix="/twilio-calls", tags=["twilio_calls"])

@router.post("/initiate", response_model=TwilioCallResponse)
def initiate_call(
    call_data: TwilioCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Инициирует звонок через Twilio
    """
    # Получаем контакт
    contact = get_contact(db, contact_id=call_data.contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Используем скрипт из данных или из контакта
    script = call_data.script or contact.script
    if not script:
        raise HTTPException(status_code=400, detail="No script provided")
    
    # Совершаем звонок
    call_sid = twilio_service.make_call(
        to_number=contact.phone,
        script=script,
        contact_id=contact.id
    )
    
    if not call_sid:
        raise HTTPException(status_code=500, detail="Failed to initiate call")
    
    return TwilioCallResponse(
        call_sid=call_sid,
        status="initiated",
        message="Call initiated successfully"
    )

@router.post("/webhook")
async def twilio_webhook(request: Request):
    """
    Webhook для обработки событий от Twilio
    """
    try:
        # Получаем данные из формы
        form_data = await request.form()
        
        # Логируем событие
        print(f"Twilio webhook received: {dict(form_data)}")
        
        # Здесь можно добавить логику обработки событий
        # Например, сохранение статуса звонка в базу данных
        
        return Response(status_code=200)
        
    except Exception as e:
        print(f"Error processing Twilio webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/status")
async def call_status_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook для получения статуса звонка
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get('CallSid')
        call_status = form_data.get('CallStatus')
        
        print(f"Call {call_sid} status: {call_status}")
        
        # Здесь можно обновить статус звонка в базе данных
        
        return Response(status_code=200)
        
    except Exception as e:
        print(f"Error processing call status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{call_sid}/status", response_model=TwilioCallStatus)
def get_call_status(
    call_sid: str,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Получает статус звонка
    """
    # В реальной реализации здесь нужно получить статус из Twilio
    # или из базы данных
    
    return TwilioCallStatus(
        call_sid=call_sid,
        status="simulated",
        duration=None,
        recording_url=None
    )