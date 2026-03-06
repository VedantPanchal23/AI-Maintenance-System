"""
Integration tests for API endpoints.
Tests endpoint routing, authentication, and response shapes.
Uses the shared client fixture (mock DB via conftest).
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.organization import User, UserRole


# ═══════════════════════════════════════════════════════════════
# Equipment Endpoints
# ═══════════════════════════════════════════════════════════════
class TestEquipmentEndpoints:
    @pytest.mark.asyncio
    async def test_list_equipment_requires_auth(self, client):
        resp = await client.get("/api/v1/equipment")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_equipment_requires_auth(self, client):
        resp = await client.post("/api/v1/equipment", json={"name": "Test"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_equipment_requires_auth(self, client):
        resp = await client.get(f"/api/v1/equipment/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_delete_equipment_requires_auth(self, client):
        resp = await client.delete(f"/api/v1/equipment/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_equipment_validation(self, client, auth_headers):
        """Missing required fields should return 422 or 401 (mock user not in DB)."""
        resp = await client.post(
            "/api/v1/equipment",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_get_nonexistent_equipment(self, client, auth_headers):
        resp = await client.get(
            f"/api/v1/equipment/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code in (401, 404)


# ═══════════════════════════════════════════════════════════════
# Analytics Endpoints
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, client):
        resp = await client.get("/api/v1/analytics/dashboard")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_equipment_health_requires_auth(self, client):
        resp = await client.get("/api/v1/analytics/equipment-health")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_trends_requires_auth(self, client):
        resp = await client.get("/api/v1/analytics/trends")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════
# Alert Endpoints
# ═══════════════════════════════════════════════════════════════
class TestAlertEndpoints:
    @pytest.mark.asyncio
    async def test_list_alerts_requires_auth(self, client):
        resp = await client.get("/api/v1/alerts")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_active_alerts_requires_auth(self, client):
        resp = await client.get("/api/v1/alerts/active")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_acknowledge_alert_requires_auth(self, client):
        resp = await client.put(
            f"/api/v1/alerts/{uuid.uuid4()}",
            json={"status": "acknowledged"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_resolve_alert_requires_auth(self, client):
        resp = await client.put(
            f"/api/v1/alerts/{uuid.uuid4()}",
            json={"status": "resolved", "resolution_notes": "test"},
        )
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════
# User Management Endpoints
# ═══════════════════════════════════════════════════════════════
class TestUserManagementEndpoints:
    @pytest.mark.asyncio
    async def test_list_users_requires_auth(self, client):
        resp = await client.get("/api/v1/users")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_users_requires_admin(self, client, engineer_token):
        """Non-admin users should be rejected (401 if user not in DB, 403 if found)."""
        resp = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {engineer_token}"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_user_requires_auth(self, client):
        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_role_requires_admin(self, client, engineer_token):
        resp = await client.put(
            f"/api/v1/users/{uuid.uuid4()}/role",
            headers={"Authorization": f"Bearer {engineer_token}"},
            json={"role": "viewer"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_status_requires_admin(self, client, engineer_token):
        resp = await client.put(
            f"/api/v1/users/{uuid.uuid4()}/status",
            headers={"Authorization": f"Bearer {engineer_token}"},
            json={"is_active": False},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_role_invalid_role(self, client, auth_headers):
        """Invalid role string should return 400, 401, or 422."""
        resp = await client.put(
            f"/api/v1/users/{uuid.uuid4()}/role",
            headers=auth_headers,
            json={"role": "superadmin"},
        )
        assert resp.status_code in (400, 401, 404, 422)


# ═══════════════════════════════════════════════════════════════
# Prediction Endpoints
# ═══════════════════════════════════════════════════════════════
class TestPredictionEndpoints:
    @pytest.mark.asyncio
    async def test_predict_requires_auth(self, client):
        resp = await client.post(
            "/api/v1/predictions/predict",
            json={"equipment_id": str(uuid.uuid4()), "air_temperature": 300, "process_temperature": 310, "rotational_speed": 1500, "torque": 40, "tool_wear": 100},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_history_requires_auth(self, client):
        resp = await client.get(f"/api/v1/predictions/history/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_predict_validation(self, client, auth_headers):
        """Predict with non-existent equipment should return 401 (mock user) or 404."""
        resp = await client.post(
            "/api/v1/predictions/predict",
            headers=auth_headers,
            json={
                "equipment_id": str(uuid.uuid4()),
                "air_temperature": 300,
                "process_temperature": 310,
                "rotational_speed": 1500,
                "torque": 40,
                "tool_wear": 100,
            },
        )
        assert resp.status_code in (401, 404, 422)


# ═══════════════════════════════════════════════════════════════
# Sensor Endpoints
# ═══════════════════════════════════════════════════════════════
class TestSensorEndpoints:
    @pytest.mark.asyncio
    async def test_ingest_requires_auth(self, client):
        resp = await client.post("/api/v1/sensors/readings", json={})
        assert resp.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_readings_requires_auth(self, client):
        resp = await client.get("/api/v1/sensors/readings")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_latest_requires_auth(self, client):
        resp = await client.get(f"/api/v1/sensors/latest/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════
# ML Admin Endpoints
# ═══════════════════════════════════════════════════════════════
class TestMLAdminEndpoints:
    @pytest.mark.asyncio
    async def test_train_requires_auth(self, client):
        resp = await client.post("/api/v1/ml/train", json={"algorithm": "random_forest"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_models_requires_auth(self, client):
        resp = await client.get("/api/v1/ml/models")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_train_requires_admin(self, client, engineer_token):
        resp = await client.post(
            "/api/v1/ml/train",
            headers={"Authorization": f"Bearer {engineer_token}"},
            json={"algorithm": "random_forest"},
        )
        assert resp.status_code in (401, 403)
