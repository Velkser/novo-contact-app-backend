from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import (
    auth, 
    contacts, 
    prompt_templates, 
    scheduled_calls, 
    twilio_calls,
    groups  
)
from app.database import engine, Base
import logging
import os 
from dotenv import load_dotenv
from fastapi.responses import FileResponse
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

START_WAV_PATH = os.path.join(BASE_DIR, 'sounds',"start.wav")
END_WAV_PATH = os.path.join(BASE_DIR, 'sounds', "end.wav")
FQUESTION_WAV_PATH = os.path.join(BASE_DIR, 'sounds', "fquestion.wav")
SQUESTION_WAV_PATH = os.path.join(BASE_DIR, 'sounds', "squestion.wav")
REPEAT_WAV_PATH = os.path.join(BASE_DIR, 'sounds', "repeat.wav")


# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Novo Contact App API",
    description="API для управления контактами и звонками",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"]
)

# Подключение роутов
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(contacts.router, prefix="/api", tags=["contacts"])
app.include_router(prompt_templates.router, prefix="/api", tags=["prompt_templates"])
app.include_router(scheduled_calls.router, prefix="/api", tags=["scheduled_calls"])
app.include_router(twilio_calls.router, prefix="/api", tags=["twilio_calls"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(groups.scheduled_calls_router, prefix="/api/scheduled-group-calls", tags=["scheduled_group_calls"])  # ← Новый роутер

@app.get("/")
async def root():
    return {"message": "Novo Contact App API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/static/start.wav")
async def get_start_wav():
    """
    Отдаёт заранее записанный start.wav для Twilio Play.
    """
    if not os.path.exists(START_WAV_PATH):
        return {"error": f"start.wav not found. {START_WAV_PATH}"}
    
    return FileResponse(
        START_WAV_PATH,
        media_type="audio/wav",
        filename="start.wav"
    )

@app.get("/static/end.wav")
async def get_end_wav():
    """
    Отдаёт заранее записанный end.wav для Twilio Play.
    """
    if not os.path.exists(END_WAV_PATH):
        return {"error": "end.wav not found"}
    
    return FileResponse(
        END_WAV_PATH,
        media_type="audio/wav",
        filename="end.wav"
    )

@app.get("/static/fquestion.wav")
async def get_fquestion_wav():
    """
    Отдаёт заранее записанный fquestion.wav для Twilio Play.
    """
    if not os.path.exists(FQUESTION_WAV_PATH):
        return {"error": "fquestion.wav not found"}
    
    return FileResponse(
        FQUESTION_WAV_PATH,
        media_type="audio/wav",
        filename="fquestion.wav"
    )

@app.get("/static/squestion.wav")
async def get_squestion_wav():
    """
    Отдаёт заранее записанный squestion.wav для Twilio Play.
    """
    if not os.path.exists(SQUESTION_WAV_PATH):
        return {"error": "squestion.wav not found"}
    
    return FileResponse(
        FQUESTION_WAV_PATH,
        media_type="audio/wav",
        filename="squestion.wav"
    )

@app.get("/static/repeat.wav")
async def get_repeat_wav():
    """
    Отдаёт заранее записанный repeat.wav для Twilio Play.
    """
    if not os.path.exists(REPEAT_WAV_PATH):
        return {"error": "repeat.wav not found"}
    
    return FileResponse(
        REPEAT_WAV_PATH,
        media_type="audio/wav",
        filename="repeat.wav"
    )