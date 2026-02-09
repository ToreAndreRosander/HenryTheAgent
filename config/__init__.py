"""Configuration management module."""
from .config_manager import (
    DEFAULT_CONFIG,
    load_config,
    merge_dicts
)

__all__ = [
    "DEFAULT_CONFIG",
    "load_config",
    "merge_dicts"
]
