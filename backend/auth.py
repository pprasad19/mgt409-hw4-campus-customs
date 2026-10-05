"""Password hashing and session tokens for Campus Customs.

Passwords are never stored or logged in plaintext. Only a salted PBKDF2-HMAC-SHA256
digest is written to users.password_hash, and verification is constant-time.

Two hash encodings are supported:

    pbkdf2_sha256$<salt>$<hex>                 legacy, seeded rows, 120_000 iterations
    pbkdf2_sha256$<iterations>$<salt>$<hex>    written for every new password

The seeded database stores the 3-field form with no iteration count, so the count
is pinned by LEGACY_ITERATIONS. New hashes record their own iteration count, which
lets the work factor be raised later without locking existing users out.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from dataclasses import dataclass

from env_file import load_env

ALGORITHM = "pbkdf2_sha256"

# OWASP's current floor for PBKDF2-HMAC-SHA256 is 600_000 iterations.
ITERATIONS = 600_000

# The seeded rows were written at this count and do not record it themselves.
LEGACY_ITERATIONS = 120_000

SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8

# Sliding expiry: the window is short because there is no server-side
# revocation, so expiry is the only kill switch for a stolen token. Every
# authenticated response carries a freshly issued token, which resets the
# clock while someone is active and lets it run out once they go idle.
TOKEN_TTL_SECONDS = 60 * 60

# Absolute cap on a session, measured from the original login and carried
# through every renewal. Without it, sliding expiry has no upper bound: an
# attacker holding a stolen token could keep it alive forever just by using
# it before each idle timeout. Renewal cannot push a session past this.
ABSOLUTE_SESSION_SECONDS = 60 * 60 * 12

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Signing key for session tokens. Set CAMPUS_CUSTOMS_SECRET to keep sessions
# valid across restarts; otherwise a fresh key is generated each boot and old
# tokens simply stop validating.
#
# The .env is loaded here rather than trusting another module to have done it.
# It previously worked only because main.py imports agent just before auth, so
# importing auth on its own generated a throwaway key and sessions quietly
# stopped surviving restarts.
load_env()
SECRET_KEY = os.environ.get("CAMPUS_CUSTOMS_SECRET") or secrets.token_hex(32)


class AuthError(Exception):
    """Raised for invalid credentials or malformed signup input."""


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash. The plaintext is never retained."""
    salt = secrets.token_hex(SALT_BYTES)
    digest = _pbkdf2(password, salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check of a candidate password against a stored hash."""
    try:
        algorithm, iterations, salt, digest = _parse(stored)
    except (ValueError, AttributeError):
        return False

    if algorithm != ALGORITHM:
        return False

    candidate = _pbkdf2(password, salt, iterations)
    return hmac.compare_digest(candidate, digest)


def needs_rehash(stored: str) -> bool:
    """True when a stored hash uses a weaker work factor than current policy."""
    try:
        _, iterations, _, _ = _parse(stored)
    except (ValueError, AttributeError):
        return True
    return iterations < ITERATIONS


def _parse(stored: str) -> tuple[str, int, str, str]:
    parts = stored.split("$")
    if len(parts) == 4:
        algorithm, iterations, salt, digest = parts
        return algorithm, int(iterations), salt, digest
    if len(parts) == 3:
        algorithm, salt, digest = parts
        return algorithm, LEGACY_ITERATIONS, salt, digest
    raise ValueError("unrecognized password hash format")


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()


# --------------------------------------------------------------------------
# Signup validation
# --------------------------------------------------------------------------


def validate_signup(first_name: str, last_name: str, email: str, password: str) -> None:
    """Raise AuthError describing the first problem found, if any."""
    if not first_name.strip():
        raise AuthError("First name is required.")
    if not last_name.strip():
        raise AuthError("Last name is required.")
    if not EMAIL_PATTERN.match(email.strip()):
        raise AuthError("Enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")


# --------------------------------------------------------------------------
# Session tokens (stateless, HMAC-signed)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    issued_at: int
    """Time of the original login, preserved across every renewal."""


def create_token(user_id: int, issued_at: int | None = None) -> str:
    """Mint a token.

    Pass the original `issued_at` when renewing so the absolute session cap
    keeps counting from the real login rather than restarting.
    """
    now = int(time.time())
    origin = now if issued_at is None else issued_at

    # Never advertise an expiry beyond the absolute cap.
    expires = min(now + TOKEN_TTL_SECONDS, origin + ABSOLUTE_SESSION_SECONDS)

    payload = {"sub": user_id, "iat": origin, "exp": expires}
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body)}"


def read_token(token: str) -> TokenClaims | None:
    """Return the claims for a valid token, else None.

    A token is rejected when the signature does not verify, when it is
    malformed, when it has passed its idle expiry, or when the session has
    run past ABSOLUTE_SESSION_SECONDS from the original login.
    """
    try:
        body, signature = token.split(".")
    except (ValueError, AttributeError):
        return None

    if not hmac.compare_digest(_sign(body), signature):
        return None

    try:
        payload = json.loads(_b64decode(body))
    except (ValueError, json.JSONDecodeError):
        return None

    now = time.time()

    if payload.get("exp", 0) < now:
        return None

    user_id = payload.get("sub")
    issued_at = payload.get("iat")
    if not isinstance(user_id, int) or not isinstance(issued_at, int):
        # Tokens minted before the absolute cap existed have no iat. Fail
        # closed rather than grant an uncapped session.
        return None

    if now - issued_at > ABSOLUTE_SESSION_SECONDS:
        return None

    return TokenClaims(user_id=user_id, issued_at=issued_at)


def _sign(body: str) -> str:
    return _b64encode(
        hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).digest()
    )


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
