

import hmac

from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import PlainTextResponse
from backend.config import whatsapp_settings
from backend.integration.whatsapp import verify_signature
from backend.api.dependencies import WADeps


router = APIRouter()


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    if (
        hub_mode == "subscribe"
        and hub_verify_token == whatsapp_settings.WHATSAPP_VERIFY_TOKEN
    ):
        return hub_challenge

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_whatsapp_webhook(request: Request, whatsapp_services: WADeps):
    signature_header = request.headers.get("x-hub-signature-256")
    raw_body = await request.body()
    if not verify_signature(raw_body, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    await whatsapp_services.handle_incoming_whatsapp_message(payload)

    return {"status": "received"}
