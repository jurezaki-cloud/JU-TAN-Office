from app.services.licensing_service import device_id


def test_device_id_is_api_compatible():
    value = device_id()
    assert len(value) == 64
    assert all(c in "0123456789abcdef" for c in value)
