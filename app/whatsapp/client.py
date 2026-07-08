import httpx

from app.config import get_settings

settings = get_settings()

_BASE_URL = f"https://graph.facebook.com/{settings.whatsapp_api_version}"


class WhatsAppClient:
    """Thin wrapper around the Meta WhatsApp Cloud API."""

    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.whatsapp_token}",
            "Content-Type": "application/json",
        }
        self._phone_number_id = settings.whatsapp_phone_number_id

    def send_text(self, to: str, body: str) -> dict:
        url = f"{_BASE_URL}/{self._phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def mark_as_read(self, message_id: str) -> None:
        url = f"{_BASE_URL}/{self._phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()

    def get_media_url(self, media_id: str) -> str:
        url = f"{_BASE_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()["url"]

    def download_media(self, media_id: str) -> bytes:
        media_url = self.get_media_url(media_id)
        headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
        with httpx.Client(timeout=30) as client:
            resp = client.get(media_url, headers=headers)
            resp.raise_for_status()
            return resp.content


whatsapp_client = WhatsAppClient()
