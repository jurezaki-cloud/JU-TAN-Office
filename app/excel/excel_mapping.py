from dataclasses import dataclass


def _norm(value: str) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    required: bool = False
    aliases: tuple[str, ...] = ()
    kind: str = "text"  # text, number, date, vat


MODULES = {
    "customers": {
        "title": "Stranke",
        "fields": (
            FieldSpec("company", "Naziv stranke", True, ("customer name", "naziv", "company", "name", "stranka"), "text"),
            FieldSpec("contact", "Kontakt", False, ("contact", "oseba", "kontakt"), "text"),
            FieldSpec("address", "Naslov", False, ("address", "naslov"), "text"),
            FieldSpec("postal_code", "Poštna številka", False, ("postal", "postna", "zip"), "text"),
            FieldSpec("city", "Kraj", False, ("city", "kraj", "mesto"), "text"),
            FieldSpec("country", "Država", False, ("country", "drzava"), "text"),
            FieldSpec("tax_number", "Davčna številka", False, ("tax", "davcna", "vat id"), "text"),
            FieldSpec("email", "Email", False, ("email", "e-mail"), "text"),
            FieldSpec("phone", "Telefon", False, ("phone", "telefon", "tel"), "text"),
        ),
    },
    "products": {
        "title": "Artikli",
        "fields": (
            FieldSpec("code", "Šifra", True, ("code", "sifra", "sku"), "text"),
            FieldSpec("name", "Naziv", True, ("name", "naziv", "artikel", "product"), "text"),
            FieldSpec("description", "Opis", False, ("description", "opis"), "text"),
            FieldSpec("unit", "Enota", False, ("unit", "enota", "em"), "text"),
            FieldSpec("price", "Cena", False, ("price", "cena"), "number"),
            FieldSpec("vat", "DDV", False, ("vat", "ddv", "tax"), "vat"),
        ),
    },
    "invoices": {
        "title": "Računi",
        "fields": (
            FieldSpec("number", "Številka", True, ("invoice", "number", "stevilka", "racun"), "text"),
            FieldSpec("customer", "Stranka", True, ("customer", "customer name", "stranka", "naziv"), "text"),
            FieldSpec("issue_date", "Datum", False, ("date", "issue", "datum"), "date"),
            FieldSpec("due_date", "Rok", False, ("due", "rok"), "date"),
            FieldSpec("total", "Znesek", False, ("total", "znesek", "amount"), "number"),
            FieldSpec("status", "Status", False, ("status",), "text"),
            FieldSpec("notes", "Opombe", False, ("notes", "opombe"), "text"),
        ),
    },
    "offers": {
        "title": "Ponudbe",
        "fields": (
            FieldSpec("number", "Številka", True, ("offer", "number", "stevilka", "ponudba"), "text"),
            FieldSpec("customer", "Stranka", True, ("customer", "customer name", "stranka"), "text"),
            FieldSpec("issue_date", "Datum", False, ("date", "datum"), "date"),
            FieldSpec("valid_until", "Veljavnost", False, ("valid", "veljavnost"), "date"),
            FieldSpec("total", "Znesek", False, ("total", "znesek"), "number"),
            FieldSpec("status", "Status", False, ("status",), "text"),
            FieldSpec("notes", "Opombe", False, ("notes", "opombe"), "text"),
        ),
    },
    "warehouse": {
        "title": "Skladišče",
        "fields": (
            FieldSpec("code", "Šifra", True, ("code", "sifra"), "text"),
            FieldSpec("name", "Naziv", True, ("name", "naziv"), "text"),
            FieldSpec("warehouse", "Skladišče", False, ("warehouse", "skladisce"), "text"),
            FieldSpec("qty", "Na zalogi", False, ("qty", "zaloga"), "number"),
            FieldSpec("reserved", "Rezervirano", False, ("reserved",), "number"),
            FieldSpec("free", "Prosto", False, ("free", "prosto"), "number"),
            FieldSpec("min_qty", "Minimalna zaloga", False, ("min",), "number"),
            FieldSpec("status", "Status", False, ("status",), "text"),
            FieldSpec("category", "Kategorija", False, ("category", "enota"), "text"),
        ),
    },
    "orders": {
        "title": "Naročila",
        "fields": (
            FieldSpec("number", "Številka", True, ("order", "number", "stevilka", "narocilo"), "text"),
            FieldSpec("customer", "Stranka", True, ("customer", "customer name", "stranka"), "text"),
            FieldSpec("issue_date", "Datum", False, ("date", "datum"), "date"),
            FieldSpec("delivery_date", "Dobava", False, ("delivery", "dobava"), "date"),
            FieldSpec("total", "Znesek", False, ("total", "znesek"), "number"),
            FieldSpec("status", "Status", False, ("status",), "text"),
            FieldSpec("notes", "Opombe", False, ("notes", "opombe"), "text"),
        ),
    },
    "suppliers": {
        "title": "Dobavitelji",
        "fields": (
            FieldSpec("name", "Naziv", True, ("name", "naziv", "supplier"), "text"),
            FieldSpec("tax_number", "Davčna", False, ("tax", "davcna"), "text"),
            FieldSpec("contact", "Kontakt", False, ("contact",), "text"),
            FieldSpec("phone", "Telefon", False, ("phone", "telefon"), "text"),
            FieldSpec("email", "Email", False, ("email",), "text"),
            FieldSpec("status", "Status", False, ("status",), "text"),
        ),
    },
    "purchase": {
        "title": "Nabava",
        "fields": (
            FieldSpec("number", "Številka", True, ("number", "po"), "text"),
            FieldSpec("supplier", "Dobavitelj", True, ("supplier", "dobavitelj"), "text"),
            FieldSpec("issue_date", "Datum", False, ("date", "datum"), "date"),
            FieldSpec("delivery_date", "Rok dobave", False, ("delivery", "rok"), "date"),
            FieldSpec("status", "Status", False, ("status",), "text"),
            FieldSpec("total", "Skupaj", False, ("total", "skupaj"), "number"),
        ),
    },
    "documents": {
        "title": "Dokumenti",
        "fields": (
            FieldSpec("name", "Ime", True, ("name", "ime"), "text"),
            FieldSpec("kind", "Tip", False, ("type", "tip"), "text"),
            FieldSpec("size", "Velikost", False, ("size",), "number"),
            FieldSpec("date", "Datum", False, ("date", "datum"), "date"),
            FieldSpec("linked", "Povezano z", False, ("linked",), "text"),
            FieldSpec("owner", "Lastnik", False, ("owner",), "text"),
        ),
    },
    "crm": {
        "title": "CRM",
        "fields": (
            FieldSpec("title", "Naslov", True, ("title", "naslov"), "text"),
            FieldSpec("company", "Podjetje", False, ("company",), "text"),
            FieldSpec("stage", "Stage", False, ("stage",), "text"),
            FieldSpec("status", "Status", False, ("status",), "text"),
            FieldSpec("priority", "Prioriteta", False, ("priority",), "text"),
            FieldSpec("salesperson", "Skrbnik", False, ("owner", "salesperson"), "text"),
            FieldSpec("value", "Vrednost", False, ("value",), "number"),
        ),
    },
    "reports": {
        "title": "Poročila",
        "fields": (
            FieldSpec("col1", "Stolpec 1", False, ("col1",), "text"),
        ),
    },
    "automation": {
        "title": "Automation",
        "fields": (
            FieldSpec("name", "Ime", True, ("name", "ime"), "text"),
            FieldSpec("trigger", "Sprožilec", False, ("trigger",), "text"),
            FieldSpec("enabled", "Aktivno", False, ("enabled",), "text"),
            FieldSpec("priority", "Prioriteta", False, ("priority",), "number"),
        ),
    },
}


def suggest_mapping(headers: list[str], module: str) -> dict[str, str]:
    specs = MODULES[module]["fields"]
    mapping = {}
    unused = list(headers)
    for spec in specs:
        match = ""
        for header in unused:
            token = _norm(header)
            if token == _norm(spec.label) or token == _norm(spec.key) or token in spec.aliases:
                match = header
                break
        if match:
            unused.remove(match)
        mapping[spec.key] = match
    return mapping
