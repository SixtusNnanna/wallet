from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import oauth2_scheme
from backend.database.db_types import Role
from backend.database.models import User
from backend.database.redis import is_jti_blacklisted
from backend.database.session import get_session
from backend.exceptions import user as user_exception
from backend.integration.paystack import PaystackClient
from backend.services.loan import LoanService
from backend.services.repayment import RepaymentServices
from backend.services.user import UserService
from backend.services.webhook import WebHookService
from backend.utlis import decode_access_token


SessionDeps = Annotated[AsyncSession, Depends(get_session)]


def get_user_service(session: SessionDeps):
    return UserService(session)


UserDeps = Annotated[UserService, Depends(get_user_service)]


def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = decode_access_token(token)
        return payload
    except JWTError:
        raise user_exception.InvalidTokenError


async def get_current_user(
    payload: Annotated[dict, Depends(get_token_data)],
    service: UserDeps,
):
    user_id = payload.get("id")
    if user_id is None or await is_jti_blacklisted(payload["jti"]):
        raise user_exception.InvalidTokenError

    user = await service.get(user_id)
    if user is None:
        raise user_exception.NotFoundError("User")
    if not user.is_verified:
        raise user_exception.UserVerifyEmailError

    return user


CurrentUserDps = Annotated[User, Depends(get_current_user)]


async def get_admin_user(current_user: CurrentUserDps):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    return current_user


AdminUserDeps = Annotated[User, Depends(get_admin_user)]


async def get_employee_user(current_user: CurrentUserDps):
    if current_user.role == Role.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    return current_user


EmployeeDeps = Annotated[User, Depends(get_employee_user)]


def get_loan_service(session: SessionDeps):
    return LoanService(session=session)


LoanDeps = Annotated[LoanService, Depends(get_loan_service)]


def get_webhook_service(session: SessionDeps):
    return WebHookService(session=session)


WebHookDps = Annotated[WebHookService, Depends(get_webhook_service)]


def get_paystack_client(request: Request) -> PaystackClient:
    return request.app.state.paystack_client


PayStackDeps = Annotated[PaystackClient, Depends(get_paystack_client)]


def get_repayment_service(session: SessionDeps, paystack: PayStackDeps):
    return RepaymentServices(session, paystack)


RepaymentDps = Annotated[RepaymentServices, Depends(get_repayment_service)]
