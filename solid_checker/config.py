from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml


DEFAULT_CONFIG = {
    "thresholds": {
        "max_methods_per_class": 20,
        "max_methods_per_interface": 10,
        "max_parameters": 5,
        "max_outgoing_deps": 5,
    },
    "rules": {
        "god_class": True,
        "feature_envy": True,
        "hard_coded_types": True,
        "lsp_violations": True,
        "interface_bloat": True,
        "dip_violations": True,
        "dependency_metrics": True,
    },
    "exclude": [
        "node_modules",
        "__pycache__",
        ".git",
        "venv",
        "vendor",
        "dist",
        "build",
    ],
}


def load_config(config_path: Optional[str] = None) -> dict:
    """Load config from file, falling back to defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f) or {}
        return _merge_configs(DEFAULT_CONFIG, user_config)
    return dict(DEFAULT_CONFIG)


def _merge_configs(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result
