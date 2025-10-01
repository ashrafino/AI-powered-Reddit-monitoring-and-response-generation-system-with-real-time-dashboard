from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt

from jose import jwt
from passlib.context import CryptContext

from .config import settings

# Initialize bcrypt context with optimal settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    bcrypt__default_rounds=12,
    bcrypt__salt_size=22,  # Bcrypt requires exactly 22 characters for salt
    deprecated="auto"
)
ALGORITHM = "HS256"


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)



