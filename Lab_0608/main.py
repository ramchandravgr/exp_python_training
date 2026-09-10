"""
Laboratory 5: The Data Harvester

Orchestrate a multi-page data extraction using cursor-based pagination
against an API that limits responses to PAGE_SIZE records per page.

httpbun.com/get only echoes back whatever query params it receives (it
has no real paginated dataset), so it stands in here as the "API" while
each page's records/next_cursor are simulated locally based on the
cursor it echoes back - the same pattern used in api_orchestration.py's
fetch_cursor_data().
"""

import requests

BASE_URL = "https://httpbun.com"
PAGE_SIZE = 50
TOTAL_RECORD_COUNT = 180  # simulated total size of the remote dataset


def fetch_page(base_url: str, cursor: str, page_size: int) -> dict:
    """Fetch a single page and return a {"records": [...], "next_cursor": ...} payload."""
    # verify=False: local network TLS-inspecting proxy presents a self-signed
    # cert for httpbun.com; lab/demo only, do not disable verification like this in production.
    response = requests.get(
        f"{base_url}/get",
        params={"cursor": cursor, "page_size": page_size},
        verify=False,
    )
    response.raise_for_status()
    echoed_cursor = response.json().get("args", {}).get("cursor")

    start = int(echoed_cursor.split("_")[1])
    end = min(start + page_size, TOTAL_RECORD_COUNT)
    records = [f"record-{i}" for i in range(start, end)]

    next_cursor = f"offset_{end}" if end < TOTAL_RECORD_COUNT else None
    return {"records": records, "next_cursor": next_cursor}


def harvest_all_records(base_url: str, page_size: int) -> list:
    master_data_list = []
    next_cursor = "offset_0"
    page_number = 0

    while next_cursor is not None:
        page_number += 1
        payload = fetch_page(base_url, next_cursor, page_size)

        master_data_list.extend(payload["records"])
        print(
            f"Page {page_number}: fetched {len(payload['records'])} records "
            f"(running total: {len(master_data_list)})"
        )

        next_cursor = payload["next_cursor"]

    return master_data_list


def main():
    print("Hello from lab-0608!")

    master_data_list = harvest_all_records(BASE_URL, PAGE_SIZE)

    assert len(master_data_list) == TOTAL_RECORD_COUNT, (
        f"Expected {TOTAL_RECORD_COUNT} records, got {len(master_data_list)}"
    )
    print(f"Harvest complete: {len(master_data_list)} records collected.")


if __name__ == "__main__":
    main()
