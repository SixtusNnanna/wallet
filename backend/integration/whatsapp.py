import hmac
import hashlib
from fastapi import requests
import httpx
from backend.config import whatsapp_settings
from backend.utlis import format_whatsapp_number
from backend.database.models import User


APP_SECRET = whatsapp_settings.WHATSAPP_APP_SECRET


class WhatsAppClient:
    def __init__(self, timeout: float = 10.0):
        self._client = httpx.AsyncClient(
            base_url=whatsapp_settings.WHATSAPP_API_URL,
            headers={
                "Authorization": (
                    f"Bearer {whatsapp_settings.WHATSAPP_ACCESS_TOKEN}"
                ),
                "Content-Type": "application/json",
            },
            timeout=timeout
        )
        self.api_client = httpx.AsyncClient(
            base_url="https://roxanna-unclouded-scaringly.ngrok-free.dev",
        )

    async def send_message(
        self,
        recipient_number: str,
        message: str,
    ):
        response = await self._client.post(
            f"/{whatsapp_settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": recipient_number,
                "type": "text",
                "text": {
                    "body": message
                }
            },
        )
        response.raise_for_status()

    async def send_buttons(
            self,
            recipient_number: str,
            message: str,
            buttons: list[dict]

    ):
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": button["id"],
                                "title": button["title"]
                            }
                        }
                        for button in buttons
                    ]
                }
            }
        }
        response = await self._client.post(
            f"/{whatsapp_settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
            json=payload,
        )
        response.raise_for_status()

    async def get_user_account_balance(self, access_token: str):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = await self.api_client.get(
            "/loans/me",
            headers=headers
        )
        response.raise_for_status()
        print("Here this the response", response)
        return response.json()

    async def make_payment(self, access_token: str):
        loan_data = await self.get_user_account_balance(access_token)
        amount = loan_data.get("installment")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "amount": amount
        }
        response = await self.api_client.post(
            "/repayments/initiate",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print("Here this the response", response.json())
        return response.json()

    async def get_recent_repayment_schedule(self, access_token: str):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = await self.api_client.get(
            "/schedule/recent_schedule",
            headers=headers,
        )
        response.raise_for_status()
        print("Here this the response", response)
        return response.json()


def verify_signature(
    raw_body: bytes, signature_header: str
):
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    receive = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, receive)




