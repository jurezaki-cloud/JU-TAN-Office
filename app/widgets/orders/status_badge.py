def order_badge(raw_status, _delivery_date=None) -> str:
    status = (raw_status or "").strip()
    return status or "Osnutek"
