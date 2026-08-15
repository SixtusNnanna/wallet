from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.repayment import RepaymentCreate
from backend.database.db_types import RepaymentStatus
from backend.database.models import Loan, Repayment, User, Ledger
from backend.exceptions.user import (
    NoActiveLoanError,
    NotFoundError,
    PaymentInitiationError,
    PayStackError,
    RepaymentAlreadPendingError,
    PaymentError,
    PaymentAmountMismatchError
)
from backend.integration.paystack import PaystackClient
from backend.services.base import BaseService


class RepaymentServices(BaseService[Repayment]):
    def __init__(self, session: AsyncSession, paystack_client: PaystackClient):
        super().__init__(session, Repayment)
        self.paystack_client = paystack_client

    async def check_existing_pending_repayment(self, loan_id: UUID):
        return await self.get_item(loan_id=loan_id, status="pending")

    async def make_payment(self, repayment_data: RepaymentCreate, user: User):
        stmt = select(Loan).where(
            Loan.id == repayment_data.loan_id,
            Loan.user_id == user.id,
        )

        result = await self.session.execute(stmt)
        loan = result.scalar_one_or_none()
        if loan is None:
            raise NotFoundError("No Loan")
        # if loan.status != "active":
        #     raise NoActiveLoanError("You do not have active loan")
        existing_pending_payment = await self.check_existing_pending_repayment(
            repayment_data.loan_id
        )
        if existing_pending_payment:
            raise RepaymentAlreadPendingError(
                "There is a pending Repayment Process, Conclude it"
                )

        repayment = Repayment(**repayment_data.model_dump(), user_id=user.id, status="pending")

        self.session.add(repayment)
        try:
            gate_way_response = await self.paystack_client.initialize_transaction(
                email=user.email,
                amount=int(repayment.amount * 100),
                reference=f"trans-{uuid4().hex}"
            )
        except PayStackError as e:
            repayment.status = "failed"
            await self.session.commit()
            if e.code == "duplicate_reference":
                raise PaymentInitiationError("Could not reinitiate payment, try again")

        repayment.gateway_reference = gate_way_response["data"]["reference"]
        await self.session.commit()
        return {"checkout_url": gate_way_response["data"]["authorization_url"]}

    async def get_repayments(
        self,
        user_id: UUID,
        limit: int = 100,
        skip: int = 0,
    ):
        return await self.list(
            user_id=user_id,
            offset_val=skip,
            limit_val=limit,
        )

    async def get_repayment(self, user_id: UUID, repayment_id):
        return await self.get_item(id=repayment_id, user_id=user_id)

    async def get_repayment_staff(self, repayment_id):
        return await self.get(id=repayment_id)

    async def get_all_repayment(self, limit: int = 100, skip: int = 0):
        return await self.list(
            order_by=self.model.created_at.desc(), offset_val=skip, limit_val=limit
        )

    async def pending_repayments(self, status: RepaymentStatus, user_id: UUID):
        return await self.get_items(
            order_by=self.model.created_at.desc(), status="pending", user_id=user_id
        )

    async def pending_repayments_staff(self, status: RepaymentStatus):
        return await self.get_items(
            order_by=self.model.created_at.desc(), status="pending"
        )

    async def repayment_reconcile(self, repayment_id: UUID):
        pending_repayment_exist = await self.get_item(
            id=repayment_id, status="pending"
        )
        if pending_repayment_exist is None:
            raise NotFoundError("No Pending Repayment")
        payload = await self.paystack_client.verify_transction(
            pending_repayment_exist.gateway_reference
        )
        gate_way_status = payload["data"]["status"]
        if gate_way_status != "success":
            raise PaymentError(
                f"Payment with refrence {repayment_id} is {gate_way_status}"
            )
        await self.confirm_repayment_success(
                repayment=pending_repayment_exist,
                paid_kobo=payload["data"]["amount"],
                source="reconcilliation"

            )
        await self.session.commit()
        return {"message", "Payment Reconciled"}

    async def confirm_repayment_success(
        self, repayment: Repayment, paid_kobo: int, source: str,
            ):
        existing = await self.session.execute(
            select(Ledger).where(Ledger.repayment_id==repayment.id)
        )
        if existing.scalar_one_or_none() is not None:
            return

        expected_kobo = int(repayment.amount * 100)
        if paid_kobo != expected_kobo:
            repayment.status = "failed"
            raise PaymentAmountMismatchError(
            f"Expected {expected_kobo} kobo, gateway reported {paid_kobo}"

            )
        result = await self.session.execute(
            select(Loan).where(Loan.id == repayment.loan_id).with_for_update()
        )
        loan = result.scalar_one()

        new_balance = loan.balance - repayment.amount
        repayment.status = "success"
        repayment.paid_at = datetime.now(timezone.utc)

        ledger_entry = Ledger(
            loan_id = loan.id,
            user_id=repayment.user_id,
            repayment_id=repayment.id,
            entry_type="repayment",
            account="loan_receivable",
            amount=repayment.amount,
            balance_after=new_balance,
            description=f"Repayment confirmed via {source}, reference {repayment.gateway_reference}",
            created_by=None
        )
        self.session.add(ledger_entry)

