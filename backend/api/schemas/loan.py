from datetime import datetime, UTC
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from backend.database.db_types import LoanStatus, RepaymentFrequency


class LoanBase(BaseModel):
    user_id: UUID
    status: LoanStatus = Field(default=LoanStatus.ACTIVE)
    repayment_frequency: RepaymentFrequency = Field(
        default="monthly")

    start_date: datetime = Field(default=datetime.now(UTC))
    due_date: datetime = Field(default=datetime.now(UTC))
    end_date: datetime = Field(default=datetime.now(UTC))


class LoanCreate(LoanBase):
    principal: Decimal

    @field_validator("principal")
    @classmethod
    def validate_non_zero(cls, v):
        if v < 0:
            raise ValueError("Principal or Balance can not be less than Zero")
        return v


class LoanRead(LoanBase):
    id: UUID
    currency: str
    principal: Decimal
    balance: Decimal
    installment: Decimal
    start_date: datetime | None = None
    due_date: datetime | None = None
    end_date: datetime | None = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
