from datetime import date


def offer_badge(raw_status, valid_until=None) -> str:
    status = (raw_status or "").strip()

    if status == "Sprejeta":
        return "Sprejeta"
    if status == "Zavrnjena":
        return "Zavrnjena"
    if status == "Osnutek":
        return "Osnutek"

    if valid_until and status not in ("Sprejeta", "Zavrnjena"):
        try:
            until = date.fromisoformat(str(valid_until)[:10])
            if until < date.today():
                return "Potekla"
        except ValueError:
            pass

    if status in ("Poslana", "Izdan", "Izdana"):
        return "Poslana"

    return status or "Osnutek"
