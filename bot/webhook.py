import os
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.rest import Client as TwilioClient

from bot.agent import get_reply

router = APIRouter()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def _send_whatsapp(to: str, body: str):
    """Send a WhatsApp reply via Twilio."""
    client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
        body=body,
    )


@router.post("/webhook", response_class=PlainTextResponse)
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
):
    """
    Twilio sends incoming WhatsApp messages here as form-encoded data.
    We call the AI agent and reply back via Twilio.
    """
    sender = From.strip()        # e.g. "whatsapp:+919876543210"
    message = Body.strip()

    print(f"[Webhook] Message from {sender}: {message}")

    reply = get_reply(phone_number=sender, user_message=message)

    print(f"[Webhook] Reply to {sender}: {reply}")

    # Only send via Twilio if credentials are configured
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_ACCOUNT_SID.startswith("AC"):
        try:
            _send_whatsapp(to=sender, body=reply)
        except Exception as e:
            print(f"[Twilio Error] {e}")

    # Return TwiML-compatible empty response (Twilio expects 200 OK)
    return ""


@router.post("/webhook/test")
async def test_webhook(request: Request):
    """
    Developer-friendly JSON endpoint to test the bot without Twilio.
    POST { "phone": "+919876543210", "message": "your message" }
    """
    body = await request.json()
    phone = body.get("phone", "test_user")
    message = body.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="'message' is required")

    reply = get_reply(phone_number=phone, user_message=message)
    return {"phone": phone, "message": message, "reply": reply}
