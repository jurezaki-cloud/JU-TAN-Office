# JU-TAN License & Control Center

## Scope

The licensing subsystem records only the technical data needed to enforce a
license: license and activation IDs, a pseudonymous installation ID, platform,
application version, activation time and last successful contact. It does not
upload customers, invoices, offers, payments, files or user activity.

## Local development

Generate Ed25519 keys and random secrets:

```bash
python -m license_server.generate_keys
```

Copy the printed values into environment variables. Keep the signing key,
pepper and admin token on the server. Only `JU_TAN_LICENSE_PUBLIC_KEY` is safe
to include in a desktop build.

Install and start the API:

```bash
python -m pip install -r license_server/requirements.txt
python -m uvicorn license_server.main:app --host 127.0.0.1 --port 8000
```

The API refuses to start when a required secret is missing. For a local
desktop test set:

```text
JU_TAN_LICENSE_REQUIRED=1
JU_TAN_LICENSE_SERVER_URL=http://127.0.0.1:8000
JU_TAN_LICENSE_PUBLIC_KEY=<public key generated above>
```

Create a license with an authenticated request to `POST /v1/admin/licenses`.
The plaintext license key is returned only at creation time; the database
stores an HMAC hash and the last four characters for support.

## Production checklist

- Put the API behind HTTPS and a reverse proxy.
- Store secrets in the hosting platform's secret manager.
- Restrict and rotate the admin token; add MFA before exposing a web dashboard.
- Back up and test restoration of the license database.
- Add rate limiting at the proxy and monitoring for failed activations.
- Embed the public key in release builds and enable `JU_TAN_LICENSE_REQUIRED`.
- Publish a privacy notice and retention policy before collecting telemetry.
- Keep detailed heartbeat/audit data only as long as operationally necessary.

## Behaviour during outages

A refreshed certificate is valid offline for 21 days and starts warning after
14 days. A server outage therefore does not immediately block legitimate work.
The server never receives business documents.
