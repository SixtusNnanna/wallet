from backend.services.user import UserService
from backend.utlis import create_access_token, format_whatsapp_number
from backend.integration.whatsapp import WhatsAppClient
from datetime import datetime


class WhatsAppService:
    def __init__(self, user_service: UserService, wa_client: WhatsAppClient):
        self.user_service = user_service
        self.wa_client = wa_client

    async def extract_phone_number_from_wa_data(self, wa_data: dict) -> str | None:
        try:
            phone_number = wa_data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            return phone_number
        except (KeyError, IndexError):
            return None

    async def handle_incoming_whatsapp_message(self, wa_data: dict):
        phone_number = await self.extract_phone_number_from_wa_data(wa_data)
        if not phone_number:
            return
        user_phone_number = format_whatsapp_number(phone_number)
        user = await self.user_service.get_user_by_phone(user_phone_number)
        if not user:
            await self.wa_client.send_message(
                recipient_number=phone_number,
                message="We could not find an account associated with this number. Please register first."
            )
            return
        if not user.is_verified:
            await self.wa_client.send_message(
                recipient_number=phone_number,
                message="Your account is currently unverified. Please verify your account."
            )
            return

        selected_option = await self.extract_menu_message(wa_data)
        if not selected_option:
            await self.send_main_menu(phone_number)
        if selected_option == "account_balance":
            await self.send_account_balance(phone_number)
        elif selected_option == "repayment_schedule":
            await self.recent_repayments_schedule(phone_number)

        elif selected_option == "make_payment":
            await self.initiate_payment(phone_number)

        else:
            print(" No other button option")

    async def send_main_menu(self, phone_number: str):

        message = (
            "Hello 👋 Welcome to SachetEase.\n\n"
            "How can we help you today?"
        )

        buttons = [
            {
                "id": "account_balance",
                "title": "Account Balance"
            },
            {
                "id": "repayment_schedule",
                "title": "Repayment Schedule"
            },
            {
                "id": "make_payment",
                "title": "Make a Payment"
            }
        ]

        await self.wa_client.send_buttons(
            recipient_number=phone_number,
            message=message,
            buttons=buttons
        )

    async def user_access_token(self, phone_number: str) -> str | None:
        user_phone_number = format_whatsapp_number(phone_number)
        user = await self.user_service.get_user_by_phone(user_phone_number)
        if not user:
            return None
        access_token = create_access_token(payload={"id": str(user.id)})
        return access_token

    async def send_account_balance(self, phone_number: str):
        access_token = await self.user_access_token(phone_number)

        response = await self.wa_client.get_user_account_balance(access_token)
        balance = response.get("balance")
        if balance is not None:
            message = f"Your current account balance is: ₦{balance}"
        else:
            message = "We could not retrieve your account balance at this time. Please try again later."
        await self.wa_client.send_message(
            recipient_number=phone_number,
            message=message
        )

    async def extract_menu_message(self, wa_data: dict):
        try:
            message = (
                wa_data["entry"][0]
                ["changes"][0]
                ["value"]["messages"][0]
            )
            interactive = message.get("interactive")
            if not interactive:
                return None
            button_reply = interactive.get("button_reply")
            if button_reply:
                return button_reply.get("id")
            return None
        except (KeyError, IndexError, TypeError):
            return None

    async def recent_repayments_schedule(self, phone_number: str):

        access_token = await self.user_access_token(phone_number)

        response = await self.wa_client.get_recent_repayment_schedule(
            access_token
        )

        if response:

            message = "📅 Your Recent Repayment Schedule\n\n"

            for schedule in response:
                message += (
                    f"Due date: {convert_date(schedule["due_date"])}\n"
                    f"Amount Due: ₦{schedule["amount_due"]}\n"
                    f"Amount Paid: ₦{schedule["amount_paid"]}\n"
                    f"Status: {schedule["status"]}\n\n"
                )

            await self.wa_client.send_message(
                recipient_number=phone_number,
                message=message
            )
        else:
            message = (
                "No repayment schedule found. "
                "You probably do not have an active loan with us."
            )

            await self.wa_client.send_message(
                recipient_number=phone_number,
                message=message
            )

    async def initiate_payment(self, phone_number: str):
        access_token = await self.user_access_token(phone_number)
        response = await self.wa_client.make_payment(access_token)
        payment_link = response.get("checkout_url")
        if payment_link:
            message = f"Please complete your payment using the following link: {payment_link}"
        else:
            message = "We could not initiate your payment at this time. Please try again later."
        await self.wa_client.send_message(
            recipient_number=phone_number,
            message=message
        )

def convert_date(to_fromat: datetime):
    dt = datetime.fromisoformat(str(to_fromat))
    return dt.strftime("%B %d, %Y at %I:%M %p")
