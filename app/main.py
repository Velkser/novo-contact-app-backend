from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, contacts, prompt_templates, scheduled_calls, twilio_calls 

from app.database import engine, Base

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
    allow_origins=["http://localhost:4173", "http://localhost:5173"],  # Frontend Vite
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

@app.get("/")
async def root():
    return {"message": "Novo Contact App API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}