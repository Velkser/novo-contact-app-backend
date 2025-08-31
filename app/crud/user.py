from sqlalchemy.orm import Session
from app.models.user import User, RefreshToken
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password
from datetime import datetime, timedelta
from typing import Optional

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def update_last_login(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
    return user

def create_refresh_token(db: Session, user_id: int) -> RefreshToken:
    token = RefreshToken.generate_token()
    expires_at = datetime.utcnow() + timedelta(days=7)  # 7 дней
    
    db_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(datetime.timezone.utc)
    ).first()

def revoke_refresh_token(db: Session, token: str):
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if db_token:
        db_token.revoked = True
        db.commit()