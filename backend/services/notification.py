from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from backend.integration.whatsapp import WhatsAppClient
from backend. utils import normalize_whatsapp_number


from backend.config import mail_settings


class NotificationService:
    def __init__(self):
        self.fastmail = FastMail(
            ConnectionConfig(**mail_settings.model_dump()),
        )
        self.wa = WhatsAppClient()

    async def send_mail(
        self,
        recipients: list[EmailStr],
        subject: str,
        context: dict,
        templates: str,
    ):
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=context,
            subtype=MessageType.html,
        )

        await self.fastmail.send_message(message=message, template_name=templates)

    async def send_today_repayment_reminders(self):

        schedules = await self.get_repayments_schedule_due_today()

        for schedule, user in schedules:
            user_phone = normalize_whatsapp_number(user.phone)

            message = f"""
                Dear {user.full_name} 👋

                Your Sachet Ease repayment of ₦{schedule.amount_due:,.2f} is due today.

                💰 Amount Due: ₦{schedule.amount_due:,.2f}
                📅 Due Date: {schedule.due_date.strftime("%d %b %Y")}

                You can make your repayment here:
                {{await self.repayment_client.initiate_repayment(schedule.amount_due)}}

                Thank you for choosing Sachet Ease.
                Making rent easier. 🏠
                """

            await self.wa.send_message(
                user_phone,
                message.strip()
            )




