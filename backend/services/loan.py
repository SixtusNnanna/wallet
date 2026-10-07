from decimal import Decimal
from uuid import UUID
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Ledger, Loan, User
from backend.api.schemas.loan import LoanCreate, LoanRead
from backend.services.base import BaseService
from backend.exceptions.user import ExistsError, NotFoundError
from backend.database.db_types import LoanStatus, RepaymentFrequency
from backend.services.schedule import ScheduleService
from backend.integration.whatsapp import WhatsAppClient
from backend.utlis import normalize_whatsapp_number

class LoanService(BaseService[Loan]):
    def __init__(self, session: AsyncSession):
        self.schedule_service = ScheduleService(session)
        self.whatsapp_client = WhatsAppClient()
        super().__init__(session, Loan)

    @staticmethod
    def get_due_date(start_date: datetime, term: int) -> datetime:
        if term <= 0:
            raise ValueError("Tenure must be greater than Zero")
        return start_date + relativedelta(months=term)

    @staticmethod
    def get_loan_data(
        principal: Decimal,
        term: int,
        repayment_frequency: RepaymentFrequency,
    ) -> dict:
        if repayment_frequency == RepaymentFrequency.MONTHLY:
            balance = principal * Decimal("1.50")
            installment = balance / term
            return {
                "interest_rate": Decimal("0.04"),
                "balance": balance,
                "installment": installment
            }
        elif repayment_frequency == RepaymentFrequency.WEEKLY:
            balance = principal * Decimal("1.40")
            installment = balance / (term * 4)
            return {
                "interest_rate": Decimal("0.04"),
                "balance": balance,
                "installment": installment
             }
        elif repayment_frequency == RepaymentFrequency.DAILY:
            balance = principal * Decimal("1.40")
            installment = balance / (term * 20)
            return {
                    "interest_rate": Decimal("0.03"),
                    "balance": balance,
                    "installment": installment
                }
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
            select(User).where(
                User.id == loan_create.user_id, User.is_verified
                )
                )
        loan_user = result.scalar_one_or_none()
        if loan_user is None:
            raise NotFoundError("User")
        payload = self.get_loan_data(
            loan_create.principal,
            loan_create.term,
            loan_create.repayment_frequency
            )
        new_loan = Loan(
            **loan_create.model_dump(),
            currency="NGN",
            interest_rate=payload["interest_rate"],
            balance=payload["balance"],
            installment=payload["installment"] * Decimal("1.3"),
            due_date=self.get_due_date(
                loan_create.start_date,
                loan_create.term
            )
        )
        blocking_loan = await self.get_active_loan(user_id=loan_create.user_id)

        if blocking_loan:
            raise ExistsError("Loan")
        self.session.add(new_loan)
        await self.session.flush()
        loan_disbursement_entry = Ledger(
                loan_id=new_loan.id,
                user_id=new_loan.user_id,
                entry_type="disbursement",
                account="loan_disbursement",
                amount=new_loan.balance,
                balance_after=new_loan.balance,
                description="Loan Disbursement",
                reference=f"loan_{new_loan.id}",
                created_by=None,
                )
        self.session.add(loan_disbursement_entry)
        await self.schedule_service.schedule_repayment(
            new_loan, loan_user)
        await self.session.commit()
        await self.whatsapp_client.send_message(
            normalize_whatsapp_number(loan_user.phone),
            f"""
            Dear {loan_user.full_name} 👋
            Your loan of {new_loan.balance} has been successfully disbursed.
            Your first repayment of {new_loan.installment} is due on {new_loan.start_date + relativedelta(months=1)}.
            """.strip()
        )
        return new_loan

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
        status: str,
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









