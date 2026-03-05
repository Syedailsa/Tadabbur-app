import asyncio
import logging
from fastapi.websockets import WebSocketState
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSDisconnectedError(Exception):
    """Raised when WebSocket is permanently disconnected or send fails after all retries."""
    pass


# Keywords that indicate a permanent disconnect — no point retrying
_DISCONNECT_KEYWORDS = (
    "disconnect", "closed", "close", "1000", "1001",
    "1006", "1011", "connection reset", "broken pipe",
    "transport", "no close frame",
)


async def ws_send(
    websocket: WebSocket,
    payload: dict,
    *,
    retries: int = 5,
    delay: float = 5.0,
    label: str = "ws_send",
) -> bool:

    for attempt in range(1, retries + 1):
        
        if websocket.client_state != WebSocketState.CONNECTED:
            logger.warning(f"🔌 [{label}] WebSocket not connected — raising WSDisconnectedError")
            raise WSDisconnectedError(
                f"[{label}] WebSocket not in CONNECTED state "
                f"(current: {websocket.client_state}). Aborting send."
            )

        try:
            await websocket.send_json(payload)
            logger.info(f"✅ [{label}] Message sent successfully")
            return True 

        except WSDisconnectedError:
            raise 

        except Exception as exc:
            err_str = str(exc).lower()

            if any(kw in err_str for kw in _DISCONNECT_KEYWORDS):
                logger.warning(f"[{label}] Client disconnected during send: {exc}")
                raise WSDisconnectedError(
                    f"[{label}] Client disconnected during send: {exc}"
                ) from exc

            if attempt < retries:
                logger.warning(
                    f"⚠️ [{label}] Attempt {attempt}/{retries} failed "
                    f"({type(exc).__name__}: {exc}). Retrying in {delay}s…"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"❌ [{label}] Failed permanently after {retries} attempts. Last error: {exc}"
                )
                raise WSDisconnectedError(
                    f"[{label}] ws_send gave up after {retries} attempts: {exc}"
                ) from exc

    return False