# app/schemas/scheduled_call.py
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime

class ScheduledCallBase(BaseModel):
    contact_id: int
    # Поддержка обоих вариантов: конкретное время или временное окно
    scheduled_time: Optional[datetime] = None      # Конкретное время звонка
    start_time_window: Optional[datetime] = None   # Начало временного окна
    end_time_window: Optional[datetime] = None     # Конец временного окна
    retry_until_success: Optional[bool] = False    # Повторять пока не дозвонимся
    script: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "pending"  # pending, completed, failed, cancelled, retrying

class ScheduledCallCreate(ScheduledCallBase):
    # Валидация: должен быть указан либо scheduled_time, либо оба временных окна
    @model_validator(mode="after")
    @classmethod
    def validate_timing(cls, values):
        scheduled_time = values.scheduled_time
        start_time_window = values.start_time_window
        end_time_window = values.end_time_window

        # Проверяем, что указано либо scheduled_time, либо оба временных окна
        if not scheduled_time and not (start_time_window and end_time_window):
            raise ValueError(
                "Must specify either scheduled_time or both start_time_window and end_time_window"
            )

        if scheduled_time and (start_time_window or end_time_window):
            raise ValueError(
                "Cannot specify both scheduled_time and time windows"
            )

        if start_time_window and end_time_window and start_time_window >= end_time_window:
            raise ValueError("start_time_window must be before end_time_window")

        return values

class ScheduledCallUpdate(BaseModel):
    # Делаем все поля необязательными для обновления
    contact_id: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    start_time_window: Optional[datetime] = None
    end_time_window: Optional[datetime] = None
    retry_until_success: Optional[bool] = None
    script: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ScheduledCall(ScheduledCallBase):
    id: int
    user_id: int
    call_attempts: int = 0  # Количество попыток звонка
    last_attempt_at: Optional[datetime] = None  # Время последней попытки
    next_retry_at: Optional[datetime] = None    # Время следующей попытки
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ScheduledCallResponse(ScheduledCall):
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_company: Optional[str] = None
    
    class Config:
        from_attributes = True