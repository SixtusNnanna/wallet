from pathlib import Path
from datetime import datetime, timedelta, timezone, UTC
from jose import jwt, JWTError
from uuid import uuid4

from backend.config import settings
from backend.exceptions.user import InvalidTokenError


def create_access_token(payload: dict, expiry: timedelta | None = None):
    to_encode = payload.copy()
    expire = datetime.now(UTC) + \
        (expiry or timedelta(minutes=settings.ACCESS_TOKEN_EXP_TIME))
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    return jwt.encode(
        to_encode, key=settings.SECRETS, algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token=token, key=settings.SECRETS,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise InvalidTokenError
