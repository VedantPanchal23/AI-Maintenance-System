"""
Real-Time Sensor Data Simulation Engine

Generates realistic time-series sensor data for equipment,
simulating gradual degradation and failure patterns.

Each equipment type has distinct sensor profiles:
- Air Compressor: High pressure, moderate temp
- Pump: Variable flow rate, vibration focus
- Electric Motor: RPM/torque focus
- HVAC/Chiller: Temperature-dominated
"""

import asyncio
import logging
import math
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════
# Equipment Sensor Profiles
# ═══════════════════════════════════════════════════════════════

EQUIPMENT_PROFILES = {
    "air_compressor": {
        "air_temperature": {"base": 300, "noise_std": 1.5, "drift_rate": 0.02},
        "process_temperature": {"base": 312, "noise_std": 2.0, "drift_rate": 0.03},
        "rotational_speed": {"base": 1500, "noise_std": 50, "drift_rate": -0.5},
        "torque": {"base": 42, "noise_std": 5, "drift_rate": 0.05},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 4.0, "noise_std": 0.8, "drift_rate": 0.03},
        "pressure": {"base": 7.5, "noise_std": 0.3, "drift_rate": -0.01},
    },
    "pump": {
        "air_temperature": {"base": 298, "noise_std": 1.0, "drift_rate": 0.01},
        "process_temperature": {"base": 308, "noise_std": 1.5, "drift_rate": 0.02},
        "rotational_speed": {"base": 2200, "noise_std": 80, "drift_rate": -0.3},
        "torque": {"base": 35, "noise_std": 4, "drift_rate": 0.04},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 5.5, "noise_std": 1.2, "drift_rate": 0.04},
        "pressure": {"base": 5.0, "noise_std": 0.5, "drift_rate": -0.02},
    },
    "electric_motor": {
        "air_temperature": {"base": 302, "noise_std": 2.0, "drift_rate": 0.025},
        "process_temperature": {"base": 315, "noise_std": 2.5, "drift_rate": 0.035},
        "rotational_speed": {"base": 1800, "noise_std": 60, "drift_rate": -0.8},
        "torque": {"base": 50, "noise_std": 6, "drift_rate": 0.06},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 3.5, "noise_std": 0.6, "drift_rate": 0.025},
        "power_consumption": {"base": 15.0, "noise_std": 1.0, "drift_rate": 0.05},
    },
    "hvac_chiller": {
        "air_temperature": {"base": 295, "noise_std": 1.0, "drift_rate": 0.015},
        "process_temperature": {"base": 280, "noise_std": 1.5, "drift_rate": 0.02},
        "rotational_speed": {"base": 1200, "noise_std": 40, "drift_rate": -0.2},
        "torque": {"base": 30, "noise_std": 3, "drift_rate": 0.03},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 3.0, "noise_std": 0.5, "drift_rate": 0.02},
        "humidity": {"base": 45, "noise_std": 5, "drift_rate": 0.01},
    },
    "cnc_mill": {
        "air_temperature": {"base": 301, "noise_std": 1.8, "drift_rate": 0.022},
        "process_temperature": {"base": 318, "noise_std": 2.2, "drift_rate": 0.035},
        "rotational_speed": {"base": 3500, "noise_std": 100, "drift_rate": -1.0},
        "torque": {"base": 55, "noise_std": 7, "drift_rate": 0.07},
        "tool_wear": {"base": 0, "increment": 2},
        "vibration": {"base": 4.5, "noise_std": 1.0, "drift_rate": 0.04},
        "power_consumption": {"base": 12.0, "noise_std": 1.5, "drift_rate": 0.04},
    },
    "hydraulic_press": {
        "air_temperature": {"base": 299, "noise_std": 1.2, "drift_rate": 0.018},
        "process_temperature": {"base": 325, "noise_std": 3.0, "drift_rate": 0.04},
        "rotational_speed": {"base": 800, "noise_std": 30, "drift_rate": -0.15},
        "torque": {"base": 120, "noise_std": 10, "drift_rate": 0.08},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 6.0, "noise_std": 1.5, "drift_rate": 0.05},
        "pressure": {"base": 200, "noise_std": 5, "drift_rate": -0.1},
    },
    "injection_molder": {
        "air_temperature": {"base": 303, "noise_std": 2.0, "drift_rate": 0.025},
        "process_temperature": {"base": 350, "noise_std": 4.0, "drift_rate": 0.05},
        "rotational_speed": {"base": 1000, "noise_std": 40, "drift_rate": -0.3},
        "torque": {"base": 65, "noise_std": 8, "drift_rate": 0.06},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 5.0, "noise_std": 1.2, "drift_rate": 0.035},
        "pressure": {"base": 150, "noise_std": 4, "drift_rate": -0.05},
    },
    "conveyor": {
        "air_temperature": {"base": 296, "noise_std": 0.8, "drift_rate": 0.01},
        "process_temperature": {"base": 300, "noise_std": 1.0, "drift_rate": 0.015},
        "rotational_speed": {"base": 600, "noise_std": 20, "drift_rate": -0.1},
        "torque": {"base": 25, "noise_std": 3, "drift_rate": 0.03},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 3.5, "noise_std": 0.7, "drift_rate": 0.025},
    },
    "compressor": {
        "air_temperature": {"base": 302, "noise_std": 1.5, "drift_rate": 0.02},
        "process_temperature": {"base": 315, "noise_std": 2.0, "drift_rate": 0.03},
        "rotational_speed": {"base": 1600, "noise_std": 55, "drift_rate": -0.6},
        "torque": {"base": 45, "noise_std": 5, "drift_rate": 0.05},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 4.2, "noise_std": 0.9, "drift_rate": 0.03},
        "pressure": {"base": 8.0, "noise_std": 0.4, "drift_rate": -0.015},
    },
    "motor": {
        "air_temperature": {"base": 300, "noise_std": 1.8, "drift_rate": 0.022},
        "process_temperature": {"base": 312, "noise_std": 2.2, "drift_rate": 0.032},
        "rotational_speed": {"base": 1750, "noise_std": 65, "drift_rate": -0.7},
        "torque": {"base": 48, "noise_std": 6, "drift_rate": 0.055},
        "tool_wear": {"base": 0, "increment": 1},
        "vibration": {"base": 3.8, "noise_std": 0.7, "drift_rate": 0.028},
        "power_consumption": {"base": 18.0, "noise_std": 1.2, "drift_rate": 0.06},
    },
}


