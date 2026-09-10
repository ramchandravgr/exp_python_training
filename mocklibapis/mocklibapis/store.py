from __future__ import annotations

from copy import deepcopy

from .config import CONFIG
from .database import (
    build_session_store,
    flatten_library_books,
    load_books_manifest,
    load_books_page_file,
    paginate_books,
)


class LibraryStore:
    """In-memory session store — resets when the server process exits."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._libraries_by_zip = build_session_store()
        self._next_book_id = self._compute_next_book_id()
        self._small_books_cache: list[dict] | None = None

    def _compute_next_book_id(self) -> int:
        max_id = 0
        for libraries in self._libraries_by_zip.values():
            for library in libraries:
                for book in library["books"]:
                    max_id = max(max_id, book["book_id"])
        return max_id + 1

    def _get_small_books(self) -> list[dict]:
        if self._small_books_cache is None:
            self._small_books_cache = flatten_library_books(self._libraries_by_zip)
        return self._small_books_cache

    def get_books_page(self, page: int, page_size: int) -> dict | None:
        if page < 1:
            return None

        if CONFIG.dataset == "large":
            manifest = load_books_manifest()
            if manifest is None:
                return None

            total_pages = manifest["total_pages"]
            if page > total_pages:
                return None

            payload = load_books_page_file(page)
            return {
                "page": payload["page"],
                "total_pages": payload["total_pages"],
                "page_size": payload["page_size"],
                "total_records": payload["total_records"],
                "data": deepcopy(payload["data"]),
            }

        books = self._get_small_books()
        result = paginate_books(books, page, page_size)
        if page > result["total_pages"]:
            return None
        return result

    def pagination_info(self) -> dict:
        if CONFIG.dataset == "large":
            manifest = load_books_manifest()
            if manifest is None:
                return {
                    "available": False,
                    "total_pages": 0,
                    "page_size": CONFIG.page_size,
                    "total_records": 0,
                }
            return {
                "available": True,
                "total_pages": manifest["total_pages"],
                "page_size": manifest["page_size"],
                "total_records": manifest["total_records"],
            }

        books = self._get_small_books()
        page_size = min(CONFIG.page_size, max(len(books), 1))
        total_pages = max(1, (len(books) + page_size - 1) // page_size)
        return {
            "available": True,
            "total_pages": total_pages,
            "page_size": page_size,
            "total_records": len(books),
        }

    def get_libraries_by_zip(self, zipcode: str) -> list[dict] | None:
        libraries = self._libraries_by_zip.get(zipcode)
        if libraries is None:
            return None
        return deepcopy(libraries)

    def find_library(self, library_id: int) -> tuple[str, dict] | None:
        for zipcode, libraries in self._libraries_by_zip.items():
            for library in libraries:
                if library["library_id"] == library_id:
                    return zipcode, library
        return None

    def add_book(self, library_id: int, book: dict) -> dict | None:
        found = self.find_library(library_id)
        if found is None:
            return None

        _, library = found
        new_book = {
            "book_id": self._next_book_id,
            **book,
        }
        self._next_book_id += 1
        library["books"].append(new_book)
        self._small_books_cache = None
        return deepcopy(new_book)

    def delete_book(self, library_id: int, book_id: int) -> dict | None:
        found = self.find_library(library_id)
        if found is None:
            return None

        _, library = found
        for index, book in enumerate(library["books"]):
            if book["book_id"] == book_id:
                deleted = library["books"].pop(index)
                self._small_books_cache = None
                return deleted
        return None

    @property
    def known_zipcodes(self) -> list[str]:
        return sorted(self._libraries_by_zip.keys())


STORE = LibraryStore()
