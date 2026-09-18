"""Translate technical exceptions into safe, user-facing Slovenian messages."""

import sqlite3


def friendly_error_message(error):
    text = str(error).strip()
    if isinstance(error, ValueError):
        return text or "Vneseni podatki niso veljavni."
    if isinstance(error, LookupError):
        return text or "Izbranega zapisa ni več mogoče najti."
    if isinstance(error, sqlite3.IntegrityError):
        lowered = text.lower()
        if "foreign key" in lowered:
            return "Zapisa ni mogoče izbrisati, ker je uporabljen v dokumentih."
        if "unique" in lowered:
            return "Zapis z enako šifro ali številko že obstaja."
        return "Podatkov ni bilo mogoče shraniti zaradi povezane evidence."
    if isinstance(error, sqlite3.Error):
        return "Pri delu s podatkovno bazo je prišlo do napake."
    return "Prišlo je do nepričakovane napake. Poskusite znova."
