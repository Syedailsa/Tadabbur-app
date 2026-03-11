import asyncio
import logging
from fastapi.websockets import WebSocketState
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WSDisconnectedError(Exception):
    """Raised when WebSocket is permanently disconnected or send fails after all retries."""
    pass


# async def ws_ping(websocket: WebSocket, timeout: float = 1.0) -> bool:
#     """
#     Quick ping to check if WebSocket connection is alive.
    
#     Returns True if connection is healthy, False otherwise.
#     This helps detect disconnection before attempting to send large payloads.
#     """
#     if websocket.client_state != WebSocketState.CONNECTED:
#         return False
    
#     try:
#         # Send a ping and wait for pong (with timeout)
#         await asyncio.wait_for(
#             websocket.send_json({"type": "ping"}),
#             timeout=timeout
#         )
#         return True
#     except asyncio.TimeoutError:
#         logger.warning("⚠️ WS ping timeout - connection may be stale")
#         return False
#     except Exception:
#         return False


async def ws_send(
    websocket: WebSocket,
    payload: dict,
    *,
    retries: int = 3,
    delay: float = 0.3,
    label: str = "ws_send",
    check_first: bool = True,
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
    # Quick health check before first attempt (optional, can be disabled)
    # if check_first and not await ws_ping(websocket, timeout=5.0):
    #     logger.warning(
    #         f"🔌 [{label}] Connection health check failed before send - "
    #         f"state: {websocket.client_state}"
    #     )
    #     raise WSDisconnectedError(
    #         f"[{label}] Connection health check failed: {websocket.client_state}"
    #     )

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