from __future__ import annotations

import socket

import uvicorn

from .config import CONFIG
from .database import dataset_summary


def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(
    host: str,
    start: int,
    end: int,
    preferred: int | None = None,
) -> int:
    """Return the first available port in *start*..*end* (inclusive)."""
    if start > end:
        raise ValueError(f"Invalid port range: {start}-{end}")

    candidates: list[int] = []
    if preferred is not None and start <= preferred <= end:
        candidates.append(preferred)
    candidates.extend(port for port in range(start, end + 1) if port != preferred)

    for port in candidates:
        if _is_port_available(host, port):
            return port

    raise RuntimeError(
        f"No available port found on {host} between {start} and {end}. "
        "Stop other services using those ports and try again."
    )


def run() -> None:
    port = find_available_port(
        CONFIG.host,
        CONFIG.port_range_start,
        CONFIG.port_range_end,
        preferred=CONFIG.port,
    )

    url = f"http://{CONFIG.host}:{port}"
    summary = dataset_summary()
    print(f"[INFO] Mock Library API starting on {url}", flush=True)
    print(f"[INFO] Dataset: {summary['dataset']} ({summary.get('book_count', 0):,} books)", flush=True)
    print(f"[INFO] Data source: {summary['data_file']}", flush=True)
    print(f"[INFO] Interactive docs: {url}/docs", flush=True)

    uvicorn.run(
        "mocklibapis.app:app",
        host=CONFIG.host,
        port=port,
        reload=False,
    )
