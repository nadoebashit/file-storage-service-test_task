# app/core/security.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(
    sub: str,
    data: Optional[Dict[str, Any]] = None,
    expires_min: Optional[int] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_min or settings.JWT_EXPIRES_MIN)
    payload: Dict[str, Any] = {"sub": sub, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if data:
        payload.update(data)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Вернёт payload или бросит JWTError при проблеме подписи/срока/алгоритма."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
