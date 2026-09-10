"""
Memory-Efficient Harvester (beginner version)

WHAT THIS SCRIPT DOES:
  1. Talks to our Mock Library API
  2. Reads books page by page (100 pages, 5 million books total)
  3. Keeps only books with demand = "HIGH"
  4. Saves them to high_demand_report.csv
  5. Checks that we did NOT use too much RAM

BEFORE YOU RUN:
  1. Start the API:
       cd mocklibapis
       uv run python main.py
  2. In mocklibapis/.env set:
       MOCKLIB_DATASET=large
       MOCKLIB_DISABLE_FAILURES=1
  3. Run this script:
       cd Lab_1808
       uv run python memEfficioHarv.py
"""

import csv
import gc
import time
import tracemalloc

import httpx

# --- settings you can change ---
API_URL = "http://127.0.0.1:5000"          # change port if needed
OUTPUT_FILE = "high_demand_report.csv"
MEMORY_LIMIT_MB = 50


def get_function_memory(func, *args, **kwargs):
    """Measure peak memory used by a function (from course material)."""
    tracemalloc.start()

    result = func(*args, **kwargs)

    current, peak = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    print(
        f"[{func.__name__}] Net Allocated Memory: {current / (1024 * 1024):.2f} MB"
    )
    print(
        f"[{func.__name__}] Peak Memory Allocation: {peak / (1024 * 1024):.2f} MB"
    )

    return result, peak / (1024 * 1024)


def get_function_time(func, *args, **kwargs):
    """Measure how long a function takes to run (from course material)."""
    gc.disable()

    start_time = time.perf_counter()

    result = func(*args, **kwargs)

    elapsed_time = time.perf_counter() - start_time

    gc.enable()

    print(f"[{func.__name__}] Execution Time: {elapsed_time:.6f} seconds")

    return result


def get_function_time_and_memory(func, *args, **kwargs):
    """
    Measure time AND memory in one run.

    We use this instead of calling get_function_time and get_function_memory
    separately, because run_harvester takes a long time (5M books).
    """
    tracemalloc.start()
    gc.disable()

    start_time = time.perf_counter()

    result = func(*args, **kwargs)

    elapsed_time = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()

    tracemalloc.stop()
    gc.enable()

    print(f"[{func.__name__}] Execution Time: {elapsed_time:.6f} seconds")
    print(
        f"[{func.__name__}] Net Allocated Memory: {current / (1024 * 1024):.2f} MB"
    )
    print(
        f"[{func.__name__}] Peak Memory Allocation: {peak / (1024 * 1024):.2f} MB"
    )

    return result, peak / (1024 * 1024)


def get_high_demand_books(api_url):
    """
    THIS IS THE GENERATOR.

    A normal function uses 'return' and stops.
    A generator uses 'yield' — it gives one result, pauses,
    then continues when asked for the next one.

    We use 'yield book' so we never store all 5 million books in a list.
    """

    page = 1
    total_pages = 1

    while page <= total_pages:
        url = f"{api_url}/api/books"
        response = httpx.get(url, params={"page": page}, timeout=120.0)
        response.raise_for_status()
        page_data = response.json()

        total_pages = page_data["total_pages"]
        print(f"Reading page {page} of {total_pages}...")

        for book in page_data["data"]:
            if book["demand"] == "HIGH":
                yield book

        page = page + 1


def save_books_to_csv(books, filename):
    """Write books to CSV. 'books' is our generator."""
    columns = [
        "book_id",
        "name",
        "author",
        "date_of_publish",
        "available",
        "demand",
        "library_id",
        "zipcode",
    ]

    count = 0

    file = open(filename, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()

    for book in books:
        writer.writerow(book)
        count = count + 1

    file.close()

    return count


def run_harvester():
    """Fetch all pages and save HIGH demand books to CSV."""
    health = httpx.get(f"{API_URL}/health")
    health.raise_for_status()
    print("API is online.")

    high_demand_books = get_high_demand_books(API_URL)
    total_saved = save_books_to_csv(high_demand_books, OUTPUT_FILE)

    return total_saved


def main():
    print("Starting harvester...")
    print(f"API: {API_URL}")

    total_saved, peak_mb = get_function_time_and_memory(run_harvester)

    print(f"Done! Saved {total_saved:,} HIGH demand books to {OUTPUT_FILE}")

    if peak_mb <= MEMORY_LIMIT_MB:
        print(f"PASS - peak memory stayed under {MEMORY_LIMIT_MB} MB")
    else:
        print(f"FAIL - peak memory went over {MEMORY_LIMIT_MB} MB")


if __name__ == "__main__":
    main()
