from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DemandLevel = Literal["HIGH", "MEDIUM", "LOW"]


class BookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=200)
    date_of_publish: str = Field(..., description="Publication date in yyyy-MM-dd format")
    available: bool = True
    demand: DemandLevel = "MEDIUM"

    @field_validator("date_of_publish")
    @classmethod
    def validate_publish_date(cls, value: str) -> str:
        if not DATE_PATTERN.match(value):
            raise ValueError("date_of_publish must be in yyyy-MM-dd format")

        year, month, day = (int(part) for part in value.split("-"))
        date(year, month, day)
        return value


class BookResponse(BaseModel):
    book_id: int
    name: str
    author: str
    date_of_publish: str
    available: bool
    demand: DemandLevel
    library_id: int | None = None
    zipcode: str | None = None


class PaginatedBooksResponse(BaseModel):
    page: int
    total_pages: int
    page_size: int
    total_records: int
    data: list[BookResponse]


class LibraryResponse(BaseModel):
    library_id: int
    place: str
    address: str
    contact: str
    books: list[BookResponse]


class LibrariesByZipResponse(BaseModel):
    zipcode: str
    libraries: list[LibraryResponse]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    status_code: int
