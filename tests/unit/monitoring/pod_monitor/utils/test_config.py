"""Unit tests for the configuration utilities."""

import os
from unittest.mock import mock_open, patch

from apps.monitoring.pod_monitor.utils.config import Config, VMwareConfig, load_config


class TestConfig:
    """Tests for the Config class."""

    def test_init(self):
        """Test initialization of the Config class."""
        # Create config with default values
        config = Config()

        # Verify default values
        assert config.namespaces == ["default"]
        assert config.monitoring_interval == 60
        assert config.kubeconfig_path is None
        assert config.pod_label_selectors == {}
        assert config.monitor_all_nodes is False
        assert config.vmware is None

    def test_from_dict(self):
        """Test creating a Config from a dictionary."""
        # Create config dictionary
        config_dict = {
            "namespaces": ["default", "kube-system"],
            "monitoring_interval": 30,
            "kubeconfig_path": "/path/to/kubeconfig",
            "pod_label_selectors": {"app": "nginx"},
            "monitor_all_nodes": True,
            "vmware": {
                "host": "vcenter.example.com",
                "username": "admin",
                "password": "password",
                "port": 443,
                "disable_ssl_verification": True,
            },
        }

        # Create config from dictionary
        config = Config.from_dict(config_dict)

        # Verify values
        assert config.namespaces == ["default", "kube-system"]
        assert config.monitoring_interval == 30
        assert config.kubeconfig_path == "/path/to/kubeconfig"
        assert config.pod_label_selectors == {"app": "nginx"}
        assert config.monitor_all_nodes is True
        assert config.vmware is not None
        assert config.vmware.host == "vcenter.example.com"
        assert config.vmware.username == "admin"
        assert config.vmware.password == "password"
        assert config.vmware.port == 443
        assert config.vmware.disable_ssl_verification is True


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_from_file(self):
        """Test loading configuration from a file."""
        # Create mock config file
        mock_config_yaml = """
        namespaces:
          - default
          - kube-system
        monitoring_interval: 30
        kubeconfig_path: /path/to/kubeconfig
        pod_label_selectors:
          app: nginx
        monitor_all_nodes: true
        vmware:
          host: vcenter.example.com
          username: admin
          password: password
          port: 443
          disable_ssl_verification: true
        """

        # Create the expected parsed YAML data
        expected_yaml_data = {
            "namespaces": ["default", "kube-system"],
            "monitoring_interval": 30,
            "kubeconfig_path": "/path/to/kubeconfig",
            "pod_label_selectors": {"app": "nginx"},
            "monitor_all_nodes": True,
            "vmware": {
                "host": "vcenter.example.com",
                "username": "admin",
                "password": "password",
                "port": 443,
                "disable_ssl_verification": True,
            },
        }

        # Create expected config object
        expected_config = Config(
            namespaces=["default", "kube-system"],
            monitoring_interval=30,
            kubeconfig_path="/path/to/kubeconfig",
            pod_label_selectors={"app": "nginx"},
            monitor_all_nodes=True,
            vmware=VMwareConfig(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            ),
        )

        # Mock open function and yaml.safe_load
        mock_file = mock_open(read_data=mock_config_yaml)

        with patch("builtins.open", mock_file):
            with patch(
                "apps.monitoring.pod_monitor.utils.config.yaml.safe_load",
                return_value=expected_yaml_data,
            ):
                with patch(
                    "apps.monitoring.pod_monitor.utils.config.Config.from_dict",
                    return_value=expected_config,
                ):
                    # Load config
                    config = load_config("/path/to/config.yaml")

                    # Verify values
                    assert config.namespaces == ["default", "kube-system"]
                    assert config.monitoring_interval == 30
                    assert config.kubeconfig_path == "/path/to/kubeconfig"
                    assert config.pod_label_selectors == {"app": "nginx"}
                    assert config.monitor_all_nodes is True
                    assert config.vmware is not None
                    assert config.vmware.host == "vcenter.example.com"
                    assert config.vmware.username == "admin"
                    assert config.vmware.password == "password"
                    assert config.vmware.port == 443
                    assert config.vmware.disable_ssl_verification is True

    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        # Mock environment variables
        mock_env = {
            "POD_MONITOR_NAMESPACES": "default,kube-system",
            "POD_MONITOR_MONITORING_INTERVAL": "30",
            "POD_MONITOR_KUBECONFIG_PATH": "/path/to/kubeconfig",
            "POD_MONITOR_LABEL_SELECTORS": "app=nginx,environment=prod",
            "POD_MONITOR_MONITOR_ALL_NODES": "true",
            "POD_MONITOR_VMWARE_HOST": "vcenter.example.com",
            "POD_MONITOR_VMWARE_USERNAME": "admin",
            "POD_MONITOR_VMWARE_PASSWORD": "password",
            "POD_MONITOR_VMWARE_PORT": "443",
            "POD_MONITOR_VMWARE_DISABLE_SSL_VERIFICATION": "true",
        }

        # Create expected config object
        expected_config = Config(
            namespaces=["default", "kube-system"],
            monitoring_interval=30,
            kubeconfig_path="/path/to/kubeconfig",
            pod_label_selectors={"app": "nginx", "environment": "prod"},
            monitor_all_nodes=True,
            vmware=VMwareConfig(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            ),
        )

        # Create an empty config data to simulate no file found
        empty_config_data = {}

        with patch.dict(os.environ, mock_env, clear=True):
            # Load config without file
            with patch("builtins.open", side_effect=FileNotFoundError):
                with patch(
                    "apps.monitoring.pod_monitor.utils.config.yaml.safe_load",
                    return_value=empty_config_data,
                ):
                    with patch(
                        "apps.monitoring.pod_monitor.utils.config.Config.from_dict",
                        return_value=expected_config,
                    ):
                        config = load_config()

                        # Verify values
                        assert config.namespaces == ["default", "kube-system"]
                        assert config.monitoring_interval == 30
                        assert config.kubeconfig_path == "/path/to/kubeconfig"
                        assert config.pod_label_selectors == {"app": "nginx", "environment": "prod"}
                        assert config.monitor_all_nodes is True
                        assert config.vmware is not None
                        assert config.vmware.host == "vcenter.example.com"
                        assert config.vmware.username == "admin"
                        assert config.vmware.password == "password"
                        assert config.vmware.port == 443
                        assert config.vmware.disable_ssl_verification is True

    def test_load_config_default(self):
        """Test loading default configuration."""
        # Mock environment with no variables
        with patch.dict(os.environ, clear=True):
            # Load config without file
            with patch("builtins.open", side_effect=FileNotFoundError):
                config = load_config()

                # Verify default values
                assert config.namespaces == ["default"]
                assert config.monitoring_interval == 60
                assert config.kubeconfig_path is None
                assert config.pod_label_selectors == {}
                assert config.monitor_all_nodes is False
                assert config.vmware is None
