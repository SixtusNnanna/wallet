from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal


class ScheduleRead(BaseModel):

    due_date: datetime
    amount_due: Decimal
    amount_paid: Decimal
    installment_number: int
    status: str

    class Config:
        orm_mode = True
