from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.database.invoice_repository import invoice_repository
from app.database.payment_repository import payment_repository


@dataclass(frozen=True)
class BankMatch:
    date: str
    amount: float
    reference: str
    description: str
    invoice_id: int | None
    invoice_number: str
    confidence: str


def _amount(value: str) -> float:
    text = (value or '').strip().replace('\u00a0', '').replace(' ', '')
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    return float(text or 0)


def _date(value: str) -> str:
    text = (value or '').strip()
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f'Neveljaven datum: {text}')


def read_csv(path: str) -> list[dict]:
    raw = Path(path).read_text(encoding='utf-8-sig')
    dialect = csv.Sniffer().sniff(raw[:4096], delimiters=';,\t')
    rows = list(csv.DictReader(raw.splitlines(), dialect=dialect))
    aliases = {
        'date': ('datum', 'date', 'datum knjiženja', 'datum knjizenja'),
        'amount': ('znesek', 'amount', 'dobro', 'priliv'),
        'reference': ('sklic', 'reference', 'referenca'),
        'description': ('namen', 'opis', 'description', 'plačnik', 'placnik'),
    }
    out = []
    for row in rows:
        normalized = {str(k or '').strip().casefold(): str(v or '').strip() for k, v in row.items()}
        def pick(name):
            return next((normalized[a] for a in aliases[name] if a in normalized), '')
        amount = _amount(pick('amount'))
        if amount <= 0:
            continue
        out.append({'date': _date(pick('date')), 'amount': amount,
                    'reference': pick('reference'), 'description': pick('description')})
    return out


def propose_matches(rows: list[dict]) -> list[BankMatch]:
    invoices = invoice_repository.get_all()
    result = []
    for tx in rows:
        haystack = f"{tx['reference']} {tx['description']}".casefold()
        candidates = []
        for inv in invoices:
            if str(inv[5] or '') in ('Osnutek', 'Storniran', 'Plačan'):
                continue
            remaining = payment_repository.remaining(inv[0], inv[4] or 0)
            number = str(inv[1] or '')
            number_hit = number and re.search(rf'(?<!\w){re.escape(number.casefold())}(?!\w)', haystack)
            amount_hit = abs(remaining - float(tx['amount'])) < 0.01
            if number_hit and amount_hit:
                candidates.append((3, inv, 'visoka'))
            elif number_hit:
                candidates.append((2, inv, 'srednja'))
            elif amount_hit:
                candidates.append((1, inv, 'nizka'))
        candidates.sort(key=lambda item: item[0], reverse=True)
        best = candidates[0] if candidates else None
        result.append(BankMatch(tx['date'], float(tx['amount']), tx['reference'], tx['description'],
                                best[1][0] if best else None, str(best[1][1]) if best else '',
                                best[2] if best else 'brez ujemanja'))
    return result


def confirm_match(match: BankMatch) -> int:
    if match.invoice_id is None:
        raise ValueError('Transakcija nima izbranega računa.')
    payment_id = payment_repository.add(match.invoice_id, match.date, match.amount, 'Bančno nakazilo',
                                        f'Uvoz banke: {match.reference} {match.description}'.strip())
    invoice = invoice_repository.get_by_id(match.invoice_id)
    payment_repository.sync_invoice_status(match.invoice_id, invoice[9] or 0)
    return payment_id
