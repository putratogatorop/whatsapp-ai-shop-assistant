import logging

from app.db.crud import latest_order_for_customer, set_payment_proof
from app.db.session import get_session
from app.integrations.n8n_notify import notify_admin
from app.ocr.payment_proof import analyze_payment_proof
from app.whatsapp.client import whatsapp_client
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_payment_proof", bind=True, max_retries=3)
def process_payment_proof(self, wa_id: str, media_id: str) -> None:
    """Runs off the request path so the WhatsApp webhook always responds fast:
    download the image, OCR it, attach it to the customer's latest order, and
    let the customer + an admin know what happened.
    """
    try:
        image_bytes = whatsapp_client.download_media(media_id)
        result = analyze_payment_proof(image_bytes)

        with get_session() as db:
            order = latest_order_for_customer(db, wa_id)
            if order is None:
                whatsapp_client.send_text(
                    wa_id, "I received your payment proof, but couldn't find a pending order for you."
                )
                return
            set_payment_proof(db, order.id, media_id, result["raw_text"])
            order_id = order.id

        amount = result["amount_guess"]
        amount_text = f"Rp{amount:,.0f}" if amount else "an amount I couldn't quite read"
        whatsapp_client.send_text(
            wa_id,
            f"Thanks! I've recorded your payment proof for order #{order_id} "
            f"({amount_text}). Our team will verify it shortly.",
        )
        notify_admin(
            "payment_proof_submitted",
            {"wa_id": wa_id, "order_id": order_id, "amount_guess": amount},
        )
    except Exception as exc:  # noqa: BLE001 - retry any transient failure (network, OCR, etc.)
        logger.exception("process_payment_proof failed for wa_id=%s", wa_id)
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="send_followup_reminder")
def send_followup_reminder(wa_id: str, message: str) -> None:
    whatsapp_client.send_text(wa_id, message)
