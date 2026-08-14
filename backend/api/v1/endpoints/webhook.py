import json
from fastapi import APIRouter, Request, HTTPException, status
from backend.api.dependencies import WebHookDps
from backend.integration.paystack import verify_paystack_signature
from backend.config import payment_settings


router = APIRouter()


@router.post("/paystack", status_code=status.HTTP_200_OK)
async def paystack_webhook(request: Request, service: WebHookDps):
    signature = request.headers.get("x-paystack-signature")
    if signature is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Signature"
        )

    raw_body = await request.body()

    if not verify_paystack_signature(
        raw_body,
        signature,
        payment_settings.PAYSTACK_SECRET_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature",
        )
    try:
        payload = json.loads(raw_body)

    except json.JSONDecodeError:
        return {"status": "Ignored"}

    try:
        await service.process_gateway_event(payload)

    except Exception:
        return

    return {"status": "recieved" }
