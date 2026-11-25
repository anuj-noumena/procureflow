import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import jwt


def derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode(), salt=salt, n=2**15, r=8, p=3, maxmem=64 * 1024**2
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return "scrypt-v1$" + salt.hex() + "$" + derive(password, salt).hex()


def verify(password: str, stored: str) -> bool:
    scheme, salt, digest = stored.split("$")
    return scheme == "scrypt-v1" and hmac.compare_digest(
        derive(password, bytes.fromhex(salt)), bytes.fromhex(digest)
    )


def issue(member: str, user: str, key: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user,
            "mid": member,
            "iss": "procureflow",
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        key,
        algorithm="HS256",
    )


def claims(token: str, key: str):
    return jwt.decode(
        token,
        key,
        algorithms=["HS256"],
        issuer="procureflow",
        options={"require": ["sub", "mid", "iat", "exp"]},
    )
