from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _env(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return None
    return raw.strip()


def _float_env(name: str, default: float) -> float:
    raw = _env(name)
    if raw is None:
        return default
    return float(raw)


def _int_env(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    return int(raw)


@dataclass(slots=True)
class ServerConfig:
    project_root: Path = PROJECT_ROOT
    host: str = _env("MOCKLIB_HOST") or "127.0.0.1"
    port: int | None = _int_env("MOCKLIB_PORT", 0) if _env("MOCKLIB_PORT") else None
    port_range_start: int = _int_env("MOCKLIB_PORT_START", 5000)
    port_range_end: int = _int_env("MOCKLIB_PORT_END", 5050)
    dataset: str = (_env("MOCKLIB_DATASET") or "small").lower()
    data_file: str | None = _env("MOCKLIB_DATA_FILE")

    # Paginated /api/books settings (Memory-Efficient Harvester lab)
    page_size: int = _int_env("MOCKLIB_PAGE_SIZE", 50_000)
    total_pages: int = _int_env("MOCKLIB_TOTAL_PAGES", 100)

    # Simulated failure rates for GET /api/libraries/{zipcode}
    failure_rate: float = _float_env("MOCKLIB_FAILURE_RATE", 0.20)
    timeout_rate: float = _float_env("MOCKLIB_TIMEOUT_RATE", 0.10)
    not_found_rate: float = _float_env("MOCKLIB_NOT_FOUND_RATE", 0.05)

    # Artificial latency (seconds)
    min_delay: float = _float_env("MOCKLIB_MIN_DELAY", 0.1)
    max_delay: float = _float_env("MOCKLIB_MAX_DELAY", 0.5)
    timeout_delay: float = _float_env("MOCKLIB_TIMEOUT_DELAY", 2.0)

    # Disable all simulated failures (useful for deterministic demos)
    disable_failures: bool = (_env("MOCKLIB_DISABLE_FAILURES") or "").lower() in {
        "1",
        "true",
        "yes",
    }


CONFIG = ServerConfig()

DATA_DIR = CONFIG.project_root / "data"
SMALL_DATA_FILE = DATA_DIR / "libraries_small.json"
LARGE_MANIFEST_FILE = DATA_DIR / "books_manifest.json"
LARGE_PAGES_DIR = DATA_DIR / "books_pages"


def resolve_data_file_override() -> Path | None:
    """Explicit MOCKLIB_DATA_FILE override, if set."""
    if CONFIG.data_file:
        path = Path(CONFIG.data_file)
        if not path.is_absolute():
            path = CONFIG.project_root / path
        return path
    return None


def resolve_libraries_file() -> Path:
    """Zipcode/CRUD dataset — always the small libraries file unless overridden."""
    override = resolve_data_file_override()
    if override is not None:
        return override
    return SMALL_DATA_FILE


def resolve_pagination_source() -> Path:
    """Paginated /api/books source — follows dataset selection when not overridden."""
    override = resolve_data_file_override()
    if override is not None:
        return override
    if CONFIG.dataset == "large":
        return LARGE_MANIFEST_FILE
    return SMALL_DATA_FILE


def resolved_data_file_label() -> str:
    """Human-readable description of the active data source(s)."""
    if CONFIG.data_file:
        return str(resolve_data_file_override())

    if CONFIG.dataset == "large":
        return f"{LARGE_MANIFEST_FILE.relative_to(CONFIG.project_root)} + {LARGE_PAGES_DIR.relative_to(CONFIG.project_root)}/"

    return str(SMALL_DATA_FILE.relative_to(CONFIG.project_root))

