from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)

from backend.config import settings

serializer = URLSafeTimedSerializer(secret_key=settings.SECRETS)

EMAIL_VERIFICATION_SALT = "email_verification"


def generate_verification_token(email: str) -> str:
    return serializer.dumps(email, salt=EMAIL_VERIFICATION_SALT)


def verify_verfication_token(
    token: str,
    max_age_seconds: int = 3600,
) -> str | None:
    try:
        email = serializer.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
            max_age=max_age_seconds,
        )

    except (BadSignature, SignatureExpired):
        return None
    return email
