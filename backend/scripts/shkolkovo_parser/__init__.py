"""Parser package for public Shkolkovo problem pages."""

from scripts.shkolkovo_parser.config import (
    DATA_RAW_RELATIVE_PATH,
    repository_root,
    shkolkovo_data_dir,
    shkolkovo_data_path,
)
from scripts.shkolkovo_parser.fetcher import (
    FetchError,
    FetchResult,
    ShkolkovoFetcher,
    snapshot_filename_for_url,
)

__version__ = "0.1.0"

__all__ = [
    "DATA_RAW_RELATIVE_PATH",
    "FetchError",
    "FetchResult",
    "ShkolkovoFetcher",
    "__version__",
    "repository_root",
    "shkolkovo_data_dir",
    "shkolkovo_data_path",
    "snapshot_filename_for_url",
]
