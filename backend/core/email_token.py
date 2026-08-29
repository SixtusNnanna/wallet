from redis.asyncio import Redis
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)

from backend.config import settings


serializer = URLSafeTimedSerializer(secret_key=settings.SECRETS)


def generate_verification_token(email: str, salt: str) -> str:
    return serializer.dumps(email, salt=salt)


def verify_verfication_token(
    token: str,
    salt: str,
    max_age_seconds: int = 3600,
) -> str | None:
    try:
        email = serializer.loads(
            token,
            salt=salt,
            max_age=max_age_seconds,
        )

    except (BadSignature, SignatureExpired):
        return None
    return email
