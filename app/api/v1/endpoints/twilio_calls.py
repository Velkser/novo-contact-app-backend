from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import Optional
import logging
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.models.contact import Contact
from app.services.twilio_service import twilio_service
from app.crud.contact import get_contact, add_dialog
from app.schemas.twilio_call import TwilioCallCreate, TwilioCallResponse, TwilioCallStatus

router = APIRouter(prefix="/twilio-calls", tags=["twilio_calls"])
logger = logging.getLogger(__name__)

@router.post("/initiate", response_model=TwilioCallResponse)
def initiate_call(
    call_data: TwilioCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Инициирует звонок через Twilio (реальный звонок)
    """
    logger.info(f"📞 Initiating REAL call for user {current_user.id}, contact {call_data.contact_id}")
    
    # Получаем контакт
    contact = get_contact(db, contact_id=call_data.contact_id, user_id=current_user.id)
    if not contact:
        logger.warning(f"❌ Contact {call_data.contact_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Используем скрипт из данных или из контакта
    script = call_data.script or contact.script
    if not script:
        logger.warning(f"❌ No script provided for contact {contact.id}")
        raise HTTPException(status_code=400, detail="No script provided")
    
    # Проверяем наличие Twilio клиента
    if not twilio_service.client:
        logger.error("❌ Twilio service not initialized")
        raise HTTPException(status_code=500, detail="Twilio service not configured")
    
    # Совершаем реальный звонок через Twilio
    call_sid = twilio_service.make_call(
        to_number=contact.phone,
        script=script,
        contact_id=contact.id
    )
    
    if not call_sid:
        logger.error(f"❌ Failed to initiate REAL call to {contact.phone}")
        raise HTTPException(status_code=500, detail="Failed to initiate call")
    
    # Сохраняем диалог в базу данных
    try:
        messages = [
            {
                "role": "agent",
                "text": script
            }
        ]
        
        dialog = add_dialog(
            db=db,
            contact_id=contact.id,
            user_id=current_user.id,
            messages=messages,
            transcript=script
        )
        
        if dialog:
            logger.info(f"✅ Dialog saved to database. ID: {dialog.id}")
        else:
            logger.error("❌ Failed to save dialog to database")
            
    except Exception as e:
        logger.error(f"❌ Error saving dialog: {e}")
    
    logger.info(f"✅ REAL call initiated successfully. SID: {call_sid}")
    
    return TwilioCallResponse(
        call_sid=call_sid,
        status="initiated",
        message="Real call initiated successfully"
    )

@router.get("/{call_sid}/status", response_model=TwilioCallStatus)
def get_call_status(
    call_sid: str,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Получает статус реального звонка из Twilio
    """
    logger.info(f"📞 Getting REAL call status for {call_sid}")
    
    # Получаем статус звонка из Twilio
    call_status = twilio_service.get_call_status(call_sid)
    
    if not call_status:
        logger.error(f"❌ Failed to get call status for {call_sid}")
        raise HTTPException(status_code=500, detail="Failed to get call status")
    
    logger.info(f"✅ Call status retrieved: {call_status['status']}")
    
    return TwilioCallStatus(
        call_sid=call_status['call_sid'],
        status=call_status['status'],
        duration=call_status['duration'],
        recording_url=None  # Пока не реализовано
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
        logger.info(f"📱 Twilio webhook received: {dict(form_data)}")
        
        # Здесь можно добавить логику обработки событий
        # Например, сохранение статуса звонка в базу данных
        
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Error processing Twilio webhook: {e}")
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
        
        logger.info(f"📞 Call {call_sid} status: {call_status}")
        
        # Здесь можно обновить статус звонка в базе данных
        
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Error processing call status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")