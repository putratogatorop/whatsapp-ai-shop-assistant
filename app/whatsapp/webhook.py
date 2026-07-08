import hashlib
import hmac
from dataclasses import dataclass

from app.config import get_settings

settings = get_settings()


def verify_signature(payload: bytes, signature_header: str | None) -> bool:
    """Validate the X-Hub-Signature-256 header Meta sends with every webhook POST."""
    if not settings.whatsapp_app_secret:
        # No app secret configured (local/dev demo) — skip verification.
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.whatsapp_app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


@dataclass
class IncomingMessage:
    wa_id: str
    message_id: str
    contact_name: str | None
    type: str  # "text" | "image" | ...
    text: str | None = None
    media_id: str | None = None


def parse_incoming_messages(payload: dict) -> list[IncomingMessage]:
    """Extract normalized messages from a WhatsApp Cloud API webhook payload.

    Payload shape: entry[].changes[].value.{messages[], contacts[]}
    Status-update callbacks (delivered/read) have no "messages" key and are skipped.
    """
    results: list[IncomingMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages")
            if not messages:
                continue
            contacts = {c["wa_id"]: c.get("profile", {}).get("name") for c in value.get("contacts", [])}
            for msg in messages:
                wa_id = msg["from"]
                msg_type = msg.get("type", "text")
                if msg_type == "text":
                    results.append(
                        IncomingMessage(
                            wa_id=wa_id,
                            message_id=msg["id"],
                            contact_name=contacts.get(wa_id),
                            type="text",
                            text=msg["text"]["body"],
                        )
                    )
                elif msg_type == "image":
                    results.append(
                        IncomingMessage(
                            wa_id=wa_id,
                            message_id=msg["id"],
                            contact_name=contacts.get(wa_id),
                            type="image",
                            media_id=msg["image"]["id"],
                        )
                    )
                # other types (audio, document, location, ...) are ignored for this demo
    return results
