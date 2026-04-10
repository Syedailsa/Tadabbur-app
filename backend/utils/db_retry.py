import asyncio
import logging
import random
from typing import Callable, Any

logger = logging.getLogger(__name__)


NON_RETRIABLE_MESSAGES = [
    "duplicate key",
    "violates foreign key",
    "violates not-null",
    "permission denied",
    "invalid input syntax",
    "column does not exist",
    "relation does not exist",
]

class DBRetryError(Exception):
    def __init__(self, label: str, attempts: int, original_error: Exception):
        self.label = label
        self.attempts = attempts
        self.original_error = original_error
        super().__init__(
            f"[{label}] Failed after {attempts} attempt(s). "
            f"Cause: {type(original_error).__name__}: {original_error}"
    )

async def db_retry(
    operation: Callable[[], Any],
    max_retries: int = 5,
    delay: float = 0.5,
    timeout: float = 10.0,
    label: str = "DB operation"
) -> Any:
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(operation),
                timeout=timeout
            )
            logger.info(f"[{label}] Succeeded on attempt {attempt + 1}")
            return result

        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning(f"[{label}] Attempt {attempt+1}/{max_retries} timed out after {timeout}s")

        except Exception as e:
            error_str = str(e).lower()

            if any(msg in error_str for msg in NON_RETRIABLE_MESSAGES):
                logger.error(f"[{label}] Non-retriable DB error on attempt {attempt+1}: {e}")
                raise DBRetryError(label, attempt + 1, e) from e

            last_error = e
            logger.warning(f"[{label}] Attempt {attempt+1}/{max_retries} failed: {type(e).__name__}: {e}")
        
        if attempt < max_retries - 1:
            jitter = random.uniform(0, 0.3)
            sleep_time = (delay * (2 ** attempt)) + jitter
            logger.debug(f"[{label}] Retrying in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)

    logger.error(f"[{label}] All {max_retries} attempts exhausted.")
    raise DBRetryError(label, max_retries, last_error) from last_error