import base64
import io
import json
import wave
import logging
import os
from datetime import datetime
from urllib.parse import quote, unquote
from typing import List, Optional, Dict, Any
import httpx

from twilio.twiml.voice_response import VoiceResponse, Gather


from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.websockets import WebSocket
from sqlalchemy.orm import Session

from app.database import get_db
from app.api import deps
from app.models.user import User
from app.models.contact import Contact, ContactDialog, DialogMessage
from app.services.twilio_service import twilio_service
from app.schemas.twilio_call import TwilioCallCreate, TwilioCallResponse, TwilioCallStatus
from app.crud.contact import get_contact, add_dialog, add_dialog_message

# Новый API
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

# import openai  # или твой клиент genai_model
# genai_model = openai  # заменить на конкретный клиент если нужно




client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

BASE_URL = os.getenv("BASE_URL")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

START_WAV_PATH = os.path.join(BASE_DIR, 'sounds',"start.wav")
END_WAV_PATH = os.path.join(BASE_DIR, 'sounds', "end.wav")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/twilio-calls", tags=["twilio_calls"])

# Хранение активных звонков и подключений
active_calls: Dict[str, Dict] = {}  # call_sid -> {contact_id, user_id, script}
active_connections: Dict[str, WebSocket] = {}  # call_sid -> websocket

connected_clients = []  # фронтенд клиенты


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
    


