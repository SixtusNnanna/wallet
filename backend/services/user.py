from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from backend.database.models import User
from backend.api.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.base import BaseService
from backend.core.email_token import generate_verification_token, verify_verfication_token

from backend.exceptions import user as user_exception
from backend.services.notification import NotificationService

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


class UserService(BaseService[User]):

    def __init__(self, session:  AsyncSession):
        super().__init__(session, User)
        self.notifcation = NotificationService()

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
        token = generate_verification_token(new_user.email)
        verifcation_link = f"http://127.0.0.1:8000/auth/verify?token={token}"
        context = {
            "full_name": new_user.full_name,
            "verification_url": verifcation_link
        }
        await self.notifcation.send_mail(
            recipients=[new_user.email,],
            subject="Verification Token",
            context=context,
            templates="email_verification.html"
        )

        return new_user

    async def get_verification_token(self, email):
        return generate_verification_token(email)

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self.get_item(email=email)
        if not user:
            raise user_exception.NotFoundError("User")
        if not pwd_context.verify(password, user.password_hash):
            raise user_exception.InvalidPasswordError
        return user

    async def verify_email(self, token: str):
        email = verify_verfication_token(token)
        print("decoded email:", email)
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








