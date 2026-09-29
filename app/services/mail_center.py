from __future__ import annotations

# JU-TAN Mail Center
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from app.core.permissions import audit, require
from app.database.company_repository import company_repository
from app.modules.settings.settings_controller import SettingsController


class MailCenter:
    def settings(self) -> dict:
        ctrl = SettingsController()
        extras = ctrl.load_extras()
        data = dict(extras.get("mail") or {})
        data["password"] = ctrl.secrets().get("smtp_password", "")
        return data

    def profile(self) -> dict:
        data = self.settings()
        company = company_repository.get_company()
        return {
            "host": str(data.get("host") or "").strip(),
            "port": int(data.get("port") or 587),
            "username": str(data.get("username") or "").strip(),
            "password": str(data.get("password") or ""),
            "security": str(data.get("security") or "STARTTLS").upper(),
            "sender_name": str(data.get("sender_name") or (company[1] if company else "JU-TAN Studio")).strip(),
            "sender_email": str(data.get("sender_email") or (company[11] if company else "")).strip(),
            "reply_to": str(data.get("reply_to") or "").strip(),
        }

    def _validate(self, p: dict) -> None:
        if not p["host"] or not p["port"]:
            raise ValueError("V Nastavitvah najprej vnesite SMTP strežnik in vrata.")
        if not p["sender_email"]:
            raise ValueError("V Nastavitvah določite e-poštni naslov pošiljatelja.")
        if p["security"] not in {"STARTTLS", "SSL", "NONE"}:
            raise ValueError("Neveljavna vrsta SMTP zaščite.")

    def _connect(self, p: dict):
        context = ssl.create_default_context()
        if p["security"] == "SSL":
            server = smtplib.SMTP_SSL(p["host"], p["port"], timeout=20, context=context)
        else:
            server = smtplib.SMTP(p["host"], p["port"], timeout=20)
            server.ehlo()
            if p["security"] == "STARTTLS":
                server.starttls(context=context)
                server.ehlo()
        if p["username"]:
            server.login(p["username"], p["password"])
        return server

    def test_connection(self) -> None:
        p = self.profile()
        self._validate(p)
        server = self._connect(p)
        try:
            server.noop()
        finally:
            server.quit()

    def send(self, *, to: str, subject: str, body: str, attachments=()) -> None:
        require("write")
        p = self.profile()
        self._validate(p)
        recipient = (to or "").strip()
        if "@" not in recipient:
            raise ValueError("Vnesite veljaven e-poštni naslov prejemnika.")
        message = EmailMessage()
        message["From"] = f'{p["sender_name"]} <{p["sender_email"]}>' if p["sender_name"] else p["sender_email"]
        message["To"] = recipient
        message["Subject"] = (subject or "").strip()
        if p["reply_to"]:
            message["Reply-To"] = p["reply_to"]
        message.set_content(body or "")
        paths = [Path(item) for item in attachments]
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(f"Priponka ne obstaja: {path}")
            message.add_attachment(
                path.read_bytes(),
                maintype="application",
                subtype="pdf",
                filename=path.name,
            )
        server = self._connect(p)
        try:
            server.send_message(message)
        finally:
            server.quit()
        audit("email", f"to:{recipient}; subject:{subject}; attachments:{len(paths)}")


mail_center = MailCenter()
