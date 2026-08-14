from datetime import datetime, UTC
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from backend.database.db_types import LoanStatus


class LoanBase(BaseModel):
    user_id: UUID
    currency: str
    interest_rate: Decimal
    status: LoanStatus = Field(default=LoanStatus.PENDING)
    start_date: datetime = Field(default=datetime.now(UTC))
    due_date: datetime = Field(default=datetime.now(UTC))
    end_date: datetime = Field(default=datetime.now(UTC))


class LoanCreate(LoanBase):
    principal: Decimal
    balance: Decimal

    @field_validator("principal", "balance")
    @classmethod
    def validate_non_zero(cls, v):
        if v < 0:
            raise ValueError("Principal or Balance can not be less than Zero")
        return v


class LoanRead(LoanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
