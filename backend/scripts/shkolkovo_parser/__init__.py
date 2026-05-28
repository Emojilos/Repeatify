"""Parser package for public Shkolkovo problem pages."""

from scripts.shkolkovo_parser.config import (
    DATA_RAW_RELATIVE_PATH,
    repository_root,
    shkolkovo_data_dir,
    shkolkovo_data_path,
)
from scripts.shkolkovo_parser.fetcher import (
    CollectionStoppedError,
    FetchError,
    FetchResult,
    ShkolkovoFetcher,
    snapshot_filename_for_url,
)
from scripts.shkolkovo_parser.problem_parser import (
    ParsedProblem,
    parse_problem_html,
    source_id_from_url,
)

__version__ = "0.1.0"

__all__ = [
    "DATA_RAW_RELATIVE_PATH",
    "CollectionStoppedError",
    "FetchError",
    "FetchResult",
    "ParsedProblem",
    "ShkolkovoFetcher",
    "__version__",
    "parse_problem_html",
    "repository_root",
    "shkolkovo_data_dir",
    "shkolkovo_data_path",
    "snapshot_filename_for_url",
    "source_id_from_url",
]
