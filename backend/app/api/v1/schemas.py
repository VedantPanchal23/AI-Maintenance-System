"""
Pydantic Schemas — Request/Response models for API validation.

Organized by domain entity for maintainability.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ═══════════════════════════════════════════════════════════════
# Auth Schemas
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    organization_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(default="engineer", pattern="^(admin|engineer|viewer)$")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    organization_id: uuid.UUID
    organization_name: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ═══════════════════════════════════════════════════════════════
# Equipment Schemas
# ═══════════════════════════════════════════════════════════════

class EquipmentTypeEnum(str, Enum):
    AIR_COMPRESSOR = "air_compressor"
    PUMP = "pump"
    ELECTRIC_MOTOR = "electric_motor"
    HVAC_CHILLER = "hvac_chiller"
    CNC_MILL = "cnc_mill"
    HYDRAULIC_PRESS = "hydraulic_press"
    INJECTION_MOLDER = "injection_molder"
    CONVEYOR = "conveyor"
    COMPRESSOR = "compressor"
    MOTOR = "motor"


class EquipmentStatusEnum(str, Enum):
    OPERATIONAL = "operational"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class EquipmentCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    name: str = Field(..., min_length=2, max_length=255)
    equipment_type: EquipmentTypeEnum
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[str] = None
    rated_power_kw: Optional[float] = Field(None, ge=0)
    max_rpm: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    status: Optional[EquipmentStatusEnum] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EquipmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    equipment_type: str
    status: str
    location: Optional[str]
    manufacturer: Optional[str]
    model_number: Optional[str]
    serial_number: Optional[str]
    installation_date: Optional[str]
    rated_power_kw: Optional[float]
    max_rpm: Optional[int]
    operating_hours: float
    risk_score: float
    is_active: bool
    notes: Optional[str]
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Computed fields for frontend convenience
    latest_risk_score: Optional[float] = None
    latest_risk_level: Optional[str] = None
    last_reading_at: Optional[datetime] = None
    last_maintenance_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class EquipmentListResponse(BaseModel):
    items: List[EquipmentResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# Sensor Schemas
# ═══════════════════════════════════════════════════════════════

class SensorReadingCreate(BaseModel):
    equipment_id: uuid.UUID
    timestamp: Optional[datetime] = None
    air_temperature: Optional[float] = Field(None, ge=250, le=400, description="Kelvin")
    process_temperature: Optional[float] = Field(None, ge=250, le=450, description="Kelvin")
    rotational_speed: Optional[int] = Field(None, ge=0, le=5000, description="RPM")
    torque: Optional[float] = Field(None, ge=0, le=200, description="Nm")
    tool_wear: Optional[int] = Field(None, ge=0, le=500, description="minutes")
    vibration: Optional[float] = Field(None, ge=0, le=50, description="mm/s")
    power_consumption: Optional[float] = Field(None, ge=0, description="kW")
    pressure: Optional[float] = Field(None, ge=0, description="bar")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="%")


class SensorReadingResponse(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    timestamp: datetime
    air_temperature: Optional[float]
    process_temperature: Optional[float]
    rotational_speed: Optional[int]
    torque: Optional[float]
    tool_wear: Optional[int]
    vibration: Optional[float]
    power_consumption: Optional[float]
    pressure: Optional[float]
    humidity: Optional[float]
    quality_flag: str

    model_config = {"from_attributes": True}


class SensorBatchCreate(BaseModel):
    readings: List[SensorReadingCreate] = Field(..., min_length=1, max_length=1000)


# ═══════════════════════════════════════════════════════════════
# Prediction Schemas
# ═══════════════════════════════════════════════════════════════

class PredictionRequest(BaseModel):
    equipment_id: uuid.UUID
    air_temperature: float = Field(..., ge=250, le=400)
    process_temperature: float = Field(..., ge=250, le=450)
    rotational_speed: int = Field(..., ge=0, le=5000)
    torque: float = Field(..., ge=0, le=200)
    tool_wear: int = Field(..., ge=0, le=500)
    vibration: float = Field(default=5.0, ge=0, le=50)


class PredictionResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    equipment_id: uuid.UUID
    timestamp: datetime
    failure_probability: float
    predicted_failure: bool
    failure_type: str
    confidence: float
    risk_level: str
    model_version: str
    feature_importance: Optional[Dict[str, float]] = None

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PredictionHistoryResponse(BaseModel):
    items: List[PredictionResponse]
    total: int
    equipment_id: uuid.UUID


# ═══════════════════════════════════════════════════════════════
# Alert Schemas
# ═══════════════════════════════════════════════════════════════

class AlertSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatusEnum(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertResponse(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    severity: str
    status: str
    title: str
    message: str
    risk_score: Optional[float]
    failure_probability: Optional[float] = None
    failure_type: Optional[str] = None
    equipment_name: Optional[str] = None
    email_sent: bool
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertUpdateRequest(BaseModel):
    status: AlertStatusEnum
    resolution_notes: Optional[str] = None


class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# Analytics Schemas
# ═══════════════════════════════════════════════════════════════

class EquipmentHealthSummary(BaseModel):
    equipment_id: uuid.UUID
    equipment_name: str
    equipment_type: str
    status: str
    risk_score: float
    latest_prediction: Optional[float] = None
    active_alerts: int = 0
    operating_hours: float = 0


class DashboardSummary(BaseModel):
    total_equipment: int
    operational_count: int
    warning_count: int
    critical_count: int
    maintenance_count: int
    active_alerts: int
    avg_risk_score: float
    equipment_health: List[EquipmentHealthSummary]

    # Convenience fields for frontend stat cards & charts
    healthy_equipment: int = 0
    equipment_by_status: Dict[str, int] = {}
    predictions_today: int = 0
    alerts_this_week: int = 0
    model_accuracy: Optional[float] = None
    system_uptime: Optional[str] = None


class MLModelInfo(BaseModel):
    model_config = {"protected_namespaces": ()}

    algorithm: str
    version: str
    model_path: str
    metrics: Dict[str, Any]
    is_loaded: bool
    feature_importance: Optional[Dict[str, float]] = None


class RiskTrendPoint(BaseModel):
    date: str
    avg_risk: float
    max_risk: float
    count: int


# ═══════════════════════════════════════════════════════════════
# ML Admin Schemas
# ═══════════════════════════════════════════════════════════════

class TrainModelRequest(BaseModel):
    algorithm: str = Field(
        default="xgboost",
        pattern="^(random_forest|xgboost|lightgbm|neural_network_deep|neural_network_sklearn)$",
    )
    data_filepath: Optional[str] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)


class TrainingResultResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    run_id: str
    algorithm: str
    version: str
    model_path: str
    metrics: Dict[str, Any]
    training_samples: int
    test_samples: int
    training_duration_seconds: float
    device: str = "cpu"


# ═══════════════════════════════════════════════════════════════
# Maintenance Log Schemas
# ═══════════════════════════════════════════════════════════════

class MaintenanceTypeEnum(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"


class MaintenanceLogCreate(BaseModel):
    equipment_id: uuid.UUID
    maintenance_type: MaintenanceTypeEnum
    description: str = Field(..., min_length=5, max_length=2000)
    status: str = Field("todo", description="todo | in_progress | completed")
    priority: str = Field("medium", description="low | medium | high | urgent")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cost: Optional[float] = Field(None, ge=0)
    downtime_hours: Optional[float] = Field(None, ge=0)
    parts_replaced: Optional[str] = None


class MaintenanceLogUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=5, max_length=2000)
    status: Optional[str] = None
    priority: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cost: Optional[float] = Field(None, ge=0)
    downtime_hours: Optional[float] = Field(None, ge=0)
    parts_replaced: Optional[str] = None


class MaintenanceLogResponse(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    performed_by: Optional[uuid.UUID]
    maintenance_type: str
    description: str
    status: str
    priority: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    cost: Optional[float]
    downtime_hours: Optional[float]
    parts_replaced: Optional[str]
    equipment_name: Optional[str] = None
    performer_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenanceLogListResponse(BaseModel):
    items: List[MaintenanceLogResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# User Alert Preference Schemas
# ═══════════════════════════════════════════════════════════════

class AlertPreferencesUpdate(BaseModel):
    notification_email: Optional[EmailStr] = None
    email_enabled: bool = True
    severities: List[str] = Field(
        default=["critical", "high"],
        description="Severity levels to receive email alerts for",
    )

    @field_validator("severities")
    @classmethod
    def validate_severities(cls, v: list) -> list:
        allowed = {"low", "medium", "high", "critical"}
        for s in v:
            if s.lower() not in allowed:
                raise ValueError(f"Invalid severity '{s}'. Allowed: {allowed}")
        return [s.lower() for s in v]


class AlertPreferencesResponse(BaseModel):
    notification_email: Optional[str] = None
    email_enabled: bool
    severities: List[str]


# ═══════════════════════════════════════════════════════════════
# Audit Log Schemas
# ═══════════════════════════════════════════════════════════════

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# Pagination & Common
# ═══════════════════════════════════════════════════════════════

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
