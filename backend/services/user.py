import secrets
from uuid import UUID
from passlib.context import CryptContext
from sqlalchemy import select
from backend.database.models import User
from backend.api.schemas.user import UserCreate, PassWordReset, PasswordResetRequest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.base import BaseService
from backend.core.email_token import generate_verification_token, verify_verfication_token
from backend.database.db_types import Role

from backend.exceptions import user as user_exception
from backend.worker.tasks import sendmail
from backend.database.redis import get_verifcation_code, add_verification_code, delete_verification_code




pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


def create_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

class UserService(BaseService[User]):

    def __init__(self, session:  AsyncSession):
        super().__init__(session, User)

    async def change_user_role(self, user_id: UUID, role: Role):
        user = await self.get(id=user_id)
        if not user:
            return
        if user.role == role:
            raise user_exception.BadRequestException(
                f"User is already a {user.role.value}"
            )

        user.role = role

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def signup(self, user_data: UserCreate):
        existing = await self.session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise user_exception.ExistsError("User")

        hash_password = pwd_context.hash(user_data.password)
        new_user = User(
            **user_data.model_dump(exclude={"password"}),
            password_hash=hash_password
        )
        await self.add(new_user)
        token = generate_verification_token(
            email=new_user.email,
            salt="email_verification_salt",
            )
        verifcation_link = f"http://127.0.0.1:8000/auth/verify?token={token}"
        context = {
            "full_name": new_user.full_name,
            "verification_url": verifcation_link
        }
        sendmail.delay(
            recipients=[new_user.email,],
            subject="Verification Token",
            context=context,
            templates="email_verification.html"
        )

        return new_user

    async def get_verification_token(self, email: str):
        return generate_verification_token(email=email, salt="email_verification_salt" )

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self.get_item(email=email)
        if not user:
            raise user_exception.NotFoundError("User")
        if not pwd_context.verify(password, user.password_hash):
            raise user_exception.InvalidPasswordError
        return user

    async def verify_email(self, token: str):
        email = verify_verfication_token(
            token=token,
            salt="email_verification_salt",
            )
        if email is None:
            return None
        user = await self.get_item(email=email)
        if user is None:
            return None
        if user.is_verified:
            return user
        user.is_verified = True
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def password_reset_link(self, data: PasswordResetRequest):
        token = generate_verification_token(
            email=data.email,
            salt="password_reset_verification",
        )
        email_exist = await self.get_item(email=data.email)
        if email_exist is None:
            return { "message": "If this email exists, a reset link has been sent,"}
        context = {
            "fullname": email_exist.full_name,
            "verification_link": f"http://localhost/auth/reset_password?token={token}"
        }
        sendmail.delay(
            recipients=[data.email],
            subject="Password Reset Link",
            context=context,
            templates="password_reset.html"
        )
        return {
            "Message": "Click the link in your mail box to reset your password"
        }

    async def password_reset_code(self, data: PasswordResetRequest):
        code = create_code()
        email_exist = await self.get_item(email=data.email)
        if email_exist is None:
            return {"message": "If this email exists, a reset code has been sent,"}

        await add_verification_code(str(email_exist.id), code)
        context = {
            "fullname": email_exist.full_name,
            "verification_code": code
        }
        sendmail.delay(
            recipients=[data.email],
            subject="Password Reset Code",
            context=context,
            templates="password_reset_code.html"
        )
        return {
            "message": f"If this email exists, a reset code has been sent, {email_exist.id}"
            }

    async def reset_password(self, token: str, password_reset_data: PassWordReset):
        email = verify_verfication_token(
            token=token,
            salt="password_reset_verification"
        )
        user = await self.get_item(email=email)
        if user is None:
            raise user_exception.NotFoundError("User")
        password = password_reset_data.password

        hash_password = pwd_context.hash(password)
        user.password_hash = hash_password
        await self.session.commit()
        await self.session.refresh(user)
        return {
            "Message": "Your password has been reset successfully!"
        }

    async def reset_password_code(self, password_reset_data: PassWordReset):
        user_id = await get_verifcation_code(password_reset_data.code)

        if user_id is None:
            raise user_exception.InvalidCodeError(
                "Invalid or expired reset code"
            )
        user = await self.get(id=user_id)
        if user is None:
            raise user_exception.NotFoundError("User")
        password = password_reset_data.password
        hash_password = pwd_context.hash(password)
        user.password_hash = hash_password
        await self.session.commit()
        await self.session.refresh(user)
        await delete_verification_code(password_reset_data.code)
        return {
            "Message": "Your password has been reset successfully!"
        }








