import hmac
import hashlib
import httpx

from backend.config import payment_settings


class PaystackClient:
    def __init__(self, timeout: float = 10.0):
        self._client = httpx.AsyncClient(
            base_url="https://api.paystack.co",
            headers={
                "Authorization": (
                    f"Bearer {payment_settings.PAYSTACK_SECRET_KEY}"
                ),
                "Content-Type": "application/json",
            },
            timeout=timeout
        )

    async def initialize_transaction(
        self,
        email: str,
        amount: int,
        reference: str,
    ):
        response = await self._client.post(
            "/transaction/initialize",
            json={
                "email": email,
                "amount": amount,
                "reference": reference,
            },
        )
        print("PAYSTACK STATUS:", response.status_code)
        print("PAYSTACK RESPONSE:", response.text)
        response.raise_for_status()

        return response.json()


    async def verify_transction(self, reference: str):
        response = await self._client.get(
            f"/transaction/verify/{reference}"
        )
        response.raise_for_status()

        return response.json()


def verify_paystack_signature(raw_body: bytes, signature: str, secret: str):
    computed = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


