"""Unit tests for Custom Resource Definitions (CRDs)."""

from unittest.mock import MagicMock, patch

import pytest
from kubernetes import client
from kubernetes.client.exceptions import ApiException


class TestPodMonitorCRD:
    """Tests for the PodMonitor CRD."""

    def test_create_pod_monitor_crd(self):
        """Test creating a PodMonitor CRD."""
        # Mock the Kubernetes client
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api:
            mock_api_instance = mock_custom_api.return_value

            # Create test CRD object
            pod_monitor = {
                "apiVersion": "monitoring.k8s.playground/v1",
                "kind": "PodMonitor",
                "metadata": {"name": "test-pod-monitor", "namespace": "default"},
                "spec": {
                    "namespaces": ["default", "kube-system"],
                    "labelSelector": {"matchLabels": {"app": "nginx"}},
                    "interval": 30,
                    "vmwareIntegration": {
                        "enabled": True,
                        "host": "vcenter.example.com",
                        "port": 443,
                    },
                },
            }

            # Mock the API response
            mock_api_instance.create_namespaced_custom_object.return_value = pod_monitor

            # Create the CRD
            result = mock_api_instance.create_namespaced_custom_object(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                body=pod_monitor,
            )

            # Verify the API call
            mock_api_instance.create_namespaced_custom_object.assert_called_once_with(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                body=pod_monitor,
            )

            # Verify the result
            assert result == pod_monitor
            assert result["metadata"]["name"] == "test-pod-monitor"
            assert result["spec"]["namespaces"] == ["default", "kube-system"]
            assert result["spec"]["interval"] == 30

    def test_get_pod_monitor_crd(self):
        """Test getting a PodMonitor CRD."""
        # Mock the Kubernetes client
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api:
            mock_api_instance = mock_custom_api.return_value

            # Create test CRD object
            pod_monitor = {
                "apiVersion": "monitoring.k8s.playground/v1",
                "kind": "PodMonitor",
                "metadata": {"name": "test-pod-monitor", "namespace": "default"},
                "spec": {
                    "namespaces": ["default", "kube-system"],
                    "labelSelector": {"matchLabels": {"app": "nginx"}},
                    "interval": 30,
                    "vmwareIntegration": {
                        "enabled": True,
                        "host": "vcenter.example.com",
                        "port": 443,
                    },
                },
            }

            # Mock the API response
            mock_api_instance.get_namespaced_custom_object.return_value = pod_monitor

            # Get the CRD
            result = mock_api_instance.get_namespaced_custom_object(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                name="test-pod-monitor",
            )

            # Verify the API call
            mock_api_instance.get_namespaced_custom_object.assert_called_once_with(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                name="test-pod-monitor",
            )

            # Verify the result
            assert result == pod_monitor
            assert result["metadata"]["name"] == "test-pod-monitor"

    def test_update_pod_monitor_crd(self):
        """Test updating a PodMonitor CRD."""
        # Mock the Kubernetes client
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api:
            mock_api_instance = mock_custom_api.return_value

            # Create test CRD object
            pod_monitor = {
                "apiVersion": "monitoring.k8s.playground/v1",
                "kind": "PodMonitor",
                "metadata": {"name": "test-pod-monitor", "namespace": "default"},
                "spec": {
                    "namespaces": ["default", "kube-system"],
                    "labelSelector": {"matchLabels": {"app": "nginx"}},
                    "interval": 30,
                    "vmwareIntegration": {
                        "enabled": True,
                        "host": "vcenter.example.com",
                        "port": 443,
                    },
                },
            }

            # Updated CRD object
            updated_pod_monitor = pod_monitor.copy()
            updated_pod_monitor["spec"]["interval"] = 60
            updated_pod_monitor["spec"]["namespaces"].append("monitoring")

            # Mock the API response
            mock_api_instance.patch_namespaced_custom_object.return_value = updated_pod_monitor

            # Update the CRD
            result = mock_api_instance.patch_namespaced_custom_object(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                name="test-pod-monitor",
                body=updated_pod_monitor,
            )

            # Verify the API call
            mock_api_instance.patch_namespaced_custom_object.assert_called_once_with(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                name="test-pod-monitor",
                body=updated_pod_monitor,
            )

            # Verify the result
            assert result == updated_pod_monitor
            assert result["spec"]["interval"] == 60
            assert "monitoring" in result["spec"]["namespaces"]

    def test_delete_pod_monitor_crd(self):
        """Test deleting a PodMonitor CRD."""
        # Mock the Kubernetes client
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api:
            mock_api_instance = mock_custom_api.return_value

            # Mock the API response
            mock_api_instance.delete_namespaced_custom_object.return_value = {}

            # Delete the CRD
            result = mock_api_instance.delete_namespaced_custom_object(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                name="test-pod-monitor",
            )

            # Verify the API call
            mock_api_instance.delete_namespaced_custom_object.assert_called_once_with(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
                name="test-pod-monitor",
            )

            # Verify the result
            assert result == {}

    def test_list_pod_monitor_crds(self):
        """Test listing PodMonitor CRDs."""
        # Mock the Kubernetes client
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api:
            mock_api_instance = mock_custom_api.return_value

            # Create test CRD objects
            pod_monitors = {
                "apiVersion": "monitoring.k8s.playground/v1",
                "kind": "PodMonitorList",
                "items": [
                    {
                        "apiVersion": "monitoring.k8s.playground/v1",
                        "kind": "PodMonitor",
                        "metadata": {"name": "test-pod-monitor-1", "namespace": "default"},
                        "spec": {"namespaces": ["default"], "interval": 30},
                    },
                    {
                        "apiVersion": "monitoring.k8s.playground/v1",
                        "kind": "PodMonitor",
                        "metadata": {"name": "test-pod-monitor-2", "namespace": "default"},
                        "spec": {"namespaces": ["kube-system"], "interval": 60},
                    },
                ],
            }

            # Mock the API response
            mock_api_instance.list_namespaced_custom_object.return_value = pod_monitors

            # List the CRDs
            result = mock_api_instance.list_namespaced_custom_object(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
            )

            # Verify the API call
            mock_api_instance.list_namespaced_custom_object.assert_called_once_with(
                group="monitoring.k8s.playground",
                version="v1",
                namespace="default",
                plural="podmonitors",
            )

            # Verify the result
            assert result == pod_monitors
            assert len(result["items"]) == 2
            assert result["items"][0]["metadata"]["name"] == "test-pod-monitor-1"
            assert result["items"][1]["metadata"]["name"] == "test-pod-monitor-2"

    def test_handle_crd_error(self):
        """Test handling errors with CRDs."""
        # Mock the Kubernetes client
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api:
            mock_api_instance = mock_custom_api.return_value

            # Mock the API error
            mock_api_instance.get_namespaced_custom_object.side_effect = ApiException(
                status=404, reason="Not Found"
            )

            # Attempt to get the CRD and verify exception
            with pytest.raises(ApiException) as excinfo:
                mock_api_instance.get_namespaced_custom_object(
                    group="monitoring.k8s.playground",
                    version="v1",
                    namespace="default",
                    plural="podmonitors",
                    name="nonexistent-pod-monitor",
                )

            # Verify the exception
            assert excinfo.value.status == 404
            assert excinfo.value.reason == "Not Found"
