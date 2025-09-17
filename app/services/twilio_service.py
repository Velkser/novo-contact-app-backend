from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.client = None
        self.from_number = settings.TWILIO_PHONE_NUMBER
        
        # Проверяем наличие учетных данных
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("✅ Twilio service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twilio: {e}")
        else:
            logger.warning("⚠️ Twilio credentials not configured. Calls will be simulated.")
    
    def make_call(self, to_number: str, script: str, contact_id: int) -> Optional[str]:
        """
        Совершает звонок через Twilio (реальный звонок, не симуляция)
        
        Args:
            to_number: Номер телефона получателя
            script: Текст для чтения
            contact_id: ID контакта
            
        Returns:
            SID звонка или None в случае ошибки
        """
        logger.info(f"📞 Making REAL call to {to_number} for contact {contact_id}")
        
        if not self.client:
            logger.warning("⚠️ Twilio not configured. Cannot make real call.")
            return None
        
        try:
            # Создаем TwiML для звонка
            twiml = self._generate_twiml(script)
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                twiml=twiml
            )
            
            logger.info(f"✅ Real call initiated successfully. SID: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"❌ Error making REAL call to {to_number}: {e}")
            return None
    
    def _generate_twiml(self, script: str) -> str:
        """Генерирует TwiML для чтения скрипта"""
        resp = VoiceResponse()
        
        # Предобрабатываем текст
        processed_script = self._preprocess_text(script)
        
        if not processed_script:
            processed_script = "Dobrý deň, prepáčte, ale správa je prázdna."
        
        # Добавляем паузу перед началом речи
        resp.append(resp.pause(length=1))
        
        # Основное сообщение с женским голосом
        resp.say(
            processed_script,
            voice='alice',           # Женский голос (лучше для словацкого)
            language='sk-SK'         # Словацкий язык
        )
        
        # Добавляем паузу в конце перед завершением
        resp.append(resp.pause(length=1))
        
        # Завершаем звонок
        resp.hangup()
        
        return str(resp)
    
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста для лучшего произношения"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Заменяем специальные символы
        replacements = {
            '€': 'euro',
            '&': 'a',
            '@': 'zavináč',
            '%': 'percento',
            '°C': 'stupňov Celzia',
            '°F': 'stupňov Fahrenheita'
        }
        
        for symbol, replacement in replacements.items():
            text = text.replace(symbol, f' {replacement} ')
        
        # Нормализуем множественные пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def get_call_status(self, call_sid: str) -> Optional[dict]:
        """
        Получает стататус звонка из Twilio
        
        Args:
            call_sid: SID звонка
            
        Returns:
            Словарь со статусом звонка или None в случае ошибки
        """
        if not self.client:
            logger.warning("⚠️ Twilio not configured. Cannot get call status.")
            return None
        
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                'call_sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'direction': call.direction,
                'from_': call.from_,
                'to': call.to,
                'start_time': call.start_time.isoformat() if call.start_time else None,
                'end_time': call.end_time.isoformat() if call.end_time else None,
                'price': call.price,
                'price_unit': call.price_unit
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting call status for {call_sid}: {e}")
            return None
        
    def make_call_with_url(self, to_number: str, url: str, contact_id: int) -> Optional[str]:
        """
        Совершает звонок через Twilio, используя внешний webhook (например, для диалогов)
        
        Args:
            to_number: Номер телефона получателя
            url: Webhook URL, который будет отдавать TwiML
            contact_id: ID контакта
            
        Returns:
            SID звонка или None в случае ошибки
        """
        logger.info(f"📞 Making DIALOG call to {to_number} for contact {contact_id} (webhook={url})")
        
        if not self.client:
            logger.warning("⚠️ Twilio not configured. Cannot make dialog call.")
            return None
        
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=url   # вместо twiml указываем URL вебхука
            )
            
            logger.info(f"✅ Dialog call initiated successfully. SID: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"❌ Error making DIALOG call to {to_number}: {e}")
            return None
        

    def make_call_with_media_streams(self, to_number: str, webhook_url: str, contact_id: int) -> Optional[str]:
        """
        Создает звонок с Media Streams, чтобы голос абонента шёл на сервер в реальном времени.
        """
        if not self.client:
            return None

        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                twiml=f'<Response><Start><Stream url="{webhook_url}"/></Start></Response>'
            )
            return call.sid
        except Exception as e:
            logging.error(f"❌ Error making DIALOG call to {to_number}: {e}")
            return None



# Глобальный экземпляр сервиса
twilio_service = TwilioService()