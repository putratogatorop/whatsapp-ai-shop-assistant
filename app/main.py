import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

from app.agent.graph import run_agent
from app.config import get_settings
from app.db.session import init_db
from app.whatsapp.client import whatsapp_client
from app.whatsapp.webhook import parse_incoming_messages, verify_signature
from app.workers.tasks import process_payment_proof

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="WhatsApp AI Shop Assistant", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/webhook")
def verify_webhook(request: Request) -> Response:
    """Meta's one-time webhook verification handshake."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge", "")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Verification failed", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict:
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(raw_body, signature):
        return Response(status_code=403)  # type: ignore[return-value]

    payload = await request.json()
    for msg in parse_incoming_messages(payload):
        whatsapp_client.mark_as_read(msg.message_id)

        if msg.type == "text":
            reply = run_agent(msg.wa_id, msg.text, contact_name=msg.contact_name)
            whatsapp_client.send_text(msg.wa_id, reply)

        elif msg.type == "image":
            # OCR + DB update happen off the request path so the webhook
            # response stays fast (Meta expects a 200 within a few seconds).
            whatsapp_client.send_text(
                msg.wa_id, "Got your payment proof, verifying it now — one moment!"
            )
            process_payment_proof.delay(msg.wa_id, msg.media_id)

    return {"status": "received"}
