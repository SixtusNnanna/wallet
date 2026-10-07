from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Loan, Repayment, WebhookEvent, Ledger
from backend.exceptions.user import IntegrityError, PaymentAmountMismatchError, NotFoundError
from backend.services.repayment import confirm_repayment_success


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
        amount = data.get("amount")
        paid_at_str = data.get("paid_at")

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

        if repayment is None:
            await self.session.commit()
            return
        webhook_event.repayment_id = repayment.id

        if event_type == "charge.success":
            await confirm_repayment_success(
                session=self.session,
                repayment=repayment,
                paid_kobo=amount,
                source="webhook"
            )
        elif event_type == "charge.failed":
            repayment.status = "failed"

        webhook_event.processed = True
        await self.session.commit()




