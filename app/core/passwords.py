"""Hash gesel: Argon2id, sicer scrypt (stdlib) + sol + politika."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets

MIN_LENGTH = 10
MAX_LENGTH = 128


def validate_policy(password: str) -> str:
    text = password or ""
    if len(text) < MIN_LENGTH:
        raise ValueError(f"Geslo mora imeti vsaj {MIN_LENGTH} znakov.")
    if len(text) > MAX_LENGTH:
        raise ValueError("Geslo je predolgo.")
    if not re.search(r"[a-z]", text):
        raise ValueError("Geslo potrebuje malo črko.")
    if not re.search(r"[A-Z]", text):
        raise ValueError("Geslo potrebuje veliko črko.")
    if not re.search(r"\d", text):
        raise ValueError("Geslo potrebuje številko.")
    return text


def hash_password(password: str) -> str:
    validate_policy(password)
    try:
        from argon2 import PasswordHasher
        from argon2.low_level import Type

        hasher = PasswordHasher(
            time_cost=2,
            memory_cost=64 * 1024,
            parallelism=2,
            hash_len=32,
            type=Type.ID,
        )
        return "argon2id:" + hasher.hash(password)
    except Exception:
        salt = os.urandom(16)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
        return "scrypt:" + base64.b64encode(salt).decode("ascii") + ":" + base64.b64encode(digest).decode("ascii")


def verify_password(password: str, stored: str) -> bool:
    if not stored or not password:
        return False
    try:
        if stored.startswith("argon2id:"):
            from argon2 import PasswordHasher
            from argon2.exceptions import VerifyMismatchError

            try:
                PasswordHasher().verify(stored.split(":", 1)[1], password)
                return True
            except (VerifyMismatchError, Exception):
                return False
        if stored.startswith("scrypt:"):
            _, salt_b64, digest_b64 = stored.split(":", 2)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(digest_b64)
            digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
            return hmac.compare_digest(digest, expected)
    except Exception:
        return False
    return False


def new_salt() -> str:
    return secrets.token_hex(16)
