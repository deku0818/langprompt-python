"""Retry logic with exponential backoff and jitter."""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

from httpx import Response

from langprompt.exceptions import (
    NetworkError,
    RateLimitError,
    ServerError,
    TimeoutError,
)


T = TypeVar("T")


def should_retry(response: Response | None, exception: Exception | None) -> bool:
    """Determine if a request should be retried.

    Retry on:
    - HTTP 5xx server errors
    - HTTP 429 rate limit
    - Network errors
    - Timeout errors

    Do not retry on:
    - 4xx client errors (except 429)
    - Authentication/permission errors
    - Validation errors
    """
    if exception:
        # Retry on network and timeout errors
        return isinstance(exception, (NetworkError, TimeoutError))

    if response:
        # Retry on 5xx and 429
        return response.status_code >= 500 or response.status_code == 429

    return False


def calculate_retry_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
) -> float:
    """Calculate retry delay with exponential backoff and jitter.

    Formula: min(base_delay * 2^attempt + random(0, 1), max_delay)

    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Calculated delay in seconds
    """
    # Exponential backoff: base_delay * 2^attempt
    delay = base_delay * (2**attempt)

    # Add jitter (random 0-1 second) to avoid thundering herd
    delay += random.random()

    # Cap at max_delay
    return min(delay, max_delay)


def retry_sync(
    func: Callable[[], T],
    max_retries: int,
    base_delay: float,
    max_delay: float,
    should_retry_func: Callable[[Response | None, Exception | None], bool] = should_retry,
) -> T:
    """Execute function with retry logic (synchronous).

    Args:
        func: Function to execute
        max_retries: Maximum number of retries
        base_delay: Base retry delay in seconds
        max_delay: Maximum retry delay in seconds
        should_retry_func: Function to determine if retry should happen

    Returns:
        Function result

    Raises:
        Exception from the last failed attempt
    """
    last_exception: Exception | None = None
    last_response: Response | None = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            last_response = None

            # Don't retry on last attempt
            if attempt >= max_retries:
                raise

            # Check if should retry
            if not should_retry_func(last_response, last_exception):
                raise

            # Calculate and apply delay
            delay = calculate_retry_delay(attempt, base_delay, max_delay)
            time.sleep(delay)

    # Should never reach here, but satisfy type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")


async def retry_async(
    func: Callable[[], T],
    max_retries: int,
    base_delay: float,
    max_delay: float,
    should_retry_func: Callable[[Response | None, Exception | None], bool] = should_retry,
) -> T:
    """Execute async function with retry logic.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retries
        base_delay: Base retry delay in seconds
        max_delay: Maximum retry delay in seconds
        should_retry_func: Function to determine if retry should happen

    Returns:
        Function result

    Raises:
        Exception from the last failed attempt
    """
    import asyncio

    last_exception: Exception | None = None
    last_response: Response | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            last_response = None

            # Don't retry on last attempt
            if attempt >= max_retries:
                raise

            # Check if should retry
            if not should_retry_func(last_response, last_exception):
                raise

            # Calculate and apply delay
            delay = calculate_retry_delay(attempt, base_delay, max_delay)
            await asyncio.sleep(delay)

    # Should never reach here, but satisfy type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")
