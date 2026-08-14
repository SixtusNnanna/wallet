from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator, ConfigDict
from backend.database.db_types import RepaymentStatus


class RepaymentBase(BaseModel):
    loan_id: UUID
    user_id: UUID
    gateway_reference: str
    payment_method: str
    paid_at: datetime | None = None


class RepaymentCreate(RepaymentBase):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class RepaymentRead(RepaymentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: RepaymentStatus

    model_config = ConfigDict(from_attributes=True)


