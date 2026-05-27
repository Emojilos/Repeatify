"""Parser package for public Shkolkovo problem pages."""

from scripts.shkolkovo_parser.config import (
    DATA_RAW_RELATIVE_PATH,
    repository_root,
    shkolkovo_data_dir,
    shkolkovo_data_path,
)

__version__ = "0.1.0"

__all__ = [
    "DATA_RAW_RELATIVE_PATH",
    "__version__",
    "repository_root",
    "shkolkovo_data_dir",
    "shkolkovo_data_path",
]
