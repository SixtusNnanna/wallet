from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from backend.database.db_types import Role


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: PhoneNumber
    address: str



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
    role: Role = Role.CUSTOMER

    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequest(BaseModel):
    email: EmailStr

class PassWordReset(BaseModel):
    code: str
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate_password(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        if len(self.password) < 8:
            raise ValueError(
                "Password must be at least 8 characters long"
            )

        if not any(c.isupper() for c in self.password):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not any(c.islower() for c in self.password):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )

        if not any(c.isdigit() for c in self.password):
            raise ValueError(
                "Password must contain at least one digit"
            )

        if not any(
            c in "!@#$%^&*()-_=+[]{}|;:,.<>?"
            for c in self.password
        ):
            raise ValueError(
                "Password must contain at least one special character"
            )

        return self


class UserSearchResult(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str

    model_config = ConfigDict(from_attributes=True)
