"""
Random and forced HTTP failure simulation for GET endpoints.

Supports learning-lab scenarios such as retry logic against 500/504 errors.
"""

from __future__ import annotations

import asyncio
import random
from typing import NoReturn

from fastapi import HTTPException

from .config import CONFIG

SIMULATED_STATUSES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def parse_force_status(raw: str | None) -> int | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        status = int(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid force_status value: {raw!r}",
        ) from exc

    if status not in SIMULATED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported force_status {status}. "
                f"Supported values: {sorted(SIMULATED_STATUSES)}"
            ),
        )
    return status


async def maybe_simulate_get_failure(force_status: int | None = None) -> None:
    """Raise an HTTPException or delay to simulate unreliable GET responses."""
    if force_status is not None:
        await _raise_simulated_status(force_status)
        return

    if CONFIG.disable_failures:
        return

    roll = random.random()

    if roll < CONFIG.timeout_rate:
        await asyncio.sleep(CONFIG.timeout_delay)
        _raise_http(504, "Gateway Timeout")

    if roll < CONFIG.failure_rate:
        _raise_http(500, "Internal Server Error")

    if roll < CONFIG.failure_rate + CONFIG.not_found_rate:
        _raise_http(404, "Library data temporarily unavailable")


async def _raise_simulated_status(status: int) -> NoReturn:
    if status == 504:
        await asyncio.sleep(CONFIG.timeout_delay)
    _raise_http(status, SIMULATED_STATUSES[status])


def _raise_http(status_code: int, error: str) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": error,
            "status_code": status_code,
        },
    )
