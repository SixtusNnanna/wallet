from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.api.dependencies import UserDeps, get_token_data, CurrentUserDps, AdminUserDeps
from backend.api.schemas.user import UserRead, UserCreate
from backend.core.security import TokenData
from backend.database.db_types import Role
from backend.utlis import create_access_token, decode_access_token
from backend.database.redis import blacklist_jti


router = APIRouter()


@router.post("/signup", response_model=UserRead, status_code=201)
async def signup(service: UserDeps, user_create: UserCreate):
    return await service.signup(user_create)


@router.post("/token", response_model=TokenData)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserDeps
        ):
    user = await service.authenticate_user(
       email=form_data.username,
       password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token = create_access_token(payload={"id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verification_code")
async def get_verifcation_token(email: str, service: UserDeps):
    return await service.get_verification_token(email)


@router.get("/verify")
async def verify_user(token: str, service: UserDeps):
    user = await service.verify_email(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link",
        )
    return {"message": "Email verified successfully"}


@router.post("/logout")
async def logout(token_data: Annotated[dict, Depends(get_token_data)]):
    await blacklist_jti(token_data["jti"])
    return {
        "Message": "User Logout Successfull"
    }


@router.get("/me", response_model=UserRead)
async def get_me(user: CurrentUserDps):
    return user

@router.patch("/{user_id}/role")
async def swap_user_role(
    user_id: UUID,
    role: Role,
    service: UserDeps,
    user: AdminUserDeps,
):
    user = await service.change_user_role(
        user_id=user_id, role=role
    )
    return {
        "message": "User role changed successfully",
        "user": user,
    }


