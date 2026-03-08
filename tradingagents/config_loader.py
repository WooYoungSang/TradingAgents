"""Utilities for loading and merging runtime configuration."""

from __future__ import annotations

import copy
import os
from typing import Any

import yaml


def _expand_env_values(value: Any) -> Any:
    """Recursively expand environment variables in string values."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_values(item) for item in value]
    return value


def load_yaml_config(path: str) -> dict:
    """Load YAML config, expand environment variables, and require a mapping root."""
    with open(path, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)

    if loaded is None:
        loaded = {}

    if not isinstance(loaded, dict):
        raise ValueError("YAML config must be a mapping/object at the root.")

    return _expand_env_values(loaded)


def merge_config(base: dict, override: dict) -> dict:
    """Deep-merge override into base without mutating either input dictionary."""
    merged = copy.deepcopy(base)

    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)

    return merged


def load_config(path: str | None, base: dict) -> dict:
    """Preserve the provided base when path is None, else deep-merge a YAML override."""
    if path is None:
        # Keep callers safe from accidental mutation when no override file is used.
        return copy.deepcopy(base)

    override = load_yaml_config(path)
    return merge_config(base, override)
