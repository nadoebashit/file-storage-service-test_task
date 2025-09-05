from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(sub: str, data: Optional[dict[str, Any]] = None, expires_minutes: int | None = None) -> str:
    to_encode = data.copy() if data else {}
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes or settings.JWT_EXPIRES_MIN)
    to_encode.update({"exp": expire, "sub": sub})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e
