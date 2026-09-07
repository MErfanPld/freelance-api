from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes,
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    jti: str,
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(
            days=settings.refresh_token_expire_days,
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def _get_fernet() -> Fernet:
    return Fernet(settings.encryption_key.encode("utf-8"))


def encrypt_value(value: str) -> str:
    return _get_fernet().encrypt(
        value.encode("utf-8"),
    ).decode("utf-8")


def decrypt_value(encrypted_value: str) -> str:
    try:
        return _get_fernet().decrypt(
            encrypted_value.encode("utf-8"),
        ).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid encrypted value") from exc
