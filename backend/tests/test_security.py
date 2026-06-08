import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    hashed = hash_password("A-secure-password-123")

    assert hashed != "A-secure-password-123"
    assert verify_password("A-secure-password-123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_type_is_enforced() -> None:
    token = create_access_token("42")

    assert decode_token(token, "access")["sub"] == "42"
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, "refresh")

