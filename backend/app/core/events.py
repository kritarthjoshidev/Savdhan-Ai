import json
from typing import Optional, Set
from fastapi import WebSocket
import redis.asyncio as redis_async
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis_async.Redis] = None
_alert_connections: Set[WebSocket] = set()


async def connect_alert_client(websocket: WebSocket) -> None:
    """Register a browser that should receive real-time alert messages."""
    await websocket.accept()
    _alert_connections.add(websocket)


def disconnect_alert_client(websocket: WebSocket) -> None:
    _alert_connections.discard(websocket)


async def broadcast_local_alert(message: dict) -> None:
    """Deliver alerts locally even when Redis is not running in demo mode."""
    disconnected = []
    for websocket in _alert_connections:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    for websocket in disconnected:
        _alert_connections.discard(websocket)

async def get_redis():
    """Get a verified Redis client when the optional service is available."""
    global _redis_client
    try:
        if _redis_client is None:
            candidate = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
            await candidate.ping()
            _redis_client = candidate
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        return None

async def publish_alert(channel: str, message: dict):
    """Publish alert to Redis channel"""
    await broadcast_local_alert(message)
    try:
        redis = await get_redis()
        if redis:
            await redis.publish(channel, json.dumps(message))
            logger.info(f"Alert published to {channel}")
    except Exception as e:
        logger.warning(f"Could not publish alert: {e}")

async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
