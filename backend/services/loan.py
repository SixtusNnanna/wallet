from decimal import Decimal
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Loan, User
from backend.api.schemas.loan import LoanCreate, LoanRead
from backend.services.base import BaseService
from backend.exceptions.user import ExistsError, NotFoundError
from backend.database.db_types import LoanStatus, RepaymentFrequency


class LoanService(BaseService[Loan]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Loan)

    @staticmethod
    def get_interest_rate(
        repayment_frequency: RepaymentFrequency,
    ) -> Decimal:
        if repayment_frequency == RepaymentFrequency.MONTHLY:
            return Decimal("0.04")
        elif repayment_frequency == RepaymentFrequency.WEEKLY:
            return Decimal("0.033")
        elif repayment_frequency == RepaymentFrequency.DAILY:
            return Decimal("0.03")
        else:
            msg = f"No interest rate defined for {repayment_frequency}"
            raise ValueError(msg)

    async def get_active_loan(self, user_id: UUID) -> Loan | None:
        result = await self.session.execute(
            select(Loan).where(Loan.user_id == user_id, Loan.status != "paid_off")
        )
        return result.scalar_one_or_none()

    async def get_active_loan_(self, user_id: UUID) -> Loan | None:
        result = await self.session.execute(
                select(Loan).where(Loan.user_id == user_id, Loan.status == "active")
            )
        loan = result.scalar_one_or_none()
        if loan is None:
            raise NotFoundError("Loan")
        return loan

    async def create_loan(self, loan_create: LoanCreate):
        result = await self.session.execute(
            select(User.id).where(
                User.id == loan_create.user_id, User.is_verified
                )
                )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("User")
        interest_rate = self.get_interest_rate(loan_create.repayment_frequency)
        balance = interest_rate * loan_create.principal * 12 + loan_create.principal
        new_loan = Loan(
            **loan_create.model_dump(),
            interest_rate=interest_rate,
            balance=balance
        )
        blocking_loan = await self.get_active_loan(user_id=loan_create.user_id)

        if blocking_loan:
            raise ExistsError("Loan")
        return await self.add(new_loan)

    async def get_owners_loan_history(self, user_id: UUID):
        return await self.get_items(
            user_id=user_id, order_by=self.model.created_at.desc()
        )

    async def loan_pending(self, limit: int = 100, skip: int = 0):
        stmt = select(Loan).where(Loan.status == "pending")
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_loans(
        self,
        status: LoanStatus,
        limit: int = 100,
        skip: int = 0,
    ):
        filters = {}
        if status is not None:
            filters["status"] = status

        return await self.get_items(
            order_by=self.model.created_at.desc(),
            **filters,
        )

    async def get_loan_by_id(self, loan_id: UUID, user_id: UUID):
        result = await self.get_item(id=loan_id, user_id=user_id)
        if not result:
            raise NotFoundError("Loan")
        return result

    async def get_just_any_loan_with_id(self, loan_id):
        result = await self.get(loan_id)
        if not result:
            raise NotFoundError("Loan")
        return result







