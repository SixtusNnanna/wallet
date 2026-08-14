from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr


from backend.config import mail_settings


class NotificationService:
    def __init__(self):
        self.fastmail = FastMail(
            ConnectionConfig(**mail_settings.model_dump()),
        )

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


