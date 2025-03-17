"""Configuration utilities.

This module provides utilities for loading and managing configuration.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

log = logging.getLogger("cluster_monitor")


@dataclass
class Config:
    """Configuration data for the cluster monitor."""

    kubeconfig_path: Optional[str] = None
    metrics_interval: int = 60
    log_level: str = "INFO"
    output_format: str = "console"
    prometheus_port: int = 9090

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "Config":
        """Create a Config object from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            Config object
        """
        return cls(
            kubeconfig_path=config_dict.get("kubeconfig_path"),
            metrics_interval=config_dict.get("metrics_interval", 60),
            log_level=config_dict.get("log_level", "INFO"),
            output_format=config_dict.get("output_format", "console"),
            prometheus_port=config_dict.get("prometheus_port", 9090),
        )


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file or environment variables.

    Args:
        config_path: Path to configuration file

    Returns:
        Config object
    """
    # Default configuration
    config_data = {}

    # Try to load from file if specified
    if config_path:
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f) or {}
                log.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            log.warning(f"Failed to load configuration from {config_path}: {e}")

    # Try to load from default locations
    if not config_data:
        default_locations = [
            Path("config.yaml"),
            Path("~/.config/k8s_playground/config.yaml").expanduser(),
            Path("/etc/k8s_playground/config.yaml"),
        ]

        for location in default_locations:
            try:
                if location.exists():
                    with open(location, "r") as f:
                        config_data = yaml.safe_load(f) or {}
                    log.info(f"Loaded configuration from {location}")
                    break
            except Exception as e:
                log.debug(f"Failed to load configuration from {location}: {e}")

    # Override with environment variables
    env_prefix = "K8S_MONITOR_"
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix) :].lower()
            config_data[config_key] = value

    # Create config object
    config = Config.from_dict(config_data)

    return config
