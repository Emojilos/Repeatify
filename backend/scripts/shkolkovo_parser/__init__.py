"""Parser package for public Shkolkovo problem pages."""

from scripts.shkolkovo_parser.catalog_parser import (
    CatalogParseError,
    CatalogProblemLink,
    ParsedCatalog,
    parse_catalog_html,
)
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
from scripts.shkolkovo_parser.normalizer import (
    normalize_plain_text,
    normalize_problem_html,
    normalize_problem_text,
)
from scripts.shkolkovo_parser.problem_parser import (
    ParsedProblem,
    parse_problem_html,
    source_id_from_url,
)
from scripts.shkolkovo_parser.validator import (
    INVALID_TASK_NUMBER,
    MISSING_CORRECT_ANSWER,
    MISSING_PROBLEM_TEXT,
    ParseStatus,
    ProblemValidationError,
    ProblemValidationResult,
    ValidatedProblemRecord,
    validate_problem,
)

__version__ = "0.1.0"

__all__ = [
    "DATA_RAW_RELATIVE_PATH",
    "CatalogParseError",
    "CatalogProblemLink",
    "CollectionStoppedError",
    "FetchError",
    "FetchResult",
    "INVALID_TASK_NUMBER",
    "MISSING_CORRECT_ANSWER",
    "MISSING_PROBLEM_TEXT",
    "ParsedCatalog",
    "ParsedProblem",
    "ParseStatus",
    "ProblemValidationError",
    "ProblemValidationResult",
    "ShkolkovoFetcher",
    "ValidatedProblemRecord",
    "__version__",
    "parse_catalog_html",
    "parse_problem_html",
    "normalize_plain_text",
    "normalize_problem_html",
    "normalize_problem_text",
    "repository_root",
    "shkolkovo_data_dir",
    "shkolkovo_data_path",
    "snapshot_filename_for_url",
    "source_id_from_url",
    "validate_problem",
]
