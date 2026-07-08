import io
import re

import pytesseract
from PIL import Image

# Matches "Rp 150.000", "Rp150,000", "IDR 150000", etc.
_AMOUNT_PATTERN = re.compile(r"(?:Rp|IDR)\s?([\d.,]{4,})", re.IGNORECASE)


def extract_text(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)


def extract_amount_from_text(text: str) -> float | None:
    """Best-effort extraction of a Rupiah amount from raw OCR text.

    Pure string function (no image/OCR dependency) so it's easy to unit test
    against the wide variety of receipt formats real payment apps produce.
    """
    match = _AMOUNT_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(1)
    # Indonesian formatting uses "." as thousands separator and "," as decimal.
    cleaned = raw.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def analyze_payment_proof(image_bytes: bytes) -> dict:
    text = extract_text(image_bytes)
    return {
        "raw_text": text.strip(),
        "amount_guess": extract_amount_from_text(text),
    }
