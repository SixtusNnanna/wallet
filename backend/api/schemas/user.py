from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from backend.database.db_types import Role


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: PhoneNumber
    address: str
    role: Role


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_validation(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError(
                "Password must be at least 8 characters long"
            )
        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )
        if not any(c.islower() for c in v):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )
        if not any(c.isdigit() for c in v):
            raise ValueError(
                "Password must contain at least one digit"
            )
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in v):
            raise ValueError(
                "Password must contain at least one special character"
            )
        return v


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    # role: Role = Role.CUSTOMER

    model_config = ConfigDict(from_attributes=True)
