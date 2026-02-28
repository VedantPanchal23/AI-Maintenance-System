"""
Tests for schema validation — ensures Pydantic models correctly
accept & reject data.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.api.v1.schemas import (
    AlertUpdateRequest,
    EquipmentCreate,
    EquipmentUpdate,
    LoginRequest,
    PredictionRequest,
    RegisterRequest,
    SensorBatchCreate,
    SensorReadingCreate,
    TrainModelRequest,
)


class TestLoginRequestSchema:
    def test_valid_login(self):
        req = LoginRequest(email="user@example.com", password="securepass")
        assert req.email == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="securepass")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="short")

    def test_long_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="a" * 129)


class TestRegisterRequestSchema:
    def test_valid_register(self):
        req = RegisterRequest(
            email="admin@example.com",
            password="securepass",
            full_name="Admin User",
            organization_name="Test Organization",
        )
        assert req.role == "engineer"  # default

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="x@test.com",
                password="securepass",
                full_name="X",
                organization_name="Org",
                role="superuser",
            )

    def test_valid_roles(self):
        for role in ("admin", "engineer", "viewer"):
            req = RegisterRequest(
                email="x@test.com",
                password="securepass",
                full_name="User",
                organization_name="Org",
                role=role,
            )
            assert req.role == role


class TestEquipmentSchemas:
    def test_valid_create(self):
        req = EquipmentCreate(
            name="Air Compressor 01",
            equipment_type="air_compressor",
        )
        assert req.name == "Air Compressor 01"

    def test_create_invalid_type(self):
        with pytest.raises(ValidationError):
            EquipmentCreate(name="X", equipment_type="unknown_type")

    def test_update_partial(self):
        req = EquipmentUpdate(notes="Updated notes")
        assert req.notes == "Updated notes"
        assert req.name is None

    def test_negative_rated_power_rejected(self):
        with pytest.raises(ValidationError):
            EquipmentCreate(
                name="Bad Equipment",
                equipment_type="pump",
                rated_power_kw=-10.0,
            )


class TestSensorSchemas:
    def test_valid_reading(self):
        reading = SensorReadingCreate(
            equipment_id=uuid.uuid4(),
            air_temperature=300.0,
            process_temperature=310.0,
            rotational_speed=1500,
            torque=40.0,
            tool_wear=100,
        )
        assert reading.air_temperature == 300.0

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(
                equipment_id=uuid.uuid4(),
                air_temperature=100.0,  # Below 250K min
            )

    def test_batch_too_large(self):
        with pytest.raises(ValidationError):
            readings = [
                SensorReadingCreate(equipment_id=uuid.uuid4())
                for _ in range(1001)
            ]
            SensorBatchCreate(readings=readings)

    def test_batch_empty_rejected(self):
        with pytest.raises(ValidationError):
            SensorBatchCreate(readings=[])


class TestPredictionRequestSchema:
    def test_valid_prediction(self):
        req = PredictionRequest(
            equipment_id=uuid.uuid4(),
            air_temperature=300.0,
            process_temperature=310.0,
            rotational_speed=1500,
            torque=40.0,
            tool_wear=100,
        )
        assert req.vibration == 5.0  # default

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            PredictionRequest(equipment_id=uuid.uuid4())


class TestAlertUpdateSchema:
    def test_valid_acknowledge(self):
        req = AlertUpdateRequest(status="acknowledged")
        assert req.status.value == "acknowledged"

    def test_valid_resolve_with_notes(self):
        req = AlertUpdateRequest(status="resolved", resolution_notes="Fixed the pump")
        assert req.resolution_notes == "Fixed the pump"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            AlertUpdateRequest(status="deleted")


class TestTrainModelSchema:
    def test_defaults(self):
        req = TrainModelRequest()
        assert req.algorithm == "xgboost"
        assert req.test_size == 0.2

    def test_invalid_algorithm(self):
        with pytest.raises(ValidationError):
            TrainModelRequest(algorithm="invalid_algo")

    def test_test_size_bounds(self):
        with pytest.raises(ValidationError):
            TrainModelRequest(test_size=0.05)  # Below 0.1 min
        with pytest.raises(ValidationError):
            TrainModelRequest(test_size=0.9)  # Above 0.5 max
