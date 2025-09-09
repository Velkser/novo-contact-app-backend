# app/schemas/twilio_call.py
from pydantic import BaseModel
from typing import Optional

class TwilioCallBase(BaseModel):
    contact_id: int
    script: Optional[str] = None

class TwilioCallCreate(TwilioCallBase):
    pass

class TwilioCallResponse(BaseModel):
    call_sid: str
    status: str
    message: Optional[str] = None

class TwilioCallStatus(BaseModel):
    call_sid: str
    status: str
    duration: Optional[int] = None
    recording_url: Optional[str] = None

class TwilioWebhookRequest(BaseModel):
    CallSid: str
    CallStatus: str
    From: str
    To: str
    Direction: str
    # Добавьте другие поля по необходимости