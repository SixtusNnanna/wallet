from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Loan, Repayment, WebhookEvent, Ledger
from backend.exceptions.user import IntegrityError, PaymentAmountMismatchError


def convert_str(date_str: str):
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

class WebHookService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_gateway_event(self, payload: dict):
        event_type = payload.get("event")
        data = payload.get("data", {})
        gate_way_event_id = str(data.get("id"))
        reference = data.get("reference")
        paid_at_str = data.get("paid_at")
        print("FOUND REFERENCE", reference)

        webhook_event = WebhookEvent(
            event_id=gate_way_event_id,
            event_type=event_type,
            gate_way="paystack",
            payload=payload,
            processed=False,
            processed_at=convert_str(paid_at_str),
        )
        self.session.add(webhook_event)

        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            return

        stmt = select(Repayment).where(Repayment.gateway_reference == reference)
        result = await self.session.execute(stmt)
        repayment = result.scalar_one_or_none()

        print("REPAYMENT HEFRE", repayment)

        if repayment is None:
            await self.session.commit()
            return
        webhook_event.repayment_id = repayment.id

        if event_type == "charge.success":
            print("EVENT TYPE IS SUCCESS")
            await self._handle_success(repayment, data)
        elif event_type == "charge.failed":
            print("EVENT TYPE FAILD")
            repayment.status = "failed"

        webhook_event.processed = True
        await self.session.commit()

    async def _handle_success(self, repayment: Repayment, data: dict):
        expected_kobo = int(repayment.amount * 100)
        paid_kobo = data.get("amount")
        if paid_kobo != expected_kobo:
            repayment.status = "failed"
            raise PaymentAmountMismatchError(
                "The amount paid is not equal to the amount expected"
            )

        result = await self.session.execute(
            select(Loan).where(Loan.id == repayment.loan_id).with_for_update()
        )
        loan = result.scalar_one()

        new_balance = loan.balance - repayment.amount
        repayment.status = "success"
        paid_at_str = data.get("paid_at")
        repayment.paid_at = convert_str(paid_at_str)

        ledger_entry = Ledger(
            loan_id=loan.id,
            user_id=repayment.user_id,
            repayment_id=repayment.id,
            entry_type="repayment",
            account="loan_receivable",
            amount=repayment.amount,
            balance_after=new_balance,
            description=f"Repayment via Paystack, reference {repayment.gateway_reference}",
            created_by=None,
        )
        self.session.add(ledger_entry)
