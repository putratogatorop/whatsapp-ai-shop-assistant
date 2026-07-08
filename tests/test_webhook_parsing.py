from app.whatsapp.webhook import parse_incoming_messages


def test_parses_text_message():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"wa_id": "6281234567890", "profile": {"name": "Budi"}}],
                            "messages": [
                                {
                                    "from": "6281234567890",
                                    "id": "wamid.abc123",
                                    "type": "text",
                                    "text": {"body": "Do you have a rice cooker?"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    messages = parse_incoming_messages(payload)

    assert len(messages) == 1
    assert messages[0].wa_id == "6281234567890"
    assert messages[0].contact_name == "Budi"
    assert messages[0].type == "text"
    assert messages[0].text == "Do you have a rice cooker?"


def test_parses_image_message():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"wa_id": "6281234567890"}],
                            "messages": [
                                {
                                    "from": "6281234567890",
                                    "id": "wamid.def456",
                                    "type": "image",
                                    "image": {"id": "media123"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    messages = parse_incoming_messages(payload)

    assert len(messages) == 1
    assert messages[0].type == "image"
    assert messages[0].media_id == "media123"


def test_ignores_status_update_callbacks():
    payload = {
        "entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.abc123", "status": "delivered"}]}}]}]
    }

    assert parse_incoming_messages(payload) == []
