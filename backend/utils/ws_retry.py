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
    delay: float = 0.3,
    label: str = "ws_send",
) -> bool:
    """
    Production-ready WebSocket send with smart retry logic.

    Behaviour:
    - Checks WebSocketState before every attempt — if not CONNECTED, raises immediately.
    - WebSocketDisconnect → always permanent, raises WSDisconnectedError immediately.
    - RuntimeError during send → always permanent (Starlette/FastAPI behaviour), raises immediately.
    - Any other Exception → treated as transient, retried up to `retries` times.
    - After exhausting retries → raises WSDisconnectedError.
    - No hardcoded keywords — version-proof and future-proof.

    Args:
        websocket : FastAPI WebSocket instance.
        payload   : JSON-serialisable dict to send.
        retries   : Max attempts for transient errors (default 3).
        delay     : Seconds between retries (default 0.3).
        label     : Tag used in log messages for easy debugging.
    """

    for attempt in range(1, retries + 1):

        # Always check state before attempting send
        if websocket.client_state != WebSocketState.CONNECTED:
            logger.warning(
                f"🔌 [{label}] WebSocket not connected "
                f"(state: {websocket.client_state}) — aborting send"
            )
            raise WSDisconnectedError(
                f"[{label}] Not connected: {websocket.client_state}"
            )

        try:
            await websocket.send_json(payload)
            logger.info(f"✅ [{label}] Sent successfully")
            return True

        except WSDisconnectedError:
            # Already a permanent disconnect — re-raise immediately
            raise

        except WebSocketDisconnect:
            
            logger.warning(f"🔌 [{label}] WebSocketDisconnect — client gone")
            raise WSDisconnectedError(
                f"[{label}] WebSocketDisconnect: client disconnected"
            )

        except RuntimeError as exc:
            # Check if it's a "send on closed socket" type error
            error_msg = str(exc).lower()
            if "closed" in error_msg or "complete" in error_msg:
                logger.warning(f"🔌 [{label}] RuntimeError during send (socket closed?): {exc}")
                raise WSDisconnectedError(
                    f"[{label}] RuntimeError during send: {exc}"
                ) from exc
            # For other RuntimeErrors, treat as transient
            if attempt < retries:
                logger.warning(
                    f"⚠️ [{label}] RuntimeError on attempt {attempt}/{retries} "
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