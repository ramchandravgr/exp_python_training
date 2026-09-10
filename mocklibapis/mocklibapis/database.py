"""
Load library datasets from external JSON files.

Small dataset: nested libraries-by-zip JSON for CRUD and zipcode lookups.
Large dataset: paginated page files for the Memory-Efficient Harvester lab.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

from .config import (
    CONFIG,
    LARGE_MANIFEST_FILE,
    LARGE_PAGES_DIR,
    resolve_libraries_file,
    resolve_pagination_source,
    resolved_data_file_label,
)

BOOKS_MANIFEST_FILE = LARGE_MANIFEST_FILE
BOOKS_PAGES_DIR = LARGE_PAGES_DIR


def load_libraries_by_zip() -> dict[str, list[dict]]:
    data_file = resolve_libraries_file()

    if not data_file.is_file():
        raise FileNotFoundError(f"Dataset file not found: {data_file}")

    with data_file.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Dataset root must be an object: {data_file}")

    return data


def load_books_manifest() -> dict | None:
    if CONFIG.dataset != "large":
        return None

    manifest_path = resolve_pagination_source()
    if not manifest_path.is_file():
        return None

    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def page_file_path(page: int) -> Path:
    return BOOKS_PAGES_DIR / f"page_{page:03d}.json"


def load_books_page_file(page: int) -> dict:
    path = page_file_path(page)
    if not path.is_file():
        raise FileNotFoundError(f"Page file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def flatten_library_books(data: dict[str, list[dict]]) -> list[dict]:
    books: list[dict] = []
    for zipcode, libraries in data.items():
        for library in libraries:
            for book in library.get("books", []):
                books.append(
                    {
                        **book,
                        "library_id": library["library_id"],
                        "zipcode": zipcode,
                    }
                )
    return books


def count_books_in_libraries(data: dict[str, list[dict]]) -> int:
    return sum(
        len(library.get("books", []))
        for libraries in data.values()
        for library in libraries
    )


def paginate_books(books: list[dict], page: int, page_size: int) -> dict:
    total_records = len(books)
    total_pages = max(1, math.ceil(total_records / page_size))
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "page": page,
        "total_pages": total_pages,
        "page_size": page_size,
        "total_records": total_records,
        "data": books[start:end],
    }


def dataset_summary() -> dict:
    summary: dict = {
        "dataset": CONFIG.dataset,
        "data_file": resolved_data_file_label(),
        "libraries_file": str(resolve_libraries_file()),
        "pagination_file": str(resolve_pagination_source()),
    }

    if CONFIG.dataset == "large":
        manifest = load_books_manifest()
        if manifest is None:
            summary.update(
                {
                    "pagination_ready": False,
                    "book_count": 0,
                    "message": (
                        "Large dataset not generated. Run: "
                        "uv run python scripts/generate_large_dataset.py"
                    ),
                }
            )
        else:
            summary.update(
                {
                    "pagination_ready": True,
                    "book_count": manifest["total_records"],
                    "total_pages": manifest["total_pages"],
                    "page_size": manifest["page_size"],
                    "pages_dir": str(BOOKS_PAGES_DIR),
                    "zipcode_count": len(manifest.get("known_zipcodes", [])),
                }
            )
    else:
        data = load_libraries_by_zip()
        summary.update(
            {
                "pagination_ready": True,
                "book_count": count_books_in_libraries(data),
                "zipcode_count": len(data),
                "library_count": sum(len(libraries) for libraries in data.values()),
            }
        )

    return summary


def build_session_store() -> dict[str, list[dict]]:
    """Return a fresh deep copy of the small libraries dataset for one session."""
    return deepcopy(load_libraries_by_zip())
