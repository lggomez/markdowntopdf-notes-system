#!/usr/bin/env python3
"""
Configuration management for markdown-to-pdf converter.
Supports environment variables, config file, and CLI arguments.

MIT License - Copyright (c) 2025 Markdown to PDF Converter
"""

import os
import json
import platform
from pathlib import Path
from typing import Dict, Optional, Any


def get_user_config_dir() -> Path:
    """Get platform-appropriate user config directory."""
    system = platform.system()
    
    if system == "Windows":
        config_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and others
        config_dir = Path.home() / ".config"
    
    return config_dir / "markdown-to-pdf"


def get_default_db_path() -> Path:
    """Get default database path in user config directory."""
    config_dir = get_user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "state.db"


def load_config_file() -> Dict[str, Any]:
    """Load configuration from config file if it exists."""
    config_file = get_user_config_dir() / "config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    return {}


def parse_dimension_value(value: str) -> Any:
    """Parse dimension value that can be pixels (int) or percentage (str).
    
    Args:
        value: String like "1680", "80%"
        
    Returns:
        int for pixel values, str for percentage values (e.g., "80%")
        
    Raises:
        ValueError: If percentage value exceeds 100%
    """
    value_stripped = value.strip()
    
    # Check if it's a percentage
    if value_stripped.endswith('%'):
        try:
            percent_value = float(value_stripped[:-1])
            if percent_value > 100:
                raise ValueError(f"Percentage value cannot exceed 100% (got {value_stripped}). Use absolute pixel values if you need larger dimensions.")
            if percent_value > 0:
                return value_stripped
        except ValueError as e:
            if "cannot exceed 100%" in str(e):
                raise
            pass
    
    # Try to parse as integer (pixels)
    try:
        return int(value_stripped)
    except ValueError:
        pass
    
    return None


def get_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    env_mapping = {
        "MD2PDF_SOURCE_DIR": "source_dir",
        "MD2PDF_OUTPUT_DIR": "output_dir",
        "MD2PDF_TEMP_DIR": "temp_dir",
        "MD2PDF_DB_PATH": "db_path",
        "MD2PDF_MAX_DIAGRAM_WIDTH": "max_diagram_width",
        "MD2PDF_MAX_DIAGRAM_HEIGHT": "max_diagram_height",
    }
    
    for env_var, config_key in env_mapping.items():
        value = os.environ.get(env_var)
        if value:
            # Parse diagram dimensions (can be pixels or percentage)
            if config_key in ["max_diagram_width", "max_diagram_height"]:
                parsed = parse_dimension_value(value)
                if parsed is not None:
                    config[config_key] = parsed
            else:
                config[config_key] = value
    
    return config


class Config:
    """Configuration manager with multi-layer precedence."""
    
    def __init__(self, cli_args: Optional[Dict[str, Any]] = None):
        """Initialize configuration.
        
        Precedence order (highest to lowest):
        1. CLI arguments
        2. Environment variables
        3. Config file
        4. Defaults
        """
        self.cli_args = cli_args or {}
        
        # Load from config file
        file_config = load_config_file()
        
        # Load from environment
        env_config = get_config_from_env()
        
        # Merge with precedence: CLI > ENV > FILE > DEFAULTS
        self._config = {}
        self._config.update(self._get_defaults())
        self._config.update(file_config)
        self._config.update(env_config)
        self._config.update(self.cli_args)
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "source_dir": "docs",
            "output_dir": "output",
            "temp_dir": "temp",
            "db_path": str(get_default_db_path()),
            "max_diagram_width": 1680,
            "max_diagram_height": 2240,
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def get_source_dir(self) -> str:
        """Get source directory path."""
        return self._config.get("source_dir", "docs")
    
    def get_output_dir(self) -> str:
        """Get output directory path."""
        return self._config.get("output_dir", "output")
    
    def get_temp_dir(self) -> str:
        """Get temporary directory path."""
        return self._config.get("temp_dir", "temp")
    
    def get_db_path(self) -> str:
        """Get database path."""
        return self._config.get("db_path", str(get_default_db_path()))
    
    def get_max_diagram_width(self):
        """Get maximum diagram width (can be int pixels or str percentage)."""
        return self._config.get("max_diagram_width", 1680)
    
    def get_max_diagram_height(self):
        """Get maximum diagram height (can be int pixels or str percentage)."""
        return self._config.get("max_diagram_height", 2240)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self._config.update(updates)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()

