import base64
import hashlib
import hmac
import secrets

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.licensing.verifier import canonical_json


def normalize_key(value):
    return value.strip().upper().replace(" ", "")


def key_hash(value, pepper):
    return hmac.new(
        pepper.encode("utf-8"), normalize_key(value).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def generate_license_key():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    chunks = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return "JUTAN-" + "-".join(chunks)


def private_key_from_base64(value):
    raw = base64.b64decode(value, validate=True)
    return Ed25519PrivateKey.from_private_bytes(raw)


def sign_claims(claims, private_key_base64):
    signature = private_key_from_base64(private_key_base64).sign(canonical_json(claims))
    return {"claims": claims, "signature": base64.b64encode(signature).decode("ascii")}


def generate_signing_keys():
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_raw = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return (
        base64.b64encode(private_raw).decode("ascii"),
        base64.b64encode(public_raw).decode("ascii"),
    )
