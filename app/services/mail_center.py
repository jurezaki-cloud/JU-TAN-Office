from __future__ import annotations

# JU-TAN Mail Center
import smtplib
import ssl
import html
import mimetypes
from email.message import EmailMessage
from email.utils import getaddresses
from pathlib import Path

from app.core.permissions import audit, require
from app.database.company_repository import company_repository
from app.database.database import db


class MailCenter:
    def settings(self) -> dict:
        from app.modules.settings.settings_controller import SettingsController
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

    @staticmethod
    def _addresses(value: str) -> list[str]:
        if "\r" in value or "\n" in value:
            raise ValueError("E-poštni naslov ne sme vsebovati preloma vrstice.")
        parsed = getaddresses([value or ""])
        addresses = [address.strip() for _, address in parsed]
        if any(not address or address.count("@") != 1 for address in addresses):
            raise ValueError("Preveri e-poštne naslove prejemnikov.")
        return addresses

    @staticmethod
    def _html_body(body: str, sender: str) -> str:
        paragraphs = "".join(
            f'<p style="margin:0 0 14px">{html.escape(line)}</p>'
            for line in (body or "").splitlines()
        )
        return (
            '<html><body style="margin:0;background:#f3f7f6;padding:24px">'
            '<div style="max-width:640px;margin:auto;background:#fff;border-radius:12px;'
            'border:1px solid #dce9e2;padding:30px;color:#142b34;font:16px Arial,sans-serif">'
            '<div style="color:#09865a;font-size:22px;font-weight:bold;margin-bottom:22px">'
            'JU-TAN Studio</div>' + paragraphs +
            '<div style="border-top:2px solid #19a974;margin-top:26px;padding-top:16px;'
            'color:#52666a;font-size:13px">' + html.escape(sender) +
            '</div></div></body></html>'
        )

    def _record_sent(self, to: str, cc: str, bcc: str, subject: str, paths) -> None:
        conn = db.connect()
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS mail_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                recipient TEXT NOT NULL, cc TEXT, bcc TEXT,
                subject TEXT NOT NULL, attachments TEXT, status TEXT NOT NULL
            )""")
            conn.execute("""INSERT INTO mail_history
                (recipient, cc, bcc, subject, attachments, status)
                VALUES (?, ?, ?, ?, ?, 'Poslano')""",
                (to, cc, bcc, subject, ", ".join(path.name for path in paths)))
            conn.commit()
        finally:
            conn.close()

    def history(self, limit: int = 30):
        require("read")
        conn = db.connect()
        try:
            if not conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mail_history'"
            ).fetchone():
                return []
            return conn.execute("""SELECT sent_at, recipient, subject, status
                FROM mail_history ORDER BY id DESC LIMIT ?""",
                (min(max(limit, 1), 100),)).fetchall()
        finally:
            conn.close()

    def send(self, *, to: str, subject: str, body: str, attachments=(),
             cc: str = "", bcc: str = "") -> None:
        require("write")
        p = self.profile()
        self._validate(p)
        recipients = self._addresses(to)
        copies = self._addresses(cc)
        hidden = self._addresses(bcc)
        if not recipients:
            raise ValueError("Vnesite prejemnika.")
        message = EmailMessage()
        message["From"] = f'{p["sender_name"]} <{p["sender_email"]}>' if p["sender_name"] else p["sender_email"]
        message["To"] = ", ".join(recipients)
        if copies:
            message["Cc"] = ", ".join(copies)
        message["Subject"] = (subject or "").strip()
        if p["reply_to"]:
            message["Reply-To"] = p["reply_to"]
        message.set_content(body or "")
        message.add_alternative(self._html_body(body, p["sender_name"]), subtype="html")
        paths = [Path(item) for item in attachments]
        for path in paths:
            if not path.is_file():
                raise FileNotFoundError(f"Priponka ne obstaja: {path}")
            media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            main, subtype = media_type.split("/", 1)
            message.add_attachment(path.read_bytes(), maintype=main,
                                   subtype=subtype, filename=path.name)
        server = self._connect(p)
        try:
            server.send_message(message, to_addrs=recipients + copies + hidden)
        finally:
            server.quit()
        try:
            self._record_sent(", ".join(recipients), ", ".join(copies),
                              ", ".join(hidden), message["Subject"], paths)
        except Exception:
            from app.core.logger import logger
            logger.exception("Email sent, but history could not be saved")
        audit("email", f"to:{message['To']}; subject:{subject}; attachments:{len(paths)}")


mail_center = MailCenter()