@router.websocket("/ws/dialog")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket для отправки текста диалога в реальном времени на фронтенд.
    Сервер будет пушить туда распозанную речь абонента и статусы звонка.
    """
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Можно обработать команды от фронтенда, например "start call"
            logger.info(f"Received from frontend: {data}")
    except Exception as e:
        connected_clients.remove(websocket)
        logger.info(f"Frontend disconnected: {e}")

async def broadcast_message(message: str):
    """
    Отправка текста всем подключенным фронтенд-клиентам.
    Используется, чтобы показать в UI прогресс диалога.
    """
    for client in connected_clients[:]:  # Копируем список чтобы избежать ошибок при удалении
        try:
            await client.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
            if client in connected_clients:
                connected_clients.remove(client)




@router.post("/initiate-dialog", response_model=TwilioCallResponse)
def initiate_dialog_call(
    call_data: TwilioCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    contact = get_contact(db, contact_id=call_data.contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    script = call_data.script or contact.script
    if not script:
        raise HTTPException(status_code=400, detail="No script provided")

    if not twilio_service.client:
        raise HTTPException(status_code=500, detail="Twilio service not configured")

    # URL вебхука для звонка
    script_encoded = quote(script)
    webhook_url = f"{call_data.base_url}/api/twilio-calls/dialog/answer?script={script_encoded}&contact_id={contact.id}&user_id={current_user.id}"

    call_sid = twilio_service.make_call_with_url(
        to_number=contact.phone,
        url=webhook_url,
        contact_id=contact.id
    )

    if not call_sid:
        raise HTTPException(status_code=500, detail="Failed to initiate call")

    active_calls[call_sid] = {
        "contact_id": contact.id,
        "user_id": current_user.id,
        "script": script
    }

    return TwilioCallResponse(
        call_sid=call_sid,
        status="initiated",
        message="Dialog call initiated successfully"
    )


# --------------------- Диалоговые Webhook ---------------------

@router.post("/dialog/answer")
async def dialog_answer(request: Request, script: str = None, contact_id: int = None, user_id: int = None):

    resp = VoiceResponse()

    # Проигрываем готовый вопрос start.wav
    start_wav_url = f"{os.getenv('BASE_URL')}/static/start.wav"
    print(start_wav_url, 'from funcion dialog_answer')
    resp.play(start_wav_url)

    gather = Gather(
        input="speech",
        action=f"/api/twilio-calls/dialog/gather?script={quote(script or '')}&contact_id={contact_id}&user_id={user_id}",
        speech_timeout=1.5,
        language="sk-SK"
    )
    resp.append(gather)

    resp.hangup()
    return Response(content=str(resp), media_type="application/xml")



# ==============================
# Dialog Gather Webhook (обработка ответа абонента)

@router.post("/dialog/gather")
async def dialog_gather(
    request: Request,
    script: str = None,
    contact_id: int = None,
    user_id: int = None,
    db: Session = Depends(get_db)
):
    from twilio.twiml.voice_response import VoiceResponse

    form = await request.form()
    speech_result = form.get("SpeechResult")
    call_sid = form.get("CallSid")

    resp = VoiceResponse()
    script_decoded = unquote(script) if script else ""

    if not speech_result:
        # Если клиент молчит → завершаем
        end_wav_url = f"{os.getenv('BASE_URL')}/static/end.wav"
        resp.play(end_wav_url)
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")

    # --------------------------
    # 1. Сохраняем реплику клиента
    # --------------------------

    normalized = speech_result.lower().strip()
    logger.info(f"🎧 Speech result: {normalized}")
    await save_speech_message(db, call_sid, "client", normalized)

    # --------------------------
    # 2. Классифицируем ответ
    # --------------------------

    classification = await classify_user_response(normalized)

    # --------------------------
    # 3. Ветвления сценария
    # --------------------------

    if classification == "exit":
        end_wav_url = f"{os.getenv('BASE_URL')}/static/end.wav"
        resp.play(end_wav_url)
        resp.hangup()

    elif classification == "question":
        reply = await generate_ai_reply(normalized)
        await save_speech_message(db, call_sid, "agent", reply)

        # Озвучиваем ответ
        tts_url = f"{os.getenv('BASE_URL')}/api/twilio-calls/gemini-tts-live?text={quote(reply)}"
        resp.play(tts_url)

        gather = Gather(
            input="speech",
            action=f"{os.getenv('BASE_URL')}/api/twilio-calls/dialog/gather?script={quote(script_decoded)}&contact_id={contact_id}&user_id={user_id}",
            speech_timeout=1.5,
            language="sk-SK"
        )

        # Снова задаём уточняющий вопрос
        squestion_wav_url = f"{os.getenv('BASE_URL')}/static/squestion.wav"
        gather.play(squestion_wav_url)

        resp.append(gather)
        resp.hangup()

    elif classification == "positive":
        # Читаем основной скрипт
        tts_url = f"{os.getenv('BASE_URL')}/api/twilio-calls/gemini-tts-live?text={quote(script_decoded)}"
        resp.play(tts_url)

        # Спросим про вопросы и сразу создаём Gather
        gather = Gather(
            input="speech",
            action=f"{os.getenv('BASE_URL')}/api/twilio-calls/dialog/gather?script={quote(script_decoded)}&contact_id={contact_id}&user_id={user_id}",
            speech_timeout=1.5,
            language="sk-SK"
        )

        # Проигрываем фразу для вопросов
        fquestion_wav_url = f"{os.getenv('BASE_URL')}/static/fquestion.wav"
        gather.play(fquestion_wav_url)

        resp.append(gather)
        resp.hangup()

    else:  # neutral
        # Если непонятно → уточняем
        gather = Gather(
            input="speech",
            action=f"{os.getenv('BASE_URL')}/api/twilio-calls/dialog/gather?script={quote(script_decoded)}&contact_id={contact_id}&user_id={user_id}",
            speech_timeout=1.5,
            language="sk-SK"
        )

        # Проигрываем повторную фразу
        repeat_wav_url = f"{os.getenv('BASE_URL')}/static/repeat.wav"
        gather.play(repeat_wav_url)

        resp.append(gather)
        resp.hangup()

    return Response(content=str(resp), media_type="application/xml")



# ==============================
# Gemini TTS Endpoint (возвращает mp3 base64)

@router.get("/gemini-tts")
async def gemini_tts(text: str):
    audio_bytes = await process_text_to_speech(text)
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    return JSONResponse({"audio": audio_base64, "text": text, "duration": len(text) * 0.1})


# ==============================
# Media Stream WebSocket (реальный TTS/STT)
@router.websocket("/media-stream/{call_sid}")
async def media_stream_websocket(websocket: WebSocket, call_sid: str, db: Session = Depends(get_db)):
    await websocket.accept()
    logger.info(f"🎙️ Media stream connected for call {call_sid}")

    if call_sid not in active_calls:
        await websocket.close(code=1008, reason="Call not found")
        return

    call_info = active_calls[call_sid]

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("event") == "media":
                recognized_text = await process_speech_to_text(msg)
                if recognized_text:
                    await save_speech_message(db, call_sid, "client", recognized_text)
                    response_text = f"Ďakujem. Teraz vám prečítam správu: {call_info['script']}"
                    audio_bytes = await process_text_to_speech(response_text)
                    await websocket.send_text(json.dumps({
                        "event": "media",
                        "audio": base64.b64encode(audio_bytes).decode("utf-8")
                    }))
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        await websocket.close()
        logger.info(f"❌ WebSocket closed for call {call_sid}")


# --------------------- Gemini TTS/STT ---------------------
async def process_speech_to_text(audio_bytes: bytes) -> str:
    """
    STT через Gemini
    """
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[{
                "role": "user",
                "parts": [types.Part(
                    inline_data=types.Blob(
                        mime_type="audio/wav",
                        data=audio_bytes
                    )
                )]
            }],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"]
            )
        )

        return response.candidates[0].content.parts[0].text.strip()
    except Exception as e:
        logger.error(f"❌ STT error: {e}")
        return ""

# ---------------------------
# TTS (Text-to-Speech)
# ---------------------------
async def process_text_to_speech(text: str) -> bytes:
    """
    Генерация речи через Gemini 2.5 Flash Preview TTS (словацкий язык)
    """
    try:
        # Декодируем URL-кодирование
        text_decoded = unquote(text)
        logger.info(f"🔊 Generating TTS for text: {text_decoded[:50]}...")

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text_decoded,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore"  # Можно выбрать другой голос из доступных
                        )
                    )
                )
            )
        )

        # Получаем аудио-данные из ответа
        audio_bytes = response.candidates[0].content.parts[0].inline_data.data
        if not audio_bytes:
            raise ValueError("Gemini TTS вернул пустой ответ")

        return audio_bytes

    except Exception as e:
        logger.error(f"❌ Gemini TTS error: {e}")
        return b""



# --------------------- Сохранение сообщений ---------------------

async def save_speech_message(db: Session, call_sid: str, role: str, text: str):
    """
    Сохраняем текст в БД
    """
    call_info = active_calls.get(call_sid)
    if not call_info:
        logger.warning(f"❌ Call {call_sid} not found")
        return

    dialog = db.query(ContactDialog).filter(
        ContactDialog.contact_id == call_info["contact_id"],
    ).order_by(ContactDialog.date.desc()).first()

    if not dialog:
        dialog = ContactDialog(
            contact_id=call_info["contact_id"],
            user_id=call_info["user_id"],
            date=datetime.utcnow()
        )
        db.add(dialog)
        db.commit()
        db.refresh(dialog)

    message = DialogMessage(
        dialog_id=dialog.id,
        role=role,
        text=text
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    logger.info(f"💾 Saved {role} message: {text[:50]}...")


# --------------------- Gemini TTS endpoint ---------------------

def pcm_to_wav(pcm_bytes: bytes, sample_rate=24000, channels=1, sample_width=2):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    buf.seek(0)
    return buf


@router.get("/gemini-tts-live")
async def gemini_tts_live(text: str = Query(..., description="Текст для озвучивания")):
    """
    Возвращает WAV поток для Twilio Play.
    Twilio ожидает прямой WAV URL.
    """
    try:
        # Получаем "сырое" аудио через общую функцию
        audio_bytes = await process_text_to_speech(text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS вернул пустое аудио")

        # Конвертируем PCM в WAV для Twilio
        wav_io = pcm_to_wav(audio_bytes)

        return StreamingResponse(wav_io, media_type="audio/wav")

    except Exception as e:
        logger.error(f"❌ gemini_tts_live error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    


def is_positive_response(speech: str) -> bool:
    """
    Проверка согласия (да/нет)
    """

    if not speech:
        return False

    text = speech.strip().lower()

    positive_keywords = [
        "áno", "ano", "jo", "ok", "okay", "yes", "da", "sure", "jasné", "hej"
    ]

    return any(word in text for word in positive_keywords)


async def generate_ai_reply(user_text: str) -> str:
    """
    Генерация ответа агента через Gemini.
    user_text: что сказал клиент
    contact_id, user_id: можно использовать для персонализации
    """
    try:
        prompt = f"""
            Si zdvorilý a užitočný asistent predaja.
        Klient povedal: „{user_text}“.
        Odpovedz na slová klienta v slovenčine, stručne a priateľsky.
        Ak otázka nie je k veci, jemne vráť rozhovor späť k produktu.
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
                temperature=0.6,
            )
        )

        ai_reply = response.candidates[0].content.parts[0].text.strip()
        logger.info(f"🤖 Agent reply: {ai_reply}")
        return ai_reply

    except Exception as e:
        logger.error(f"❌ Gemini reply error: {e}")
        return "Prepáčte, nerozumel som otázke."

async def classify_user_response(text: str) -> str:
    """
    Классифицирует ответ пользователя: positive / exit / question / neutral
    """
    prompt = f"""
        Si asistent, ktorý analyzuje reč používateľa v slovenskom jazyku.
        Text: „{text}“

        Tvoja úloha: určiť jednu z tried:
        - „positive“ → súhlas/povolenie pokračovať
        - „exit“ → rozlúčka, ukončenie rozhovoru
            - „question“ → doplňujúca otázka alebo žiadosť o dodatočné informácie
        - „neutral“ → iné

        Odpovedzte len jedným slovom zo zoznamu: positive, exit, question, neutral.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",  # можно взять любой лёгкий чат-модель
        contents=prompt
    )

    classification = response.candidates[0].content.parts[0].text.strip().lower()
    return classification
