from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Loan, Repayment, WebhookEvent, Ledger
from backend.exceptions.user import  IntegrityError


class WebHookService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_gateway_event(self, payload: dict):
        event_type = payload.get("event")
        data = payload.get("data", {})
        gate_way_event_id = str(data.get("id"))
        refrence = data.get("reference")

        webhook_event = WebhookEvent(
            event_id=gate_way_event_id,
            event_type=event_type,
            gate_way="paystack",
            payload=payload,
            processed=False
        )
        self.session.add(webhook_event)

        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            return

        stmt = select(Repayment).where(Repayment.id == refrence)
        result = await self.session.execute(stmt)
        repayment = result.scalar_one_or_none()

        if repayment is None:
            await self.session.commit()
            return
        webhook_event.repayment_id = repayment.id

        if event_type == "charge.success":
            await self._handle_success(repayment, data)
        elif event_type == "charge.failed":
            repayment.status = "failed"

        webhook_event.processed = True
        await self.session.commit()

    async def _handle_success(self, repayment: Repayment, data: dict):
        expected_kobo = int(repayment.amount * 100)
        paid_kobo = data.get("amount")
        if paid_kobo != expected_kobo:
            repayment.status = "failed"
            return

        result = await self.session.execute(
            select(Loan).where(Loan.id == repayment.loan_id).with_for_update()
        )
        loan = result.scalar_one()

        new_balance = loan.balance - repayment.amount
        repayment.status = "success"
        repayment.paid_at = data.get("paid_at") or None

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
