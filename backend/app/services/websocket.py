"""
WebSocket Handler

Real-time sensor data and prediction streaming to connected clients.
"""

import asyncio
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError
from starlette.websockets import WebSocketState

from app.core.security import decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket connected: %s (total=%d)",
            websocket.client.host if websocket.client else "unknown",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "WebSocket disconnected (total=%d)", len(self.active_connections)
        )

    async def broadcast(self, message: dict) -> None:
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

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
    Callback for SimulationEngine – forwards sensor readings to all
    connected WebSocket clients.
    """
    for reading in readings:
        await manager.broadcast({
            "type": "sensor_reading",
            "data": reading,
        })


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
    """
    # --- JWT authentication ---
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4003, reason="Invalid token type")
            return
    except (JWTError, Exception):
        await websocket.close(code=4003, reason="Invalid or expired token")
        return

    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle client commands
            if message.get("type") == "ping":
                await manager.send_to(websocket, {"type": "pong"})
            elif message.get("type") == "subscribe":
                equipment_ids = message.get("equipment_ids", [])
                await manager.send_to(websocket, {
                    "type": "subscribed",
                    "equipment_ids": equipment_ids,
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        manager.disconnect(websocket)
