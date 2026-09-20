# JU-TAN Office licensing

The desktop client uses a privacy-preserving device fingerprint and communicates only with an HTTPS API. Raw hardware identifiers are never transmitted.

## API contract (v1)

- `POST /v1/licenses/activate` binds a valid key to a device and returns a server-issued activation token.
- `POST /v1/licenses/validate` checks the token, device, subscription and allowed-device limit.
- `POST /v1/licenses/deactivate` releases the device slot.

Responses consumed by the client contain `status`, `license_id`, `company_name`, `activation_token`, `checked_at`, `valid_until`, and `grace_until`.

## Security rules

- Production API URL must use HTTPS.
- The database and administrative API remain server-side; no database credentials ship with the desktop app.
- A server rejection (blocked, expired or device limit) never falls back to offline grace.
- Grace mode is allowed only for temporary network/server failures and only until `grace_until`.
- Local state is written atomically with owner-only permissions where supported.

The startup UI gate stays disabled until the server API and activation dialog are deployed and tested. This keeps the current production build usable while the feature branch is under development.
