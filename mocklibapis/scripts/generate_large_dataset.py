"""
Generate the large paginated book dataset (default: 5,000,000 books / 100 pages).

Usage:
    uv run python scripts/generate_large_dataset.py
    uv run python scripts/generate_large_dataset.py --books 5000000 --pages 100
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
DEMAND_LEVELS = ("HIGH", "MEDIUM", "LOW")
AUTHORS = (
    "Jane Austen",
    "Mark Twain",
    "Toni Morrison",
    "George Orwell",
    "Harper Lee",
    "James Baldwin",
    "Zora Neale Hurston",
    "Virginia Woolf",
    "Chinua Achebe",
    "Gabriel Garcia Marquez",
)
GENRES = (
    "Mystery",
    "Science Fiction",
    "Historical Fiction",
    "Biography",
    "Poetry",
    "Fantasy",
    "Romance",
    "Thriller",
    "Classic",
    "Drama",
)


def random_publish_date(rng: random.Random) -> str:
    start = datetime(1900, 1, 1)
    offset = rng.randint(0, (datetime(2024, 12, 31) - start).days)
    return (start + timedelta(days=offset)).strftime("%Y-%m-%d")


def make_book(book_id: int, rng: random.Random) -> dict:
    zipcode = f"{10000 + (book_id % 100)}"
    library_id = 1 + ((book_id - 1) // 1000) % 500
    genre = GENRES[book_id % len(GENRES)]

    return {
        "book_id": book_id,
        "library_id": library_id,
        "zipcode": zipcode,
        "name": f"{genre} Volume {book_id}",
        "author": AUTHORS[book_id % len(AUTHORS)],
        "date_of_publish": random_publish_date(rng),
        "available": rng.random() < 0.75,
        "demand": rng.choice(DEMAND_LEVELS),
    }


def generate_pages(
    total_books: int,
    total_pages: int,
    output_dir: Path,
    manifest_file: Path,
    seed: int,
) -> None:
    if total_books % total_pages != 0:
        raise ValueError("total_books must be evenly divisible by total_pages")

    rng = random.Random(seed)
    page_size = total_books // total_pages
    output_dir.mkdir(parents=True, exist_ok=True)

    book_id = 1
    for page in range(1, total_pages + 1):
        books = [make_book(book_id + index, rng) for index in range(page_size)]
        book_id += page_size

        payload = {
            "page": page,
            "total_pages": total_pages,
            "page_size": page_size,
            "total_records": total_books,
            "data": books,
        }

        page_path = output_dir / f"page_{page:03d}.json"
        with page_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"))

        if page == 1 or page == total_pages or page % 10 == 0:
            print(f"  wrote {page_path.name} ({page}/{total_pages})")

    manifest = {
        "total_records": total_books,
        "total_pages": total_pages,
        "page_size": page_size,
        "pages_dir": output_dir.name,
        "known_zipcodes": [f"{10000 + index}" for index in range(100)],
    }
    with manifest_file.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate large paginated book dataset")
    parser.add_argument("--books", type=int, default=5_000_000)
    parser.add_argument("--pages", type=int, default=100)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/books_pages"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/books_manifest.json"),
    )
    args = parser.parse_args()

    print(
        f"Generating {args.books:,} books across "
        f"{args.pages} pages ({args.books // args.pages:,} per page)..."
    )
    generate_pages(
        total_books=args.books,
        total_pages=args.pages,
        output_dir=args.output_dir,
        manifest_file=args.manifest,
        seed=args.seed,
    )

    total_size_mb = sum(
        path.stat().st_size for path in args.output_dir.glob("page_*.json")
    ) / (1024 * 1024)
    print(f"Wrote {args.pages} page files to {args.output_dir} ({total_size_mb:.1f} MB total)")
    print(f"Manifest: {args.manifest}")


if __name__ == "__main__":
    main()
