from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Loan, User
from backend.api.schemas.loan import LoanCreate, LoanRead
from backend.services.base import BaseService
from backend.exceptions.user import ExistsError, NotFoundError
from backend.database.db_types import LoanStatus


class LoanService(BaseService[Loan]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Loan)

    async def get_active_loan(self, user_id: UUID) -> Loan | None:
        result = await self.session.execute(
            select(Loan).where(Loan.user_id == user_id, Loan.status != "paid_off")
        )
        return result.scalar_one_or_none()

    async def get_active_loan_(self, user_id: UUID) -> Loan | None:
        result = await self.session.execute(
                select(Loan).where(Loan.user_id == user_id, Loan.status == "active")
            )
        return result.scalar_one_or_none()

    async def create_loan(self, loan_create: LoanCreate):
        result = await self.session.execute(select(User.id).where(User.id == loan_create.user_id))
        if result.scalar_one_or_none() is None:
            raise NotFoundError("User")
        new_loan = Loan(
            **loan_create.model_dump()
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







