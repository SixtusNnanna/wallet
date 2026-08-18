from decimal import Decimal
from uuid import UUID
from datetime import datetime

from backend.database.models import Ledger, Loan
from backend.exceptions.user import NotFoundError
from backend.services.base import BaseService
from sqlalchemy import func, select

from backend.database.db_types import LedgerEntryType


class LedgerService(BaseService[Ledger]):
    def __init__(self, session):
        super().__init__(session, Ledger)

    async def get_user_ledger(
        self,
        user_id: UUID,
        loan_id: UUID | None = None,
        repayment_id: UUID | None = None,
        entry_type: LedgerEntryType | None = None,
        account: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        skip: int = 0,
    ):
        return await self.list(
            order_by=self.model.created_at.desc(),
            user_id=user_id,
            loan_id=loan_id,
            repayment_id=repayment_id,
            entry_type=entry_type,
            account=account,
            start_date=start_date,
            end_date=end_date,
            limit_val=limit,
            offset_val=skip,
        )

    async def get_single_user_legder(self, user_id: UUID, ledger_id: UUID):
        return await self.get_item(id=ledger_id, user_id=user_id)

    async def get_single_legder(self, ledger_id: UUID):
        return await self.get(id=ledger_id)

    async def get_ledger_summary(self, user_id: UUID):
        statement = (
            select(Loan)
            .where(
                Loan.user_id == user_id
            )
            .order_by(Loan.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(statement)
        loan = result.scalar_one_or_none()
        if loan is None:
            raise NotFoundError("Loan")
        repayment_statement = select(
            func.coalesce(func.sum(Ledger.amount), Decimal("0.00"))
        ).where(
            Ledger.user_id == user_id,
            Ledger.loan_id == loan.id,
            Ledger.account == "loan_receivable",
        )
        amount_repaid = await self.session.scalar(repayment_statement)

        return {
            "principal": loan.principal,
            "total_repaid": amount_repaid,
            "outstanding_balance": loan.balance,
            "savings_balance": loan.savings_balance,
        }

    async def get_users_ledger(
        self,
        user_id: UUID | None = None,
        loan_id: UUID | None = None,
        repayment_id: UUID | None = None,
        entry_type: LedgerEntryType | None = None,
        account: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        skip: int = 0,
    ):
        return await self.list(
            order_by=self.model.created_at.desc(),
            user_id=user_id,
            loan_id=loan_id,
            repayment_id=repayment_id,
            entry_type=entry_type,
            account=account,
            start_date=start_date,
            end_date=end_date,
            limit_val=limit,
            offset_val=skip,
        )
