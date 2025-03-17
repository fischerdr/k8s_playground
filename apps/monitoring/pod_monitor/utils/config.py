"""Configuration utilities.

This module provides utilities for loading and managing configuration.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

log = logging.getLogger("pod_monitor")


@dataclass
class VMwareConfig:
    """Configuration for VMware integration."""

    host: str
    username: str
    password: str
    port: int = 443
    disable_ssl_verification: bool = False


@dataclass
class Config:
    """Configuration for the pod monitor."""

    # Kubernetes configuration
    kubeconfig_path: Optional[str] = None
    namespaces: List[str] = field(default_factory=lambda: ["default"])

    # Monitoring configuration
    pod_problematic_threshold: int = 300  # 5 minutes in seconds
    monitoring_interval: int = 60  # 1 minute in seconds

    # VMware configuration
    vmware: Optional[VMwareConfig] = None

    # Prometheus configuration
    prometheus_port: int = 9090

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Rate limiting configuration
    rate_limit_api_calls: bool = True
    rate_limit_interval: int = 5  # 5 seconds between API calls

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "Config":
        """Create a Config object from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            Config object
        """
        # Extract VMware configuration if present
        vmware_config = None
        if "vmware" in config_dict:
            vmware_dict = config_dict.pop("vmware", {})
            if vmware_dict:
                vmware_config = VMwareConfig(
                    host=vmware_dict.get("host", ""),
                    username=vmware_dict.get("username", ""),
                    password=vmware_dict.get("password", ""),
                    port=vmware_dict.get("port", 443),
                    disable_ssl_verification=vmware_dict.get("disable_ssl_verification", False),
                )

        # Create Config object
        return cls(
            kubeconfig_path=config_dict.get("kubeconfig_path"),
            namespaces=config_dict.get("namespaces", ["default"]),
            pod_problematic_threshold=config_dict.get("pod_problematic_threshold", 300),
            monitoring_interval=config_dict.get("monitoring_interval", 60),
            vmware=vmware_config,
            prometheus_port=config_dict.get("prometheus_port", 9090),
            log_level=config_dict.get("log_level", "INFO"),
            log_format=config_dict.get(
                "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            rate_limit_api_calls=config_dict.get("rate_limit_api_calls", True),
            rate_limit_interval=config_dict.get("rate_limit_interval", 5),
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
    env_prefix = "POD_MONITOR_"

    # Handle basic configuration
    for key in [
        "KUBECONFIG_PATH",
        "POD_PROBLEMATIC_THRESHOLD",
        "MONITORING_INTERVAL",
        "PROMETHEUS_PORT",
        "LOG_LEVEL",
        "RATE_LIMIT_API_CALLS",
        "RATE_LIMIT_INTERVAL",
    ]:
        env_key = f"{env_prefix}{key}"
        if env_key in os.environ:
            config_key = key.lower()
            value = os.environ[env_key]

            # Convert to appropriate type
            if config_key in [
                "pod_problematic_threshold",
                "monitoring_interval",
                "prometheus_port",
                "rate_limit_interval",
            ]:
                config_data[config_key] = int(value)
            elif config_key in ["rate_limit_api_calls"]:
                config_data[config_key] = value.lower() in ["true", "1", "yes"]
            else:
                config_data[config_key] = value

    # Handle namespaces
    namespaces_env = f"{env_prefix}NAMESPACES"
    if namespaces_env in os.environ:
        config_data["namespaces"] = os.environ[namespaces_env].split(",")

    # Handle VMware configuration
    vmware_config = config_data.get("vmware", {})
    for key in ["HOST", "USERNAME", "PASSWORD", "PORT", "DISABLE_SSL_VERIFICATION"]:
        env_key = f"{env_prefix}VMWARE_{key}"
        if env_key in os.environ:
            config_key = key.lower()
            value = os.environ[env_key]

            # Convert to appropriate type
            if config_key == "port":
                vmware_config[config_key] = int(value)
            elif config_key == "disable_ssl_verification":
                vmware_config[config_key] = value.lower() in ["true", "1", "yes"]
            else:
                vmware_config[config_key] = value

    if vmware_config:
        config_data["vmware"] = vmware_config

    # Create config object
    config = Config.from_dict(config_data)

    return config
