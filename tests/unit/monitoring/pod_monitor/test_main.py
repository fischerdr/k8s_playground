"""Unit tests for the main module."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.monitoring.pod_monitor.main import api_app, health, metrics, monitor_iteration


class TestMainModule:
    """Tests for the main module."""

    def test_health_endpoint(self):
        """Test the health endpoint."""
        # Create test client
        client = TestClient(api_app)

        # Mock global health status
        with patch("apps.monitoring.pod_monitor.main.health_status", {"status": "ok"}):
            # Make request
            response = client.get("/health")

            # Verify response
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

        # Test degraded status
        with patch(
            "apps.monitoring.pod_monitor.main.health_status",
            {"status": "degraded", "error": "Test error"},
        ):
            # Make request
            response = client.get("/health")

            # Verify response
            assert response.status_code == 200
            assert response.json() == {"status": "degraded", "error": "Test error"}

        # Test error status
        with patch(
            "apps.monitoring.pod_monitor.main.health_status",
            {"status": "error", "error": "Critical error"},
        ):
            # Make request
            response = client.get("/health")

            # Verify response
            assert response.status_code == 500
            assert response.json() == {"status": "error", "error": "Critical error"}

    def test_metrics_endpoint(self):
        """Test the metrics endpoint."""
        # Create test client
        client = TestClient(api_app)

        # Mock prometheus service
        with patch(
            "apps.monitoring.pod_monitor.main.prometheus_service"
        ) as mock_prometheus_service:
            mock_app = MagicMock()
            mock_prometheus_service.get_app.return_value = mock_app

            # Make request
            response = client.get("/metrics")

            # Verify prometheus service was called
            mock_prometheus_service.get_app.assert_called_once()

    def test_monitor_iteration(self, mock_config, mock_kubernetes_client):
        """Test a monitoring iteration."""
        # Mock services
        with patch("apps.monitoring.pod_monitor.main.kubernetes_service") as mock_k8s_service:
            with patch("apps.monitoring.pod_monitor.main.vmware_service") as mock_vmware_service:
                with patch(
                    "apps.monitoring.pod_monitor.main.prometheus_service"
                ) as mock_prometheus_service:
                    # Mock pod metrics
                    mock_pod_metrics = [
                        MagicMock(node_name="node-1"),
                        MagicMock(node_name="node-2"),
                    ]
                    mock_k8s_service.get_pods.return_value = mock_pod_metrics

                    # Mock pod alerts
                    mock_k8s_service.check_pod_alerts.return_value = ["Pod alert 1"]

                    # Mock node metrics
                    mock_node_metrics = [
                        MagicMock(name="node-1", vmware_machine_name="vm-node-1"),
                        MagicMock(name="node-2", vmware_machine_name="vm-node-2"),
                    ]
                    mock_k8s_service.get_nodes.return_value = mock_node_metrics

                    # Mock node alerts
                    mock_k8s_service.check_node_alerts.return_value = ["Node alert 1"]

                    # Mock VM metrics
                    mock_vm_metrics = [MagicMock(name="vm-node-1"), MagicMock(name="vm-node-2")]
                    mock_vmware_service.get_vm_metrics.return_value = mock_vm_metrics

                    # Mock VM alerts
                    mock_vmware_service.check_vm_alerts.return_value = ["VM alert 1"]

                    # Call monitor iteration
                    monitor_iteration(mock_config)

                    # Verify pod monitoring
                    mock_k8s_service.get_pods.assert_called_with(
                        "default", label_selector="app=nginx"
                    )
                    mock_k8s_service.check_pod_alerts.assert_called_once_with(mock_pod_metrics)
                    mock_prometheus_service.update_pod_metrics.assert_called_once_with(
                        mock_pod_metrics
                    )

                    # Verify node monitoring
                    mock_k8s_service.get_nodes.assert_called_once_with(["node-1", "node-2"])
                    mock_k8s_service.check_node_alerts.assert_called_once_with(mock_node_metrics)
                    mock_prometheus_service.update_node_metrics.assert_called_once_with(
                        mock_node_metrics
                    )

                    # Verify VM monitoring
                    mock_vmware_service.get_vm_metrics.assert_called_once_with(
                        ["vm-node-1", "vm-node-2"]
                    )
                    mock_vmware_service.check_vm_alerts.assert_called_once_with(mock_vm_metrics)
                    mock_prometheus_service.update_vmware_metrics.assert_called_once_with(
                        mock_vm_metrics
                    )

                    # Verify alerts were recorded
                    assert mock_prometheus_service.record_alert.call_count == 3
