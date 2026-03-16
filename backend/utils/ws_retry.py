import asyncio
import logging
from fastapi.websockets import WebSocketState
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WSDisconnectedError(Exception):
    """Raised when WebSocket is permanently disconnected or send fails after all retries."""
    pass


async def ws_send(
    websocket: WebSocket,
    payload: dict,
    *,
    retries: int = 3,
    delay: float = 0.5,
    label: str = "ws_send",
) -> bool:

    # First check: if WebSocket is already disconnected, don't even try - just skip
    if websocket.client_state != WebSocketState.CONNECTED:
        logger.warning(
            f"🔌 [{label}] WebSocket not connected "
            f"(state: {websocket.client_state}) — skipping send. "
            f"Message will be retrieved via get_chat on reconnect."
        )
        # Don't raise exception - just return False so caller can continue
        # The message is already saved in DB, frontend will load it via get_chat
        return False

    for attempt in range(1, retries + 1):
        try:
            await websocket.send_json(payload)
            logger.info(f"✅ [{label}] Sent successfully")
            return True

        except (WebSocketDisconnect, RuntimeError) as exc:
            # Check if socket is now disconnected OR if it's a "close message sent" error
            if (websocket.client_state != WebSocketState.CONNECTED or 
                "close" in str(exc).lower() or 
                "send" in str(exc).lower()):
                logger.warning(
                    f"🔌 [{label}] WebSocket disconnected during send "
                    f"(state: {websocket.client_state}) — aborting. "
                    f"Message will be retrieved via get_chat on reconnect."
                )
                return False
            
            # Transient error but still connected - retry
            if attempt < retries:
                logger.warning(
                    f"⚠️ [{label}] Connection error on attempt {attempt}/{retries} "
                    f"({type(exc).__name__}: {exc}). Retrying in {delay}s…"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"❌ [{label}] Failed permanently after {retries} attempts."
                )
                raise WSDisconnectedError(
                    f"[{label}] Gave up after {retries} attempts: {exc}"
                ) from exc

        except Exception as exc:
            if attempt < retries:
                logger.warning(
                    f"⚠️ [{label}] Transient error on attempt {attempt}/{retries} "
                    f"({type(exc).__name__}: {exc}). Retrying in {delay}s…"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"❌ [{label}] Failed permanently after {retries} attempts. "
                    f"Last error: {type(exc).__name__}: {exc}"
                )
                raise WSDisconnectedError(
                    f"[{label}] Gave up after {retries} attempts: {exc}"
                ) from exc

    return False
