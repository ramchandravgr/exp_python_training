# Mock Library API

Local HTTP server for Python automation learning labs. Simulates a library
catalog API with intentional failures, in-memory session data, and CRUD
operations on books.

## Quick Start

Run these commands from the **`mocklibapis` project folder** (the one that contains
`pyproject.toml`), **not** from the inner `mocklibapis/mocklibapis/` package folder.

```bash
cd mocklibapis
uv sync
uv run python main.py
```

Alternative:

```bash
uv run mocklibapis
```

Server binds to the **first available port between 5000 and 5050** and prints
the URL on startup. Interactive docs are at `/docs` on that port.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (always 200) |
| GET | `/api/info` | API metadata and lab configuration |
| GET | `/api/books` | **Paginated** book catalog (Memory-Efficient Harvester lab) |
| GET | `/api/libraries/{zipcode}` | Libraries near a zipcode |
| POST | `/api/libraries/{library_id}/books` | Add a book (session only) |
| DELETE | `/api/libraries/{library_id}/books/{book_id}` | Remove a book (session only) |

## Sample Zipcodes

| Zipcode | Location | Notes |
|---------|----------|-------|
| `90210` | Beverly Hills, CA | 2 libraries |
| `10001` | New York, NY | Includes **duplicate books** for deduplication labs |
| `60601` | Chicago, IL | 1 library |
| `33101` | Miami, FL | 1 library |

## Datasets

Library data lives in external JSON files under `data/`:

| Dataset | Source | Size | Use case |
|---------|--------|------|----------|
| `small` (default) | `data/libraries_small.json` | ~14 books | CRUD, deduplication, zipcode lookups |
| `large` | `data/books_pages/` (100 files) | **5,000,000 books** | Paginated harvester / generator labs |

Switch datasets in `.env`:

```env
MOCKLIB_DATASET=small
# MOCKLIB_DATASET=large
```

Zipcode/CRUD endpoints always use `libraries_small.json`. The paginated
`/api/books` endpoint reads from page files when `MOCKLIB_DATASET=large`.

### Generate the large dataset (5,000,000 books)

The page files are not committed (too large). Generate once:

```bash
uv run python scripts/generate_large_dataset.py
```

This creates:
- `data/books_manifest.json` — metadata (total pages, page size)
- `data/books_pages/page_001.json` … `page_100.json`
- **100 pages** × **50,000 books** = **5,000,000 total records**

Then set `MOCKLIB_DATASET=large` in `.env` and restart the server.

## Paginated GET `/api/books` (Memory-Efficient Harvester lab)

```bash
curl "http://127.0.0.1:5000/api/books?page=1"
curl "http://127.0.0.1:5000/api/books?page=100"
```

Response shape:

```json
{
  "page": 1,
  "total_pages": 100,
  "page_size": 50000,
  "total_records": 5000000,
  "data": [
    {
      "book_id": 1,
      "library_id": 1,
      "zipcode": "10001",
      "name": "Science Fiction Volume 1",
      "author": "Mark Twain",
      "date_of_publish": "1952-03-14",
      "available": true,
      "demand": "HIGH"
    }
  ]
}
```

Lab workflow: use a **generator** to loop pages 1→100, yield each book, filter
where `demand == "HIGH"`, and keep memory under 50MB.

## Zipcode GET Response Shape

```json
{
  "zipcode": "90210",
  "libraries": [
    {
      "library_id": 1,
      "place": "Beverly Hills Public Library",
      "address": "444 N Rexford Dr, Beverly Hills, CA 90210",
      "contact": "+1-310-288-2211",
      "books": [
        {
          "book_id": 101,
          "name": "The Great Gatsby",
          "author": "F. Scott Fitzgerald",
          "date_of_publish": "1925-04-10",
          "available": true,
          "demand": "HIGH"
        }
      ]
    }
  ]
}
```

Book `demand` values: `HIGH`, `MEDIUM`, `LOW`

## Simulated Failures (GET only)

By default, GET requests randomly return:

- **500** Internal Server Error (~20% combined failure window)
- **504** Gateway Timeout (~10%, includes a 2s delay)
- **404** Simulated unavailable (~5%)

Disable failures for deterministic testing — either in `.env` or on the command line:

```bash
# Option 1: .env file (recommended)
copy .env.example .env
# then set MOCKLIB_DISABLE_FAILURES=1 in .env

# Option 2: inline for one run
MOCKLIB_DISABLE_FAILURES=1 uv run python main.py
```

Force a specific status code (lab/debug):

```bash
curl "http://127.0.0.1:5000/api/libraries/90210?force_status=504"
```

Supported `force_status` values: `400`, `401`, `403`, `404`, `429`, `500`, `502`, `503`, `504`

## POST — Add a Book

```bash
curl -X POST "http://127.0.0.1:5000/api/libraries/1/books" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dune",
    "author": "Frank Herbert",
    "date_of_publish": "1965-08-01",
    "available": true,
    "demand": "HIGH"
  }'
```

Returns **201 Created**. Changes exist only until the server stops.

## DELETE — Remove a Book

```bash
curl -X DELETE "http://127.0.0.1:5000/api/libraries/1/books/101"
```

## Configuration

Settings can live in a **`.env` file** in the `mocklibapis` project folder (same level as
`pyproject.toml`). Copy the template and edit:

```bash
copy .env.example .env
```

The server loads `.env` automatically on startup. Shell environment variables still
override `.env` values if both are set.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCKLIB_DATASET` | `small` | `small` or `large` (paginated books) |
| `MOCKLIB_PAGE_SIZE` | `50000` | Default page size for `/api/books` |
| `MOCKLIB_TOTAL_PAGES` | `100` | Expected page count for large dataset |
| `MOCKLIB_HOST` | `127.0.0.1` | Bind address |
| `MOCKLIB_PORT` | — | Preferred port (must be within the scan range) |
| `MOCKLIB_PORT_START` | `5000` | First port to try |
| `MOCKLIB_PORT_END` | `5050` | Last port to try |
| `MOCKLIB_FAILURE_RATE` | `0.20` | Random 500 threshold |
| `MOCKLIB_TIMEOUT_RATE` | `0.10` | Random 504 threshold |
| `MOCKLIB_NOT_FOUND_RATE` | `0.05` | Random simulated 404 threshold |
| `MOCKLIB_DISABLE_FAILURES` | — | Set to `1` to disable random failures |
| `MOCKLIB_MIN_DELAY` | `0.1` | Min response delay (seconds) |
| `MOCKLIB_MAX_DELAY` | `0.5` | Max response delay (seconds) |
| `MOCKLIB_TIMEOUT_DELAY` | `2.0` | Delay before 504 response |

## Lab Ideas

1. **Defensive API Client** — Retry GET requests on 500/504 with exponential backoff.
2. **Data Deduplication** — Use zipcode `10001` and deduplicate the books array with Python sets or dict keys.
3. **CRUD Workflow** — POST a book, verify via GET, then DELETE it.
4. **Status Code Handling** — Use `force_status` to test each error handler branch.
5. **Memory-Efficient Harvester** — Generator over 100 pages, filter `demand=HIGH`, stay under 50MB.
6. **Demand Filtering** — Filter books by `demand` (`HIGH`, `MEDIUM`, `LOW`).
