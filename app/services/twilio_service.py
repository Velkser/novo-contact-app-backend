# app/services/twilio_service.py
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Pause
from app.core.config import settings
from typing import Optional
import logging
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.client = None
        self.from_number = settings.TWILIO_PHONE_NUMBER
        
        # Проверяем наличие учетных данных
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        else:
            logger.warning("Twilio credentials not configured. Calls will be simulated.")
    
    def make_call(self, to_number: str, script: str, contact_id: int) -> Optional[str]:
        """
        Совершает звонок через Twilio с мужским английским голосом
        
        Args:
            to_number: Номер телефона получателя
            script: Текст для чтения (передается через API)
            contact_id: ID контакта
            
        Returns:
            SID звонка или None в случае ошибки
        """
        if not self.client:
            logger.info(f"SIMULATED CALL: Would call {to_number} with script: {script}")
            return "SIMULATED_CALL_SID"
        
        try:
            # Создаем TwiML для звонка
            twiml = self._generate_twiml_male_english(script)
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                twiml=twiml,
                status_callback=f"{settings.BASE_URL}/api/v1/twilio/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            logger.info(f"Call initiated: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error making call to {to_number}: {e}")
            return None
    
    def _generate_twiml_male_english(self, script: str) -> str:
        """Генерирует TwiML для мужского английского голоса"""
        resp = VoiceResponse()
        
        # Предобрабатываем текст
        processed_script = self._preprocess_text(script)
        
        if not processed_script:
            processed_script = "Hello. I'm calling from Novo. This is a test."
        
        # Добавляем паузу перед началом речи
        resp.append(Pause(length=1))
        
        # Основное сообщение с мужским английским голосом
        resp.say(
            processed_script,
            voice='man',           # Мужской голос
            language='en-US'       # Английский язык США
        )
        
        # Добавляем паузу в конце перед завершением
        resp.append(Pause(length=1))
        
        # Завершаем звонок
        resp.hangup()
        
        return str(resp)
    
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def send_sms(self, to_number: str, message: str) -> Optional[str]:
        """Отправляет SMS через Twilio"""
        if not self.client:
            logger.info(f"SIMULATED SMS: Would send '{message}' to {to_number}")
            return "SIMULATED_SMS_SID"
        
        try:
            message_obj = self.client.messages.create(
                to=to_number,
                from_=self.from_number,
                body=message
            )
            
            logger.info(f"SMS sent: {message_obj.sid}")
            return message_obj.sid
            
        except Exception as e:
            logger.error(f"Error sending SMS to {to_number}: {e}")
            return None

# Глобальный экземпляр сервиса
twilio_service = TwilioService()