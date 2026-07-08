from app.ocr.payment_proof import extract_amount_from_text


def test_extracts_amount_with_thousands_separator():
    text = "Transfer Berhasil\nBank BCA\nJumlah: Rp150.000\nke a.n Toko Maju Jaya"
    assert extract_amount_from_text(text) == 150_000.0


def test_extracts_amount_with_idr_prefix():
    text = "Payment confirmation\nIDR 1.250.000\nRef: 8839201"
    assert extract_amount_from_text(text) == 1_250_000.0


def test_returns_none_when_no_amount_present():
    text = "Thank you for shopping with us!"
    assert extract_amount_from_text(text) is None
