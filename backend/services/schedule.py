from datetime import timedelta, datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.database.models import Loan, User, RepaymentSchedule
from backend.database.db_types import RepaymentFrequency, SchedulePaymentStatus

today = datetime.now(UTC).date()

start_of_day = datetime.combine(
    today,
    datetime.min.time(),
    tzinfo=UTC,
    )

start_of_tomorrow = start_of_day + timedelta(days=1)

class ScheduleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def schedule_repayment(
        self,
        loan: Loan,
        user: User,
    ):
        repayment_amount = loan.installment
        frequency = loan.repayment_frequency

        if frequency == RepaymentFrequency.DAILY:
            number_of_repayments = loan.term * 20

        elif frequency == RepaymentFrequency.WEEKLY:
            number_of_repayments = loan.term * 4

        elif frequency == RepaymentFrequency.MONTHLY:
            number_of_repayments = loan.term

        else:
            raise ValueError(
                f"Unsupported repayment frequency: {frequency}"
            )

        due_date = loan.start_date

        for installment_number in range(1, number_of_repayments + 1):

            repayment_schedule = RepaymentSchedule(
                loan_id=loan.id,
                user_id=user.id,
                installment_number=installment_number,
                amount_due=repayment_amount,
                amount_paid=0,
                due_date=due_date,
                status="pending",
            )

            self.session.add(repayment_schedule)

            # Don't calculate another date after the final installment
            if installment_number == number_of_repayments:
                break

            if frequency == RepaymentFrequency.DAILY:
                due_date = self._next_business_day(due_date)

            elif frequency == RepaymentFrequency.WEEKLY:
                due_date += timedelta(days=7)

            elif frequency == RepaymentFrequency.MONTHLY:
                due_date += timedelta(days=30)

    async def get_next_three_pending_repayment_schedule(self,  user: User, loan: Loan):
        stmt = select(RepaymentSchedule).where(
            RepaymentSchedule.user_id == user.id,
            RepaymentSchedule.loan_id == loan.id,
            RepaymentSchedule.status != SchedulePaymentStatus.PAID,
            RepaymentSchedule.due_date >= start_of_day
        ).limit(5)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_repayments_schedule_due_today(self):

        stmt = (
            select(
                RepaymentSchedule,
                User,
                Loan,
            )
            .join(
                User,
                User.id == RepaymentSchedule.user_id,
            )
            .join(
                Loan,
                Loan.id == RepaymentSchedule.loan_id,
            )
            .where(
                RepaymentSchedule.due_date >= start_of_day,
                RepaymentSchedule.due_date < start_of_tomorrow,
                RepaymentSchedule.status == SchedulePaymentStatus.PENDING,
            )
        )

        result = await self.session.execute(stmt)

        return result.all()

    @staticmethod
    def _next_business_day(date):
        next_date = date + timedelta(days=1)

        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)

        return next_date

    async def get_user_payment_schedule(self, user: User, loan: Loan):
        stmt = (
            select(RepaymentSchedule)
            .where(
                RepaymentSchedule.user_id == user.id,
                RepaymentSchedule.loan_id == loan.id,
            )
            .order_by(RepaymentSchedule.due_date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

