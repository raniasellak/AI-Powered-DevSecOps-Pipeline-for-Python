
import uuid

import jwt
import pytest

from backend.app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password_is_rejected():
    hashed = hash_password("StrongPassword123!")

    assert not verify_password("WrongPassword123!", hashed)


def test_invalid_password_hash_is_rejected():
    assert not verify_password("password", "invalid-hash")


def test_access_token_is_valid():
    user_id = uuid.uuid4()

    token = create_access_token(user_id, "freelance")
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "freelance"
    assert payload["type"] == "access"


def test_invalid_token_is_rejected():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid.token.value")


def test_refresh_token_cannot_be_used_as_access_token():
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "iat": 2000000000,
            "exp": 2100000000,
        },
        "test-secret-key-for-invoicepay-only",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
