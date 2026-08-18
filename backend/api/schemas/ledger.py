from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.database.db_types import LedgerEntryType


class LedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loan_id: UUID
    user_id: UUID
    repayment_id: UUID | None
    entry_type: LedgerEntryType
    account: str
    amount: Decimal
    currency: str
    balance_after: Decimal
    description: str
    created_at: datetime
