from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .config import CONFIG
from .database import dataset_summary
from .failure import SIMULATED_STATUSES, maybe_simulate_get_failure, parse_force_status
from .models import (
    BookCreate,
    ErrorResponse,
    LibrariesByZipResponse,
    PaginatedBooksResponse,
)
from .store import STORE

app = FastAPI(
    title="Mock Library API",
    description=(
        "Local mock server for Python automation labs. "
        "GET requests can return simulated HTTP errors; "
        "POST/DELETE changes persist only for the current session."
    ),
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "mocklibapis"}


@app.get("/api/info")
async def api_info() -> dict:
    return {
        "endpoints": {
            "GET /api/books": (
                "Paginated book catalog for Memory-Efficient Harvester labs. "
                "Returns { page, total_pages, data }. "
                "Filter client-side for demand=HIGH."
            ),
            "GET /api/libraries/{zipcode}": (
                "List libraries and books near a zipcode. "
                "Simulates 500/504/404 failures by default (~20%). "
                "Use ?force_status=504 to trigger a specific error."
            ),
            "POST /api/libraries/{library_id}/books": (
                "Add a book to a library for the current server session."
            ),
            "DELETE /api/libraries/{library_id}/books/{book_id}": (
                "Remove a book from a library for the current server session."
            ),
        },
        "known_zipcodes": STORE.known_zipcodes,
        "pagination": STORE.pagination_info(),
        "dataset": dataset_summary(),
        "simulated_status_codes": SIMULATED_STATUSES,
        "config": {
            "failure_rate": CONFIG.failure_rate,
            "timeout_rate": CONFIG.timeout_rate,
            "not_found_rate": CONFIG.not_found_rate,
            "disable_failures": CONFIG.disable_failures,
        },
    }


@app.get(
    "/api/libraries/{zipcode}",
    response_model=LibrariesByZipResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def get_libraries_by_zip(
    zipcode: str,
    force_status: str | None = Query(
        default=None,
        description="Force a specific HTTP status code (lab/debug use).",
    ),
) -> LibrariesByZipResponse:
    forced = parse_force_status(force_status)
    await maybe_simulate_get_failure(forced)

    delay = random.uniform(CONFIG.min_delay, CONFIG.max_delay)
    await asyncio.sleep(delay)

    libraries = STORE.get_libraries_by_zip(zipcode)
    if libraries is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Zipcode not found",
                "detail": f"No libraries registered for zipcode {zipcode!r}.",
                "status_code": 404,
                "known_zipcodes": STORE.known_zipcodes,
            },
        )

    return LibrariesByZipResponse(zipcode=zipcode, libraries=libraries)


@app.get(
    "/api/books",
    response_model=PaginatedBooksResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_books_page(
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int | None = Query(
        default=None,
        ge=1,
        le=100_000,
        description="Records per page. Defaults to 50,000 for large dataset.",
    ),
    force_status: str | None = Query(
        default=None,
        description="Force a specific HTTP status code (lab/debug use).",
    ),
) -> PaginatedBooksResponse:
    forced = parse_force_status(force_status)
    await maybe_simulate_get_failure(forced)

    pagination = STORE.pagination_info()
    if not pagination["available"]:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Large dataset not available",
                "detail": (
                    "Generate the 5M record dataset with: "
                    "uv run python scripts/generate_large_dataset.py"
                ),
                "status_code": 503,
            },
        )

    effective_page_size = page_size or pagination["page_size"]
    payload = STORE.get_books_page(page, effective_page_size)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Page not found",
                "detail": (
                    f"Page {page} is out of range (1-{pagination['total_pages']})."
                ),
                "status_code": 404,
                "total_pages": pagination["total_pages"],
            },
        )

    delay = random.uniform(CONFIG.min_delay, CONFIG.max_delay)
    await asyncio.sleep(delay)

    return PaginatedBooksResponse(**payload)


@app.post("/api/libraries/{library_id}/books", status_code=201)
async def add_book(library_id: int, book: BookCreate) -> dict:
    created = STORE.add_book(library_id, book.model_dump())
    if created is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Library not found",
                "detail": f"No library with library_id={library_id}.",
                "status_code": 404,
            },
        )

    return {
        "message": "Book added successfully",
        "library_id": library_id,
        "book": created,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.delete("/api/libraries/{library_id}/books/{book_id}")
async def delete_book(library_id: int, book_id: int) -> dict:
    if STORE.find_library(library_id) is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Library not found",
                "detail": f"No library with library_id={library_id}.",
                "status_code": 404,
            },
        )

    deleted = STORE.delete_book(library_id, book_id)
    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Book not found",
                "detail": (
                    f"No book with book_id={book_id} "
                    f"in library_id={library_id}."
                ),
                "status_code": 404,
            },
        )

    return {
        "message": "Book deleted successfully",
        "library_id": library_id,
        "book": deleted,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        payload = exc.detail
    else:
        payload = {
            "error": str(exc.detail),
            "status_code": exc.status_code,
        }
    return JSONResponse(status_code=exc.status_code, content=payload)
