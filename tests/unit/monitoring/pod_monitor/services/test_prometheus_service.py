"""Unit tests for the Prometheus service."""

from unittest.mock import MagicMock, patch

from apps.monitoring.pod_monitor.models.metrics import NodeMetric, PodMetric, VMwareMetric
from apps.monitoring.pod_monitor.services.prometheus_service import PrometheusService


class TestPrometheusService:
    """Tests for the PrometheusService class."""

    def test_init(self):
        """Test initialization of the Prometheus service."""
        service = PrometheusService()

        # Verify that all the required metrics are initialized
        assert hasattr(service, "pod_status_gauge")
        assert hasattr(service, "pod_age_gauge")
        assert hasattr(service, "container_status_gauge")
        assert hasattr(service, "node_status_gauge")
        assert hasattr(service, "node_condition_gauge")
        assert hasattr(service, "vmware_status_gauge")
        assert hasattr(service, "vmware_cpu_usage_gauge")
        assert hasattr(service, "vmware_memory_usage_gauge")
        assert hasattr(service, "vmware_cpu_percent_gauge")
        assert hasattr(service, "vmware_memory_percent_gauge")
        assert hasattr(service, "alert_counter")

    def test_get_app(self):
        """Test getting the ASGI app for Prometheus metrics."""
        service = PrometheusService()

        with patch(
            "apps.monitoring.pod_monitor.services.prometheus_service.make_asgi_app"
        ) as mock_make_asgi_app:
            mock_app = MagicMock()
            mock_make_asgi_app.return_value = mock_app

            app = service.get_app()

            # Check that make_asgi_app was called with the registry parameter
            mock_make_asgi_app.assert_called_once_with(registry=service.registry)
            assert app == mock_app

    def test_update_pod_metrics(self):
        """Test updating pod metrics."""
        service = PrometheusService()

        # Create test pod metrics
        pod1 = PodMetric(
            name="test-pod-1",
            namespace="default",
            status="Running",
            node_name="node-1",
            container_statuses={"nginx": "running"},
        )

        pod2 = PodMetric(
            name="test-pod-2",
            namespace="default",
            status="Pending",
            node_name="node-2",
            container_statuses={"nginx": "waiting"},
        )

        # Mock the gauge metrics
        service.pod_status_gauge = MagicMock()
        service.pod_age_gauge = MagicMock()
        service.container_status_gauge = MagicMock()

        # Call the method
        service.update_pod_metrics([pod1, pod2])

        # Verify that the metrics were cleared
        service.pod_status_gauge._metrics.clear.assert_called_once()
        service.pod_age_gauge._metrics.clear.assert_called_once()
        service.container_status_gauge._metrics.clear.assert_called_once()

        # Verify that the pod status metrics were updated
        assert service.pod_status_gauge.labels.call_count == 2
        service.pod_status_gauge.labels.assert_any_call(
            namespace="default", pod="test-pod-1", status="Running", node="node-1"
        )
        service.pod_status_gauge.labels.assert_any_call(
            namespace="default", pod="test-pod-2", status="Pending", node="node-2"
        )

        # Verify that the container status metrics were updated
        assert service.container_status_gauge.labels.call_count == 2
        service.container_status_gauge.labels.assert_any_call(
            namespace="default", pod="test-pod-1", container="nginx", status="running"
        )
        service.container_status_gauge.labels.assert_any_call(
            namespace="default", pod="test-pod-2", container="nginx", status="waiting"
        )

    def test_update_node_metrics(self):
        """Test updating node metrics."""
        service = PrometheusService()

        # Create test node metrics
        node1 = NodeMetric(
            name="node-1",
            status="Ready",
            vmware_machine_name="vm-node-1",
            conditions={"Ready": True, "DiskPressure": False},
        )

        node2 = NodeMetric(
            name="node-2",
            status="NotReady",
            vmware_machine_name="vm-node-2",
            conditions={"Ready": False, "DiskPressure": True},
        )

        # Mock the gauge metrics
        service.node_status_gauge = MagicMock()
        service.node_condition_gauge = MagicMock()

        # Call the method
        service.update_node_metrics([node1, node2])

        # Verify that the metrics were cleared
        service.node_status_gauge._metrics.clear.assert_called_once()
        service.node_condition_gauge._metrics.clear.assert_called_once()

        # Verify that the node status metrics were updated
        assert service.node_status_gauge.labels.call_count == 2
        service.node_status_gauge.labels.assert_any_call(
            node="node-1", status="Ready", vmware_machine="vm-node-1"
        )
        service.node_status_gauge.labels.assert_any_call(
            node="node-2", status="NotReady", vmware_machine="vm-node-2"
        )

        # Verify that the node condition metrics were updated
        assert service.node_condition_gauge.labels.call_count == 4
        service.node_condition_gauge.labels.assert_any_call(node="node-1", condition="Ready")
        service.node_condition_gauge.labels.assert_any_call(node="node-1", condition="DiskPressure")
        service.node_condition_gauge.labels.assert_any_call(node="node-2", condition="Ready")
        service.node_condition_gauge.labels.assert_any_call(node="node-2", condition="DiskPressure")

    def test_update_vmware_metrics(self):
        """Test updating VMware metrics."""
        service = PrometheusService()

        # Create test VMware metrics
        vm1 = VMwareMetric(
            name="vm-node-1",
            status="poweredOn",
            node_name="node-1",
            cpu_usage=1000,
            memory_usage=4096,
            cpu_capacity=4000,
            memory_capacity=8192,
        )

        vm2 = VMwareMetric(
            name="vm-node-2",
            status="poweredOff",
            node_name="node-2",
            cpu_usage=0,
            memory_usage=0,
            cpu_capacity=4000,
            memory_capacity=8192,
        )

        # Mock the gauge metrics
        service.vmware_status_gauge = MagicMock()
        service.vmware_cpu_usage_gauge = MagicMock()
        service.vmware_memory_usage_gauge = MagicMock()
        service.vmware_cpu_percent_gauge = MagicMock()
        service.vmware_memory_percent_gauge = MagicMock()

        # Call the method
        service.update_vmware_metrics([vm1, vm2])

        # Verify that the metrics were cleared
        service.vmware_status_gauge._metrics.clear.assert_called_once()
        service.vmware_cpu_usage_gauge._metrics.clear.assert_called_once()
        service.vmware_memory_usage_gauge._metrics.clear.assert_called_once()
        service.vmware_cpu_percent_gauge._metrics.clear.assert_called_once()
        service.vmware_memory_percent_gauge._metrics.clear.assert_called_once()

        # Verify that the VMware status metrics were updated
        assert service.vmware_status_gauge.labels.call_count == 2
        service.vmware_status_gauge.labels.assert_any_call(
            vmware_machine="vm-node-1", status="poweredOn", node="node-1"
        )
        service.vmware_status_gauge.labels.assert_any_call(
            vmware_machine="vm-node-2", status="poweredOff", node="node-2"
        )

        # Verify that the VMware resource metrics were updated
        assert service.vmware_cpu_usage_gauge.labels.call_count == 2
        service.vmware_cpu_usage_gauge.labels.assert_any_call(
            vmware_machine="vm-node-1", node="node-1"
        )
        service.vmware_cpu_usage_gauge.labels.assert_any_call(
            vmware_machine="vm-node-2", node="node-2"
        )

    def test_record_alert(self):
        """Test recording an alert."""
        service = PrometheusService()

        # Mock the counter
        service.alert_counter = MagicMock()

        # Call the method
        service.record_alert("status", "pod")

        # Verify that the alert was recorded
        service.alert_counter.labels.assert_called_once_with(
            alert_type="status", resource_type="pod"
        )
        service.alert_counter.labels.return_value.inc.assert_called_once()

    def test_prometheus_endpoint_integration(self):
        """Test the Prometheus endpoint integration."""
        with patch(
            "apps.monitoring.pod_monitor.services.prometheus_service.make_asgi_app"
        ) as mock_make_asgi_app:
            mock_app = MagicMock()
            mock_make_asgi_app.return_value = mock_app

            # Create the service
            service = PrometheusService()

            # Get the app
            app = service.get_app()

            # Verify that the app was created
            mock_make_asgi_app.assert_called_once_with(registry=service.registry)
            assert app == mock_app
