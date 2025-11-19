"""
Markdown to PDF/Ebook converter package.
Converts markdown files to PDF, EPUB, or MOBI format with Mermaid and PlantUML support.

MIT License - Copyright (c) 2025 Markdown to PDF Converter
"""

__version__ = "1.0.0"

from .converter import MarkdownToPDFConverter
from .ebook_converter import MarkdownToEbookConverter
from .verification import DocumentStateManager, calculate_file_hash
from .config import Config, get_default_db_path, get_user_config_dir
from .dependencies import DependencyChecker, check_dependencies

__all__ = [
    "MarkdownToPDFConverter",
    "MarkdownToEbookConverter",
    "DocumentStateManager",
    "calculate_file_hash",
    "Config",
    "get_default_db_path",
    "get_user_config_dir",
    "DependencyChecker",
    "check_dependencies",
]

