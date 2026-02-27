"""
Integration tests for auth endpoints.
Uses mock database to avoid requiring a live PG instance.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import create_token_pair, hash_password
from app.db.models.organization import UserRole


# ── Helper ────────────────────────────────────────────────────
def make_mock_user(
    user_id=None, email="testing@test.com", role=UserRole.ADMIN,
    org_id=None, is_active=True, password="testpass123",
):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.organization_id = org_id or uuid.uuid4()
    user.email = email
    user.full_name = "Test User"
    user.role = role
    user.is_active = is_active
    user.hashed_password = hash_password(password)
    user.last_login = None
    user.created_at = datetime.now(timezone.utc)
    return user


# ── Tests ─────────────────────────────────────────────────────
class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client):
        """Login with missing fields should return 422."""
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_short_password(self, client):
        """Password less than 8 chars rejected by schema validation."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "short"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "longpassword"},
        )
        assert resp.status_code == 422


class TestRegisterEndpoint:
    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client):
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client):
        """Roles outside (admin|engineer|viewer) should be rejected."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@test.com",
                "password": "testpass123",
                "full_name": "New User",
                "organization_name": "Test Org",
                "role": "superadmin",
            },
        )
        assert resp.status_code == 422


class TestProtectedEndpoints:
    @pytest.mark.asyncio
    async def test_no_auth_header_returns_401(self, client):
        """Requests without Authorization should return 401."""
        resp = await client.get("/api/v1/equipment")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client):
        resp = await client.get(
            "/api/v1/equipment",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client):
        from datetime import timedelta
        from app.core.security import create_access_token

        expired = create_access_token(
            {"sub": str(uuid.uuid4()), "org_id": str(uuid.uuid4()), "role": "admin"},
            expires_delta=timedelta(seconds=-10),
        )
        resp = await client.get(
            "/api/v1/equipment",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code in (401, 403)


class TestRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client, admin_token):
        """Using an access token for refresh should fail."""
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": admin_token},
        )
        # Access token type != "refresh"
        assert resp.status_code in (401, 403)
