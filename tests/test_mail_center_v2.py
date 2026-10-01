"""Mail Center keeps BCC private while recording successful sends."""
import sqlite3

from app.services import mail_center as module


class Connection:
    def __init__(self, raw):
        self.raw = raw
    def execute(self, *args):
        return self.raw.execute(*args)
    def commit(self):
        self.raw.commit()
    def close(self):
        pass


class FakeSMTP:
    def __init__(self):
        self.message = None
        self.recipients = None
    def send_message(self, message, to_addrs):
        self.message = message
        self.recipients = to_addrs
    def quit(self):
        pass


def test_bcc_html_history_only_after_send(monkeypatch):
    raw = sqlite3.connect(":memory:")
    smtp = FakeSMTP()
    center = module.MailCenter()
    monkeypatch.setattr(module, "require", lambda action: None)
    monkeypatch.setattr(module, "audit", lambda *args: None)
    monkeypatch.setattr(module.db, "connect", lambda: Connection(raw))
    monkeypatch.setattr(center, "profile", lambda: {
        "host": "example.test", "port": 587, "security": "STARTTLS",
        "sender_email": "studio@example.test", "sender_name": "JU-TAN",
        "reply_to": "",
    })
    monkeypatch.setattr(center, "_connect", lambda profile: smtp)
    center.send(to="client@example.test", cc="copy@example.test",
                bcc="hidden@example.test", subject="Račun", body="<h1>Preveri</h1>")
    assert smtp.recipients == ["client@example.test", "copy@example.test", "hidden@example.test"]
    assert "Bcc" not in smtp.message
    assert "&lt;h1&gt;" in smtp.message.get_body(preferencelist=("html",)).get_content()
    assert center.history()[0][3] == "Poslano"
    raw.close()