# ═══════════════════════════════════════════════════════════════
# Sensor Simulator
# ═══════════════════════════════════════════════════════════════

class EquipmentSimulator:
    """
    Simulates a single piece of equipment with realistic degradation.

    The simulator tracks internal state (wear level, cycle count)
    and generates sensor readings that progressively degrade over time.
    """

    def __init__(
        self,
        equipment_id: str,
        equipment_type: str,
        initial_wear: int = 0,
    ):
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type
        self.profile = EQUIPMENT_PROFILES.get(equipment_type, EQUIPMENT_PROFILES["air_compressor"])
        self.cycle_count = 0
        self.wear_level = initial_wear
        self.degradation_factor = 1.0  # Increases over time
        self._anomaly_active = False
        self._anomaly_start = 0

    def generate_reading(self) -> Dict[str, Any]:
        """Generate one sensor reading with realistic noise and degradation."""
        self.cycle_count += 1
        self.wear_level = min(240, self.wear_level + self.profile.get("tool_wear", {}).get("increment", 1))

        # Gradually increase degradation
        self.degradation_factor = 1.0 + (self.wear_level / 240.0) * 0.5

        # Random anomaly injection (5% chance after wear > 150)
        if self.wear_level > 150 and random.random() < 0.05:
            self._anomaly_active = True
            self._anomaly_start = self.cycle_count

        # End anomaly after ~10 cycles
        if self._anomaly_active and (self.cycle_count - self._anomaly_start) > 10:
            self._anomaly_active = False

        reading = {
            "equipment_id": self.equipment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for sensor_name, config in self.profile.items():
            if sensor_name == "tool_wear":
                reading[sensor_name] = self.wear_level
                continue

            base = config["base"]
            noise_std = config.get("noise_std", 1.0)
            drift_rate = config.get("drift_rate", 0.0)

            # Base value with noise
            value = base + random.gauss(0, noise_std)

            # Apply degradation drift
            drift = drift_rate * self.wear_level * self.degradation_factor
            value += drift

            # Anomaly injection: spike in values
            if self._anomaly_active:
                anomaly_magnitude = noise_std * random.uniform(2.0, 4.0)
                value += anomaly_magnitude

            # Add sinusoidal component (daily operational pattern)
            hour_cycle = math.sin(2 * math.pi * self.cycle_count / 288)  # ~24h cycle at 5min intervals
            value += hour_cycle * noise_std * 0.3

            reading[sensor_name] = round(value, 2)

        return reading

    def reset(self) -> None:
        """Reset simulator state (e.g., after maintenance)."""
        self.cycle_count = 0
        self.wear_level = 0
        self.degradation_factor = 1.0
        self._anomaly_active = False


# ═══════════════════════════════════════════════════════════════
# Simulation Engine
# ═══════════════════════════════════════════════════════════════

class SimulationEngine:
    """
    Orchestrates simulation for multiple equipment units.

    Runs as a background task, generating sensor readings
    at configured intervals and optionally triggering predictions.
    """

    def __init__(self, model_service=None, session_factory=None):
        self.simulators: Dict[str, EquipmentSimulator] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._listeners: List[Any] = []  # WebSocket connections
        self._model_service = model_service
        self._session_factory = session_factory

    def register_equipment(
        self,
        equipment_id: str,
        equipment_type: str,
        initial_wear: int = 0,
    ) -> None:
        """Register equipment for simulation."""
        self.simulators[equipment_id] = EquipmentSimulator(
            equipment_id=equipment_id,
            equipment_type=equipment_type,
            initial_wear=initial_wear,
        )
        logger.info("Registered simulator for %s (%s)", equipment_id, equipment_type)

    def generate_all_readings(self) -> List[Dict[str, Any]]:
        """Generate readings for all registered equipment."""
        readings = []
        for sim in self.simulators.values():
            reading = sim.generate_reading()
            readings.append(reading)
        return readings

    async def start(self, interval_seconds: Optional[int] = None) -> None:
        """Start the simulation loop."""
        if self._running:
            logger.warning("Simulation engine already running")
            return

        self._running = True
        interval = interval_seconds or settings.SIMULATION_INTERVAL_SECONDS

        logger.info(
            "Starting simulation engine (interval=%ds, equipment=%d)",
            interval, len(self.simulators),
        )

        self._task = asyncio.create_task(self._run_loop(interval))

    async def stop(self) -> None:
        """Stop the simulation loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            logger.info("Simulation engine stopped")

    async def _run_loop(self, interval: int) -> None:
        """Main simulation loop — generates readings, stores, predicts, broadcasts."""
        while self._running:
            try:
                readings = self.generate_all_readings()

                # Notify WebSocket listeners with sensor data
                for listener in self._listeners:
                    try:
                        await listener(readings)
                    except Exception as e:
                        logger.error("Listener notification failed: %s", e)

                # Run auto-prediction pipeline (store readings, predict, update risk, alerts)
                prediction_results = []
                if self._model_service and self._session_factory and self._model_service.is_loaded:
                    try:
                        from app.services.auto_predict import run_auto_prediction_cycle
                        prediction_results = await run_auto_prediction_cycle(
                            readings=readings,
                            model_service=self._model_service,
                            session_factory=self._session_factory,
                        )
                    except Exception as e:
                        logger.error("Auto-prediction failed: %s", e)

                # Broadcast prediction results via WebSocket
                if prediction_results:
                    for listener in self._listeners:
                        try:
                            await listener([
                                {"type": "prediction", **pr}
                                for pr in prediction_results
                            ])
                        except Exception as e:
                            logger.error("Prediction broadcast failed: %s", e)

                logger.debug(
                    "Cycle complete: %d readings, %d predictions",
                    len(readings), len(prediction_results),
                )

            except Exception as e:
                logger.error("Simulation cycle error: %s", e)

            await asyncio.sleep(interval)

    def add_listener(self, callback) -> None:
        """Register a callback for new reading events."""
        self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        """Remove a registered callback."""
        self._listeners = [l for l in self._listeners if l != callback]
