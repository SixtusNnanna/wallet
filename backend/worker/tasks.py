from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig

from celery import Celery
from backend.config import db_settings, mail_settings
from asgiref.sync import async_to_sync
from pydantic import EmailStr

app = Celery(
    "wallet_celery",
    broker=db_settings.get_redis_url(4),
    backend=db_settings.get_redis_url(5)
)

fastmail = FastMail(
    ConnectionConfig(
        **mail_settings.model_dump()
    )
)

send_message = async_to_sync(fastmail.send_message)


@app.task
def sendmail(
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
    send_message(message=message, template_name=templates)


