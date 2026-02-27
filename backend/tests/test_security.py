"""
Unit tests for core security module — JWT tokens, password hashing.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_hash(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2  # bcrypt uses random salt


class TestJWT:
    def test_create_access_token(self):
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_valid_access_token(self):
        token = create_access_token({"sub": "user-123", "role": "admin"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_decode_expired_token(self):
        token = create_access_token(
            {"sub": "user-123"},
            expires_delta=timedelta(seconds=-10),
        )
        payload = decode_token(token)
        assert payload is None

    def test_decode_invalid_token(self):
        payload = decode_token("this-is-not-a-valid-token")
        assert payload is None

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_token_pair(self):
        tokens = create_token_pair(
            user_id="user-123",
            organization_id="org-456",
            role="admin",
        )
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        # Validate access token contents
        access_payload = decode_token(tokens["access_token"])
        assert access_payload["sub"] == "user-123"
        assert access_payload["org_id"] == "org-456"
        assert access_payload["role"] == "admin"
        assert access_payload["type"] == "access"

        # Validate refresh token contents
        refresh_payload = decode_token(tokens["refresh_token"])
        assert refresh_payload["type"] == "refresh"


class TestExceptions:
    def test_app_exception_defaults(self):
        from app.core.exceptions import AppException

        exc = AppException("Something went wrong")
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert str(exc) == "Something went wrong"

    def test_not_found_exception(self):
        from app.core.exceptions import NotFoundException

        exc = NotFoundException("Equipment", "abc-123")
        assert exc.status_code == 404
        assert "abc-123" in exc.message

    def test_unauthorized_exception(self):
        from app.core.exceptions import UnauthorizedException

        exc = UnauthorizedException()
        assert exc.status_code == 401

    def test_forbidden_exception(self):
        from app.core.exceptions import ForbiddenException

        exc = ForbiddenException()
        assert exc.status_code == 403

    def test_conflict_exception(self):
        from app.core.exceptions import ConflictException

        exc = ConflictException("Email already exists")
        assert exc.status_code == 409

    def test_ml_model_exception(self):
        from app.core.exceptions import MLModelException

        exc = MLModelException("Model not found")
        assert exc.status_code == 503
