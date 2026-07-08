"""Escalation notifications via an n8n webhook.

n8n receives a plain JSON POST and fans it out however the workflow is
configured (Slack DM, Telegram, Google Sheets row, email...). Kept as a
generic webhook call so the agent code has zero n8n-specific coupling — if
N8N_WEBHOOK_URL isn't set (e.g. running the free/no-n8n setup) this becomes a
harmless no-op logged locally instead of failing the conversation.
"""
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def notify_admin(event: str, payload: dict) -> bool:
    if not settings.n8n_webhook_url:
        logger.info("n8n not configured, escalation logged only: event=%s payload=%s", event, payload)
        return False

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(settings.n8n_webhook_url, json={"event": event, **payload})
            resp.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Failed to notify n8n webhook for event=%s", event)
        return False
