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
from scripts.shkolkovo_parser.exporter import (
    DEFAULT_DIFFICULTY,
    DEFAULT_SOURCE,
    ExportResult,
    build_dataset_record,
    build_error_record,
    content_hash_for_problem,
    export_task_files,
    task_errors_filename,
    task_filename,
)
from scripts.shkolkovo_parser.fetcher import (
    CollectionStoppedError,
    FetchError,
    FetchResult,
    ShkolkovoFetcher,
    snapshot_filename_for_url,
)
from scripts.shkolkovo_parser.image_downloader import (
    ImageDownload,
    ImageDownloadFailure,
    ImageDownloadResult,
    download_problem_images,
    image_download_failed_error,
    image_filename_for_url,
)
from scripts.shkolkovo_parser.normalizer import (
    normalize_plain_text,
    normalize_problem_html,
    normalize_problem_text,
)
from scripts.shkolkovo_parser.pipeline import (
    DEFAULT_TEST_TASK_NUMBER,
    MISSING_OFFLINE_SNAPSHOT,
    OfflinePipelineResult,
    default_fixture_dir,
    load_problem_fixture_pages,
    run_fixture_pipeline,
    run_offline_pipeline,
)
from scripts.shkolkovo_parser.problem_parser import (
    ParsedProblem,
    parse_problem_html,
    source_id_from_url,
)
from scripts.shkolkovo_parser.reporter import (
    ReportResult,
    TaskRunReport,
    build_task_report,
    task_report_filename,
    write_task_report,
)
from scripts.shkolkovo_parser.validator import (
    IMAGE_DOWNLOAD_FAILED,
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
    "DEFAULT_DIFFICULTY",
    "DEFAULT_SOURCE",
    "DEFAULT_TEST_TASK_NUMBER",
    "ExportResult",
    "FetchError",
    "FetchResult",
    "INVALID_TASK_NUMBER",
    "IMAGE_DOWNLOAD_FAILED",
    "ImageDownload",
    "ImageDownloadFailure",
    "ImageDownloadResult",
    "MISSING_CORRECT_ANSWER",
    "MISSING_OFFLINE_SNAPSHOT",
    "MISSING_PROBLEM_TEXT",
    "OfflinePipelineResult",
    "ParsedCatalog",
    "ParsedProblem",
    "ParseStatus",
    "ProblemValidationError",
    "ProblemValidationResult",
    "ReportResult",
    "ShkolkovoFetcher",
    "TaskRunReport",
    "ValidatedProblemRecord",
    "__version__",
    "build_dataset_record",
    "build_error_record",
    "build_task_report",
    "content_hash_for_problem",
    "default_fixture_dir",
    "download_problem_images",
    "export_task_files",
    "image_download_failed_error",
    "image_filename_for_url",
    "load_problem_fixture_pages",
    "parse_catalog_html",
    "parse_problem_html",
    "normalize_plain_text",
    "normalize_problem_html",
    "normalize_problem_text",
    "repository_root",
    "run_fixture_pipeline",
    "run_offline_pipeline",
    "shkolkovo_data_dir",
    "shkolkovo_data_path",
    "snapshot_filename_for_url",
    "source_id_from_url",
    "task_errors_filename",
    "task_filename",
    "task_report_filename",
    "validate_problem",
    "write_task_report",
]
