import json

from app.core.constants import LICENSE_FILE


class LicenseStorage:
    def __init__(self, path=LICENSE_FILE):
        self.path = path

    def load(self):
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError, TypeError):
            return None
        return value if isinstance(value, dict) else None

    def save(self, value):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)

    def clear(self):
        self.path.unlink(missing_ok=True)
