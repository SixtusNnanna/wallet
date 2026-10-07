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


def normalize_whatsapp_number(phone: str) -> str:
    phone = phone.strip()

    # Keep digits only
    digits = "".join(filter(str.isdigit, phone))

    # Nigerian local format: 0813... -> 234813...
    if digits.startswith("0"):
        digits = "234" + digits[1:]

    return digits


def format_whatsapp_number(phone: str) -> str:
    digits = "".join(filter(str.isdigit, phone))
    if digits.startswith("234") and len(digits) == 13:
        return f"tel:+234-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"
    raise ValueError("Invalid Nigerian WhatsApp phone number")


