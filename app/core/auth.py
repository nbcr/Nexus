from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.hash import bcrypt_sha256
from passlib.handlers.bcrypt import bcrypt_sha256 as bcrypt_sha256_handler
import logging
from app.core.config import settings

# Password hashing

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    # Use bcrypt_sha256 for robust password verification
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"bcrypt_sha256 backend: {bcrypt_sha256_handler.get_backend()}")
    return bcrypt_sha256.verify(plain_password, hashed_password)


def get_password_hash(password):
    # Use bcrypt_sha256 for robust password hashing
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"bcrypt_sha256 backend: {bcrypt_sha256_handler.get_backend()}")
    return bcrypt_sha256.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None
