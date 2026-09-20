import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from license_server.security import generate_license_key, key_hash, sign_claims


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LicenseError(RuntimeError):
    pass


class LicenseService:
    def __init__(self, database, signing_key, pepper, warning_days=14, limit_days=21, now=None):
        self.database = database
        self.signing_key = signing_key
        self.pepper = pepper
        self.warning_days = warning_days
        self.limit_days = limit_days
        self.now = now or utc_now

    def create_license(self, company_name, email, plan, max_devices, valid_until):
        raw_key = generate_license_key()
        customer_id, license_id = str(uuid4()), str(uuid4())
        current = self.now()
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        if valid_until <= current:
            raise LicenseError("Datum veljavnosti mora biti v prihodnosti.")
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO customers VALUES (?, ?, ?, ?)",
                (customer_id, company_name.strip(), str(email).lower(), iso(current)),
            )
            connection.execute(
                "INSERT INTO licenses VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                (
                    license_id, customer_id, key_hash(raw_key, self.pepper),
                    raw_key[-4:], plan, max_devices, iso(valid_until), iso(current),
                ),
            )
            self._audit(connection, "license_created", license_id, {"plan": plan})
        return {"license_id": license_id, "license_key": raw_key, "key_hint": raw_key[-4:]}

    def activate(self, request):
        current = self.now()
        with self.database.transaction(immediate=True) as connection:
            license_row = connection.execute(
                """SELECT l.*, c.company_name, c.email FROM licenses l
                   JOIN customers c ON c.id=l.customer_id WHERE l.key_hash=?""",
                (key_hash(request.license_key, self.pepper),),
            ).fetchone()
            self._validate_license(license_row, current)
            if license_row["email"].casefold() != str(request.email).casefold():
                raise LicenseError("Licenčni ključ in e-poštni naslov se ne ujemata.")

            existing = connection.execute(
                "SELECT * FROM activations WHERE license_id=? AND installation_id=?",
                (license_row["id"], request.installation_id),
            ).fetchone()
            if not existing or existing["status"] != "active":
                active_count = connection.execute(
                    "SELECT COUNT(*) FROM activations WHERE license_id=? AND status='active'",
                    (license_row["id"],),
                ).fetchone()[0]
                if active_count >= license_row["max_devices"]:
                    raise LicenseError("Doseženo je največje dovoljeno število naprav.")
            if not existing:
                activation_id = str(uuid4())
                connection.execute(
                    """INSERT INTO activations
                       (id, license_id, installation_id, platform, app_version, status,
                        activated_at, last_seen_at) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)""",
                    (activation_id, license_row["id"], request.installation_id,
                     request.platform, request.app_version, iso(current), iso(current)),
                )
            else:
                activation_id = existing["id"]
                connection.execute(
                    """UPDATE activations SET status='active', platform=?, app_version=?,
                       last_seen_at=?, deactivated_at=NULL WHERE id=?""",
                    (request.platform, request.app_version, iso(current), activation_id),
                )
            self._audit(connection, "activation_succeeded", activation_id, None)
            return self._certificate(license_row, activation_id, request.installation_id, current)

    def heartbeat(self, request):
        current = self.now()
        with self.database.transaction(immediate=True) as connection:
            row = connection.execute(
                """SELECT a.id activation_id, a.installation_id, a.status activation_status,
                          l.* FROM activations a JOIN licenses l ON l.id=a.license_id
                   WHERE a.id=? AND a.installation_id=?""",
                (request.activation_id, request.installation_id),
            ).fetchone()
            self._validate_license(row, current)
            if row["activation_status"] != "active":
                raise LicenseError("Aktivacija ni več veljavna.")
            connection.execute(
                "UPDATE activations SET last_seen_at=?, app_version=?, platform=? WHERE id=?",
                (iso(current), request.app_version, request.platform, request.activation_id),
            )
            return self._certificate(row, request.activation_id, request.installation_id, current)

    def deactivate(self, activation_id, installation_id):
        current = self.now()
        with self.database.transaction(immediate=True) as connection:
            result = connection.execute(
                """UPDATE activations SET status='deactivated', deactivated_at=?
                   WHERE id=? AND installation_id=? AND status='active'""",
                (iso(current), activation_id, installation_id),
            )
            if result.rowcount != 1:
                raise LicenseError("Aktivacije ni mogoče deaktivirati.")
            self._audit(connection, "activation_deactivated", activation_id, None)

    def list_licenses(self):
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT l.id, c.company_name, c.email, l.key_hint, l.plan,
                          l.max_devices, l.status, l.valid_until,
                          SUM(CASE WHEN a.status='active' THEN 1 ELSE 0 END) active_devices,
                          MAX(a.last_seen_at) last_seen_at
                   FROM licenses l JOIN customers c ON c.id=l.customer_id
                   LEFT JOIN activations a ON a.license_id=l.id
                   GROUP BY l.id ORDER BY l.created_at DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

    def list_activations(self, license_id):
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT id, installation_id, platform, app_version, status,
                          activated_at, last_seen_at, deactivated_at
                   FROM activations WHERE license_id=? ORDER BY activated_at DESC""",
                (license_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def set_license_status(self, license_id, status):
        current = self.now()
        with self.database.transaction(immediate=True) as connection:
            result = connection.execute(
                "UPDATE licenses SET status=? WHERE id=?", (status, license_id)
            )
            if result.rowcount != 1:
                raise LicenseError("Licenca ne obstaja.")
            self._audit(
                connection, "license_status_changed", license_id,
                {"status": status, "changed_at": iso(current)},
            )

    def _validate_license(self, row, current):
        if not row:
            raise LicenseError("Licenca ne obstaja.")
        if row["status"] != "active":
            raise LicenseError("Licenca ni aktivna.")
        valid_until = datetime.fromisoformat(row["valid_until"].replace("Z", "+00:00"))
        if current > valid_until:
            raise LicenseError("Licenca je potekla.")

    def _certificate(self, license_row, activation_id, installation_id, current):
        valid_until = datetime.fromisoformat(
            license_row["valid_until"].replace("Z", "+00:00")
        )
        offline_limit = min(current + timedelta(days=self.limit_days), valid_until)
        warning = min(current + timedelta(days=self.warning_days), offline_limit)
        claims = {
            "license_id": license_row["id"],
            "activation_id": activation_id,
            "installation_id": installation_id,
            "plan": license_row["plan"],
            "status": license_row["status"],
            "valid_until": iso(valid_until),
            "offline_warning_at": iso(warning),
            "offline_until": iso(offline_limit),
            "issued_at": iso(current),
        }
        return sign_claims(claims, self.signing_key)

    @staticmethod
    def _audit(connection, event_type, entity_id, detail):
        connection.execute(
            "INSERT INTO audit_log(event_type, entity_id, detail, created_at) VALUES (?, ?, ?, ?)",
            (event_type, entity_id, json.dumps(detail) if detail else None, iso(utc_now())),
        )
