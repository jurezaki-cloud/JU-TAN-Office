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
        value = str(value or "").strip()
        if not value:
            return []
        if "\r" in value or "\n" in value:
            raise ValueError("E-poštni naslov ne sme vsebovati preloma vrstice.")
        parsed = getaddresses([value])
        addresses = [address.strip() for _, address in parsed if address.strip()]
        if not addresses or any(address.count("@") != 1 for address in addresses):
            raise ValueError("Preveri e-poštne naslove prejemnikov.")
        return addresses

    @staticmethod
    def _html_body(body: str, sender: str) -> str:
        # Keep the e-mail self-contained: no remote tracking images and no
        # dependency on a mail client's CSS support. The JT mark is rendered
        # as text, so it remains crisp in Gmail/Outlook and dark mode.
        lines = (body or "").splitlines()
        paragraphs = "".join(
            '<div style="margin:0 0 12px;line-height:1.65">&nbsp;</div>' if not line.strip()
            else f'<div style="margin:0 0 12px;line-height:1.65">{html.escape(line)}</div>'
            for line in lines
        )
        sender_label = html.escape(sender or "JU-TAN studio")
        return (
            '<!doctype html><html><body style="margin:0;padding:0;background:#f3f7f6;'
            'font-family:Arial,Helvetica,sans-serif;color:#142b34">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
            'style="background:#f3f7f6;padding:28px 12px"><tr><td align="center">'
            '<table role="presentation" width="640" cellspacing="0" cellpadding="0" '
            'style="width:100%;max-width:640px;background:#ffffff;border:1px solid #dce9e2;'
            'border-radius:16px;overflow:hidden">'
            '<tr><td style="height:6px;background:#07966b;font-size:0">&nbsp;</td></tr>'
            '<tr><td style="padding:28px 32px 18px">'
            '<table role="presentation" width="100%"><tr>'
            '<td style="vertical-align:middle"><span style="display:inline-block;color:#0b2030;'
            'font-size:25px;font-weight:800;letter-spacing:-1px">JT</span>'
            '<span style="display:inline-block;margin-left:12px;padding-left:12px;'
            'border-left:1px solid #cad8d4;color:#0b2030;font-size:21px;font-weight:700">'
            'JU-TAN</span></td>'
            '<td align="right" style="color:#07966b;font-size:12px;font-weight:700;'
            'letter-spacing:.7px">POSLOVNI DOKUMENT</td></tr></table>'
            '</td></tr>'
            '<tr><td style="padding:0 32px"><div style="height:1px;background:#e3ece9">'
            '</div></td></tr>'
            '<tr><td style="padding:26px 32px 12px;font-size:15px">' + paragraphs + '</td></tr>'
            '<tr><td style="padding:8px 32px 30px">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
            'style="background:#f7faf9;border:1px solid #e0ebe7;border-radius:10px">'
            '<tr><td style="padding:18px 20px">'
            '<div style="color:#07966b;font-size:15px;font-weight:700;margin-bottom:6px">'
            + sender_label + '</div>'
            '<div style="color:#52666a;font-size:12px;line-height:1.7">'
            'JU-TAN studio, Tanja Hrup s.p.<br>'
            '<a href="mailto:info@ju-tan.com" style="color:#52666a;text-decoration:none">'
            'info@ju-tan.com</a> &nbsp;·&nbsp; '
            '<a href="https://www.ju-tan.com" style="color:#07966b;text-decoration:none;'
            'font-weight:700">www.ju-tan.com</a><br>'
            'Cerknica, Slovenija</div>'
            '</td></tr></table></td></tr>'
            '<tr><td style="padding:0 32px 24px;color:#879895;font-size:10px;line-height:1.5">'
            'To sporočilo je bilo poslano neposredno iz JU-TAN Office Enterprise. '
            'Dokument v priponki je namenjen navedenemu prejemniku.'
            '</td></tr></table></td></tr></table></body></html>'
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
