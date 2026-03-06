"""
WebSocket Handler

Real-time sensor data and prediction streaming to connected clients.
Supports per-connection equipment subscriptions for filtered delivery.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError
from starlette.websockets import WebSocketState

from app.core.security import decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections with per-client subscriptions."""

    def __init__(self):
        # Map WebSocket → set of subscribed equipment IDs (empty = all)
        self._connections: Dict[WebSocket, Set[str]] = {}

    @property
    def active_connections(self) -> list[WebSocket]:
        return list(self._connections.keys())

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[websocket] = set()  # empty = receive all
        logger.info(
            "WebSocket connected: %s (total=%d)",
            websocket.client.host if websocket.client else "unknown",
            len(self._connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)
        logger.info(
            "WebSocket disconnected (total=%d)", len(self._connections)
        )

    def subscribe(self, websocket: WebSocket, equipment_ids: list[str]) -> None:
        """Set the equipment subscription filter for a connection."""
        if websocket in self._connections:
            self._connections[websocket] = set(equipment_ids)

    def unsubscribe_all(self, websocket: WebSocket) -> None:
        """Clear subscription filter (receive all messages)."""
        if websocket in self._connections:
            self._connections[websocket] = set()

    async def broadcast(self, message: dict, equipment_id: Optional[str] = None) -> None:
        """Send message to clients subscribed to the given equipment (or all)."""
        disconnected = []
        for ws, subscriptions in self._connections.items():
            try:
                if ws.client_state != WebSocketState.CONNECTED:
                    disconnected.append(ws)
                    continue
                # If client has no subscriptions, they receive everything.
                # If they have subscriptions, only deliver matching equipment_id.
                if subscriptions and equipment_id and equipment_id not in subscriptions:
                    continue
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_to(self, websocket: WebSocket, message: dict) -> None:
        """Send message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


async def broadcast_sensor_readings(readings: list) -> None:
    """
    Callback for SimulationEngine – forwards sensor readings to
    subscribed WebSocket clients, filtered by equipment_id.
    """
    for reading in readings:
        equipment_id = reading.get("equipment_id") if isinstance(reading, dict) else None
        await manager.broadcast(
            {"type": "sensor_reading", "data": reading},
            equipment_id=str(equipment_id) if equipment_id else None,
        )


@router.websocket("/sensors")
async def sensor_stream(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time sensor data streaming.

    Pass a valid JWT access token as a query parameter ``?token=<jwt>``
    to authenticate. Unauthenticated connections are rejected with:
    - 4001 – missing token
    - 4003 – invalid / expired token

    Client commands:
    - {"type": "ping"} → {"type": "pong"}
    - {"type": "subscribe", "equipment_ids": ["id1", "id2"]} → filters delivery
    - {"type": "unsubscribe"} → receive all messages again
    """
    # --- JWT authentication ---
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4003, reason="Invalid token")
            return
        if payload.get("type") != "access":
            await websocket.close(code=4003, reason="Invalid token type")
            return
    except (JWTError, Exception):
        await websocket.close(code=4003, reason="Invalid or expired token")
        return

    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = message.get("type")

            if msg_type == "ping":
                await manager.send_to(websocket, {"type": "pong"})

            elif msg_type == "subscribe":
                equipment_ids = message.get("equipment_ids", [])
                if isinstance(equipment_ids, list):
                    manager.subscribe(websocket, [str(eid) for eid in equipment_ids])
                    await manager.send_to(websocket, {
                        "type": "subscribed",
                        "equipment_ids": equipment_ids,
                    })

            elif msg_type == "unsubscribe":
                manager.unsubscribe_all(websocket)
                await manager.send_to(websocket, {"type": "unsubscribed"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        manager.disconnect(websocket)
