from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, User, Token
from app.crud.user import (
    create_user, authenticate_user, update_last_login,
    create_refresh_token, get_refresh_token, revoke_refresh_token,
    get_user, get_user_by_email
)
from app.core.security import create_access_token
from app.core.config import settings
from app.api import deps  

router = APIRouter()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    new_user = create_user(db=db, user=user)
    return new_user

@router.post("/login", response_model=Token)
def login_user(
    user_credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Вход в систему"""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Обновление времени последнего входа
    update_last_login(db, user.id)
    
    # Создание токенов
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Создание refresh токена в БД
    refresh_token_db = create_refresh_token(db, user.id)
    
    # Установка cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Для разработки False, в production True
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_db.token,
        httponly=True,
        secure=False,  # Для разработки False, в production True
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновление токенов"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )
    
    # Проверка refresh токена в БД
    db_token = get_refresh_token(db, refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Получение пользователя
    user = get_user(db, db_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Создание новых токенов
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Создание нового refresh токена
    new_refresh_token_db = create_refresh_token(db, user.id)
    
    # Отзыв старого токена
    revoke_refresh_token(db, refresh_token)
    
    # Установка новых cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_db.token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout_user(
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Выход из системы"""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
    
    # Удаление cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):  # ← Исправлено
    """Получение информации о текущем пользователе"""
    return current_user